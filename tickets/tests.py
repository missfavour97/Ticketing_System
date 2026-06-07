import shutil
import tempfile

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Attachment, StatusHistory, Ticket, Topic, Unit
from .recaptcha import verify_recaptcha


class RecaptchaTests(TestCase):
    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_DEMO_MODE=False)
    def test_recaptcha_is_skipped_when_not_configured(self):
        ok, error = verify_recaptcha('')

        self.assertTrue(ok)
        self.assertEqual(error, '')

    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_DEMO_MODE=True)
    def test_demo_recaptcha_requires_checkbox(self):
        ok, error = verify_recaptcha('', demo_response=None)

        self.assertFalse(ok)
        self.assertIn('demo reCAPTCHA', error)

    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_DEMO_MODE=True)
    def test_demo_recaptcha_accepts_checked_box(self):
        ok, error = verify_recaptcha('', demo_response='checked')

        self.assertTrue(ok)
        self.assertEqual(error, '')


class LoginRecaptchaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student', password='demo12345')

    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_DEMO_MODE=True)
    def test_login_requires_demo_recaptcha(self):
        response = self.client.post('/api/login/', {
            'username': 'student',
            'password': 'demo12345',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please complete the demo reCAPTCHA checkbox.')

    @override_settings(RECAPTCHA_ENABLED=False, RECAPTCHA_DEMO_MODE=True)
    def test_login_accepts_demo_recaptcha(self):
        response = self.client.post('/api/login/', {
            'username': 'student',
            'password': 'demo12345',
            'demo-recaptcha': 'checked',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/api/ui/dashboard/')


class TicketModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='student', password='demo12345')
        self.unit = Unit.objects.create(name='IT Services')
        self.topic = Topic.objects.create(unit=self.unit, name='Student Portal')

    def test_ticket_number_uses_support_prefix(self):
        ticket = Ticket.objects.create(
            unit=self.unit,
            topic=self.topic,
            created_by=self.user,
            title='Cannot log in',
            description='Password reset is not arriving.',
        )

        self.assertEqual(ticket.ticket_number, f'SUP-{ticket.id:04d}')

    def test_high_priority_ticket_can_breach_sla(self):
        ticket = Ticket.objects.create(
            unit=self.unit,
            topic=self.topic,
            created_by=self.user,
            title='Wi-Fi down',
            description='No access in the lab.',
            priority='high',
        )
        Ticket.objects.filter(id=ticket.id).update(
            created_at=timezone.now() - timezone.timedelta(hours=9)
        )
        ticket.refresh_from_db()

        self.assertTrue(ticket.is_sla_breached)


class TicketAttachmentAndEmailTests(TestCase):
    def setUp(self):
        self.media_root = tempfile.mkdtemp()
        self.student = User.objects.create_user(
            username='student',
            password='demo12345',
            email='student@example.com',
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='demo12345',
            email='staff@example.com',
            is_staff=True,
        )
        self.unit = Unit.objects.create(name='IT Services')
        self.topic = Topic.objects.create(unit=self.unit, name='Student Portal')

    def tearDown(self):
        shutil.rmtree(self.media_root, ignore_errors=True)

    def test_ticket_creation_uploads_file_and_sends_email(self):
        self.client.login(username='student', password='demo12345')
        upload = SimpleUploadedFile(
            'screenshot.txt',
            b'portal error screenshot',
            content_type='text/plain',
        )

        with override_settings(
            MEDIA_ROOT=self.media_root,
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        ):
            response = self.client.post('/api/ui/tickets/create/', {
                'title': 'Portal error',
                'description': 'The portal shows a blank page.',
                'priority': 'medium',
                'unit': str(self.unit.id),
                'topic': str(self.topic.id),
                'contact_email': 'student@example.com',
                'attachments': upload,
            })

        ticket = Ticket.objects.get(title='Portal error')

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.contact_email, 'student@example.com')
        self.assertEqual(ticket.attachments.count(), 1)
        self.assertEqual(ticket.attachments.first().filename, 'screenshot.txt')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(ticket.ticket_number, mail.outbox[0].subject)

    def test_status_update_sends_email(self):
        ticket = Ticket.objects.create(
            unit=self.unit,
            topic=self.topic,
            created_by=self.student,
            contact_email='student@example.com',
            title='Wi-Fi issue',
            description='The Wi-Fi is down.',
        )
        self.client.login(username='staff', password='demo12345')

        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            response = self.client.post(f'/api/ui/tickets/{ticket.id}/update-status/', {
                'status': 'in_progress',
                'priority': 'high',
                'assigned_to': str(self.staff.id),
            })

        ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(ticket.status, 'in_progress')
        self.assertEqual(StatusHistory.objects.filter(ticket=ticket).count(), 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('status changed to In Progress', mail.outbox[0].subject)


class TicketRoutingTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username='student',
            password='demo12345',
            email='student@example.com',
        )
        self.staff = User.objects.create_user(
            username='staff_triage',
            password='demo12345',
            email='triage@example.com',
            is_staff=True,
        )
        self.triage = Unit.objects.create(name='Triage Desk')
        self.routing = Topic.objects.create(unit=self.triage, name='Ticket Routing')
        self.it = Unit.objects.create(name='IT Services')
        self.portal = Topic.objects.create(unit=self.it, name='Student Portal')
        self.ticket = Ticket.objects.create(
            unit=self.triage,
            topic=self.routing,
            created_by=self.student,
            assigned_to=self.staff,
            title='Route this request',
            description='I am not sure which office should handle this.',
        )

    def test_staff_can_route_ticket_to_correct_unit(self):
        self.client.login(username='staff_triage', password='demo12345')

        response = self.client.post(f'/api/ui/tickets/{self.ticket.id}/route/', {
            'unit': str(self.it.id),
            'topic': str(self.portal.id),
        })

        self.ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.ticket.unit, self.it)
        self.assertEqual(self.ticket.topic, self.portal)
        self.assertTrue(
            self.ticket.comments.filter(
                message__contains='Ticket routed from Triage Desk / Ticket Routing'
            ).exists()
        )

    def test_route_requires_matching_unit_and_topic(self):
        registrar = Unit.objects.create(name='Registrar Office')

        self.client.login(username='staff_triage', password='demo12345')

        response = self.client.post(f'/api/ui/tickets/{self.ticket.id}/route/', {
            'unit': str(registrar.id),
            'topic': str(self.portal.id),
        })

        self.ticket.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.ticket.unit, self.triage)
        self.assertEqual(self.ticket.topic, self.routing)

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Ticket, Topic, Unit
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

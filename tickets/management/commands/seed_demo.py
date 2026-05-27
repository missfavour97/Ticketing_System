from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from tickets.models import Comment, StatusHistory, Ticket, Topic, Unit


DEMO_PASSWORD = 'demo12345'


class Command(BaseCommand):
    help = 'Create realistic demo users, units, topics, tickets, comments, and status history.'

    def handle(self, *args, **options):
        groups = {
            name: Group.objects.get_or_create(name=name)[0]
            for name in ['Admin', 'Student', 'Unit Staff']
        }

        admin = self.create_user('admin_demo', 'Admin', groups, is_staff=True, is_superuser=True)
        student_ada = self.create_user('student_ada', 'Student', groups, first_name='Ada')
        student_musa = self.create_user('student_musa', 'Student', groups, first_name='Musa')
        staff_it = self.create_user('staff_it', 'Unit Staff', groups, first_name='Ife')
        staff_registrar = self.create_user('staff_registrar', 'Unit Staff', groups, first_name='Rana')
        staff_finance = self.create_user('staff_finance', 'Unit Staff', groups, first_name='Maya')

        it_services = self.create_unit(
            'IT Services',
            'Handles campus technology, student portal access, wireless networks, and classroom systems.'
        )
        network_team = self.create_unit(
            'Network Team',
            'Supports Wi-Fi coverage, wired network ports, and connectivity issues.',
            parent=it_services
        )
        registrar = self.create_unit(
            'Registrar Office',
            'Supports course registration, transcripts, student records, and graduation checks.'
        )
        finance = self.create_unit(
            'Student Finance',
            'Supports tuition payments, receipts, scholarships, and billing questions.'
        )

        wifi = self.create_topic(network_team, 'Campus Wi-Fi', 'Wireless access and connectivity support.')
        portal = self.create_topic(it_services, 'Student Portal', 'Login, password, and portal access issues.')
        registration = self.create_topic(registrar, 'Course Registration', 'Registration, prerequisite, and add/drop requests.')
        transcript = self.create_topic(registrar, 'Transcript Request', 'Transcript applications and delivery updates.')
        billing = self.create_topic(finance, 'Tuition and Billing', 'Payment confirmation and account balance questions.')

        self.create_ticket(
            title='Campus Wi-Fi drops in engineering lab',
            description='Wi-Fi disconnects every few minutes in Engineering Lab 204 during afternoon classes.',
            unit=network_team,
            topic=wifi,
            created_by=student_ada,
            assigned_to=staff_it,
            priority='high',
            status='in_progress',
            age_hours=10,
            comments=[
                (student_ada, 'The issue affects the whole lab, not just my laptop.'),
                (staff_it, 'We checked the access point logs and opened a maintenance task.'),
            ],
            transitions=[('new', 'in_progress', staff_it)],
        )

        self.create_ticket(
            title='Student portal password reset email not arriving',
            description='The portal says a reset email was sent, but nothing arrives in my university email inbox.',
            unit=it_services,
            topic=portal,
            created_by=student_musa,
            assigned_to=None,
            priority='medium',
            status='new',
            age_hours=3,
            comments=[
                (student_musa, 'I checked spam and tried twice this morning.'),
            ],
        )

        self.create_ticket(
            title='Tuition payment receipt not reflected',
            description='Payment was completed yesterday, but the student finance page still shows an outstanding balance.',
            unit=finance,
            topic=billing,
            created_by=student_ada,
            assigned_to=staff_finance,
            priority='high',
            status='in_progress',
            age_hours=6,
            comments=[
                (student_ada, 'I can provide the bank reference number if needed.'),
                (staff_finance, 'Finance is matching the payment reference with the bank report.'),
            ],
            transitions=[('new', 'in_progress', staff_finance)],
        )

        self.create_ticket(
            title='Course registration shows missing prerequisite',
            description='The system says I am missing CPE 201, but I passed it last semester.',
            unit=registrar,
            topic=registration,
            created_by=student_musa,
            assigned_to=staff_registrar,
            priority='medium',
            status='done',
            age_hours=48,
            comments=[
                (staff_registrar, 'The prerequisite record was refreshed and registration is now open.'),
                (student_musa, 'Confirmed, I was able to register. Thank you.'),
            ],
            transitions=[
                ('new', 'in_progress', staff_registrar),
                ('in_progress', 'done', staff_registrar),
            ],
        )

        self.create_ticket(
            title='Transcript request needs department approval',
            description='My transcript request has been waiting for approval since last week.',
            unit=registrar,
            topic=transcript,
            created_by=student_ada,
            assigned_to=staff_registrar,
            priority='low',
            status='new',
            age_hours=80,
            comments=[
                (student_ada, 'I need the transcript for a scholarship application deadline.'),
            ],
        )

        self.create_ticket(
            title='Duplicate library access request',
            description='I submitted this twice by mistake after the first page timed out.',
            unit=it_services,
            topic=portal,
            created_by=student_musa,
            assigned_to=None,
            priority='low',
            status='withdrawn',
            age_hours=12,
            comments=[
                (student_musa, 'Duplicate ticket withdrawn.'),
            ],
            transitions=[('new', 'withdrawn', student_musa)],
        )

        self.stdout.write(self.style.SUCCESS('Demo data ready.'))
        self.stdout.write('Log in with admin_demo, staff_it, or student_ada using password demo12345.')

    def create_user(self, username, group_name, groups, first_name='', is_staff=False, is_superuser=False):
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'email': f'{username}@university.example',
            }
        )
        user.first_name = first_name
        user.email = f'{username}@university.example'
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.set_password(DEMO_PASSWORD)
        user.save()
        groups[group_name].user_set.add(user)
        return user

    def create_unit(self, name, description, parent=None):
        unit, _ = Unit.objects.update_or_create(
            name=name,
            defaults={
                'description': description,
                'parent': parent,
            }
        )
        return unit

    def create_topic(self, unit, name, description):
        topic, _ = Topic.objects.update_or_create(
            unit=unit,
            name=name,
            defaults={'description': description}
        )
        return topic

    def create_ticket(
        self,
        title,
        description,
        unit,
        topic,
        created_by,
        assigned_to,
        priority,
        status,
        age_hours,
        comments,
        transitions=None,
    ):
        ticket, _ = Ticket.objects.update_or_create(
            title=title,
            created_by=created_by,
            defaults={
                'description': description,
                'unit': unit,
                'topic': topic,
                'assigned_to': assigned_to,
                'priority': priority,
                'status': status,
            }
        )

        created_at = timezone.now() - timezone.timedelta(hours=age_hours)
        Ticket.objects.filter(id=ticket.id).update(created_at=created_at, updated_at=timezone.now())
        ticket.refresh_from_db()

        StatusHistory.objects.get_or_create(
            ticket=ticket,
            old_status='created',
            new_status='new',
            changed_by=created_by,
        )

        for old_status, new_status, changed_by in transitions or []:
            StatusHistory.objects.get_or_create(
                ticket=ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by,
            )

        for user, message in comments:
            Comment.objects.get_or_create(
                ticket=ticket,
                user=user,
                message=message,
            )

        return ticket

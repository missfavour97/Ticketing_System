from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render, redirect
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count, Q
from .models import Attachment, Ticket, Unit, Topic, Comment, StatusHistory
from .notifications import (
    notify_ticket_assigned,
    notify_ticket_created,
    notify_ticket_routed,
    notify_ticket_status_changed,
    send_ticket_created_email,
    send_ticket_status_email,
)
from .recaptcha import is_recaptcha_enabled, recaptcha_mode, verify_recaptcha
import json


def recaptcha_context():
    return {
        'recaptcha_enabled': is_recaptcha_enabled(),
        'recaptcha_mode': recaptcha_mode(),
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    }


def get_user_role(user):
    if not user.is_authenticated:
        return ''
    return user.groups.first().name if user.groups.exists() else ''


def can_manage_tickets(user):
    role = get_user_role(user)
    return user.is_staff or role in ['Admin', 'Unit Staff']


def unavailable_ticket_response(request):
    messages.warning(request, 'That ticket is not available for your account.')
    return redirect('ticket_list_page')


def staff_users():
    return User.objects.filter(
        Q(groups__name='Admin') | Q(groups__name='Unit Staff') | Q(is_staff=True)
    ).distinct().order_by('username')


def visible_tickets_for(user):
    tickets = Ticket.objects.select_related(
        'unit',
        'topic',
        'created_by',
        'assigned_to',
    )

    role = get_user_role(user)

    if role == 'Student':
        return tickets.filter(created_by=user)

    if role == 'Unit Staff' and not user.is_staff:
        return tickets.filter(Q(assigned_to=user) | Q(assigned_to__isnull=True))

    return tickets


def apply_ticket_filters(tickets, params):
    query = params.get('q', '').strip()
    status = params.get('status', '').strip()
    priority = params.get('priority', '').strip()
    unit_id = params.get('unit', '').strip()
    assigned_to = params.get('assigned_to', '').strip()

    if query:
        tickets = tickets.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(created_by__username__icontains=query) |
            Q(unit__name__icontains=query) |
            Q(topic__name__icontains=query)
        )

    valid_statuses = dict(Ticket.STATUS_CHOICES)
    valid_priorities = dict(Ticket.PRIORITY_CHOICES)

    if status in valid_statuses:
        tickets = tickets.filter(status=status)

    if priority in valid_priorities:
        tickets = tickets.filter(priority=priority)

    if unit_id.isdigit():
        tickets = tickets.filter(unit_id=unit_id)

    if assigned_to == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    elif assigned_to.isdigit():
        tickets = tickets.filter(assigned_to_id=assigned_to)

    return tickets


def status_cards_for(tickets):
    counts = dict(
        tickets.values('status')
        .annotate(total=Count('id'))
        .values_list('status', 'total')
    )

    return [
        {
            'label': label,
            'count': counts.get(value, 0),
            'class': {
                'new': 'border-primary',
                'in_progress': 'border-info',
                'done': 'border-success',
                'canceled': 'border-secondary',
                'withdrawn': 'border-dark',
            }.get(value, 'border-secondary')
        }
        for value, label in Ticket.STATUS_CHOICES
    ]


def ticket_board_columns_for(tickets):
    return [
        {
            'value': value,
            'label': label,
            'tickets': tickets.filter(status=value).order_by('-updated_at'),
        }
        for value, label in Ticket.STATUS_CHOICES
    ]


def save_ticket_attachments(ticket, files, user):
    for uploaded_file in files.getlist('attachments'):
        Attachment.objects.create(
            ticket=ticket,
            uploaded_by=user,
            file=uploaded_file
        )


def add_routing_comment(ticket, user, old_unit, old_topic):
    Comment.objects.create(
        ticket=ticket,
        user=user,
        message=(
            f"Ticket routed from {old_unit.name} / {old_topic.name} "
            f"to {ticket.unit.name} / {ticket.topic.name}."
        )
    )


def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        recaptcha_token = request.POST.get("g-recaptcha-response")

        recaptcha_ok, recaptcha_error = verify_recaptcha(
            recaptcha_token,
            request.META.get("REMOTE_ADDR"),
            demo_response=request.POST.get("demo-recaptcha")
        )

        if not recaptcha_ok:
            context = recaptcha_context()
            context["error"] = recaptcha_error
            return render(request, "tickets/login.html", context)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/api/ui/dashboard/")
        else:
            context = recaptcha_context()
            context["error"] = "Invalid username or password"
            return render(request, "tickets/login.html", context)

    return render(request, "tickets/login.html", recaptcha_context())


def logout_page(request):
    logout(request)
    return redirect("/api/login/")


@csrf_exempt
def create_ticket(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            unit = Unit.objects.get(id=data['unit_id'])
            topic = Topic.objects.get(id=data['topic_id'])
            user = User.objects.get(id=data['created_by'])
            assigned_to = None

            if data.get('assigned_to'):
                assigned_to = User.objects.get(id=data['assigned_to'])

            ticket = Ticket.objects.create(
                unit=unit,
                topic=topic,
                created_by=user,
                assigned_to=assigned_to,
                title=data['title'],
                description=data['description'],
                contact_email=data.get('contact_email', user.email),
                status=data.get('status', 'new'),
                priority=data.get('priority', 'medium')
            )

            send_ticket_created_email(ticket)
            notify_ticket_created(ticket)
            notify_ticket_assigned(ticket, user)

            return JsonResponse({
                'message': 'Ticket created successfully',
                'ticket_id': ticket.id
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def list_tickets(request):
    tickets = Ticket.objects.all().values(
        'id',
        'title',
        'description',
        'status',
        'priority',
        'unit__name',
        'topic__name',
        'created_by__username',
        'assigned_to__username',
        'contact_email',
        'created_at',
        'updated_at'
    )
    return JsonResponse(list(tickets), safe=False)


def ticket_detail(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    data = {
        'id': ticket.id,
        'title': ticket.title,
        'description': ticket.description,
        'status': ticket.status,
        'priority': ticket.priority,
        'unit': ticket.unit.name,
        'topic': ticket.topic.name,
        'created_by': ticket.created_by.username,
        'assigned_to': ticket.assigned_to.username if ticket.assigned_to else None,
        'contact_email': ticket.contact_email,
        'ticket_number': ticket.ticket_number,
        'sla_due_at': ticket.sla_due_at,
        'is_sla_breached': ticket.is_sla_breached,
        'created_at': ticket.created_at,
        'updated_at': ticket.updated_at,
    }
    return JsonResponse(data)


@csrf_exempt
def update_ticket_status(request, ticket_id):
    if request.method == 'PUT':
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            data = json.loads(request.body)

            old_status = ticket.status
            new_status = data['status']
            changed_by = User.objects.get(id=data['changed_by'])

            if new_status not in dict(Ticket.STATUS_CHOICES):
                return JsonResponse({'error': 'Invalid status'}, status=400)

            ticket.status = new_status
            ticket.save()

            StatusHistory.objects.create(
                ticket=ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by
            )
            send_ticket_status_email(ticket, old_status, new_status, changed_by)
            notify_ticket_status_changed(ticket, old_status, new_status, changed_by)

            return JsonResponse({'message': 'Ticket status updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only PUT method allowed'}, status=405)


def update_ticket_status_page(request, ticket_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    ticket = visible_tickets_for(request.user).filter(id=ticket_id).first()
    if ticket is None:
        return unavailable_ticket_response(request)

    if request.method == 'POST':
        old_status = ticket.status
        old_assigned_to_id = ticket.assigned_to_id
        new_status = request.POST.get('status')
        priority = request.POST.get('priority')
        assigned_to_id = request.POST.get('assigned_to')
        can_manage = can_manage_tickets(request.user)
        status_changed = False

        valid_statuses = dict(Ticket.STATUS_CHOICES)
        valid_priorities = dict(Ticket.PRIORITY_CHOICES)

        if new_status not in valid_statuses:
            return redirect('ticket_detail_page', ticket_id=ticket.id)

        student_withdrawing = (
            ticket.created_by_id == request.user.id and
            new_status == 'withdrawn'
        )

        if not can_manage and not student_withdrawing:
            return redirect('ticket_detail_page', ticket_id=ticket.id)

        if new_status and new_status != old_status:
            ticket.status = new_status
            status_changed = True

            StatusHistory.objects.create(
                ticket=ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user
            )

        if can_manage:
            if priority in valid_priorities:
                ticket.priority = priority

            if assigned_to_id == '':
                ticket.assigned_to = None
            elif assigned_to_id and assigned_to_id.isdigit():
                ticket.assigned_to = User.objects.filter(id=assigned_to_id).first()

        ticket.save()

        if status_changed:
            send_ticket_status_email(ticket, old_status, new_status, request.user)
            notify_ticket_status_changed(ticket, old_status, new_status, request.user)

        if can_manage and ticket.assigned_to_id and ticket.assigned_to_id != old_assigned_to_id:
            notify_ticket_assigned(ticket, request.user)

    return redirect('ticket_detail_page', ticket_id=ticket.id)


@csrf_exempt
def delete_ticket(request, ticket_id):
    if request.method == 'DELETE':
        ticket = get_object_or_404(Ticket, id=ticket_id)
        ticket.delete()
        return JsonResponse({'message': 'Ticket deleted successfully'})

    return JsonResponse({'error': 'Only DELETE method allowed'}, status=405)


@csrf_exempt
def create_unit(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            unit = Unit.objects.create(
                name=data['name'],
                description=data.get('description', '')
            )

            return JsonResponse({
                'message': 'Unit created successfully',
                'unit_id': unit.id
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def list_units(request):
    units = Unit.objects.all().values('id', 'name', 'description')
    return JsonResponse(list(units), safe=False)


@csrf_exempt
def create_topic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit = Unit.objects.get(id=data['unit_id'])

            topic = Topic.objects.create(
                unit=unit,
                name=data['name'],
                description=data.get('description', '')
            )

            return JsonResponse({
                'message': 'Topic created successfully',
                'topic_id': topic.id
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def list_topics(request):
    topics = Topic.objects.all().values(
        'id',
        'name',
        'description',
        'unit__name'
    )
    return JsonResponse(list(topics), safe=False)


@csrf_exempt
def create_comment(request, ticket_id):
    if request.method == 'POST':
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            data = json.loads(request.body)
            user = User.objects.get(id=data['user_id'])

            comment = Comment.objects.create(
                ticket=ticket,
                user=user,
                message=data['message']
            )

            return JsonResponse({
                'message': 'Comment created successfully',
                'comment_id': comment.id
            }, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only POST method allowed'}, status=405)


def create_unit_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    units = Unit.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        parent_id = request.POST.get('parent')

        parent = None
        if parent_id:
            parent = Unit.objects.get(id=parent_id)

        if name:
            Unit.objects.create(
                name=name,
                description=description,
                parent=parent
            )
            return redirect('unit_list_page')

    return render(request, 'tickets/create_unit.html', {
        'units': units,
        'role': get_user_role(request.user),
    })


def unit_list_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    units = Unit.objects.prefetch_related('topics').order_by('name')
    return render(request, 'tickets/unit_list.html', {
        'units': units,
        'role': get_user_role(request.user),
    })


def create_ticket_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    units = Unit.objects.all().order_by('name')
    topics = Topic.objects.select_related('unit').order_by('unit__name', 'name')
    error = None

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        priority = request.POST.get('priority')
        unit_id = request.POST.get('unit')
        topic_id = request.POST.get('topic')
        contact_email = request.POST.get('contact_email') or request.user.email

        if title and description and priority and unit_id and topic_id:
            topic = Topic.objects.filter(id=topic_id, unit_id=unit_id).first()

            if topic is None:
                error = 'Please choose a topic that belongs to the selected unit.'
            else:
                ticket = Ticket.objects.create(
                    title=title,
                    description=description,
                    status='new',
                    priority=priority,
                    unit_id=unit_id,
                    topic=topic,
                    created_by=request.user,
                    contact_email=contact_email
                )
                save_ticket_attachments(ticket, request.FILES, request.user)

                StatusHistory.objects.create(
                    ticket=ticket,
                    old_status='created',
                    new_status='new',
                    changed_by=request.user
                )
                send_ticket_created_email(ticket)
                notify_ticket_created(ticket)

                return redirect('ticket_detail_page', ticket_id=ticket.id)
        else:
            error = 'Please complete all required fields.'

    return render(request, 'tickets/create_ticket.html', {
        'units': units,
        'topics': topics,
        'error': error,
        'default_contact_email': request.user.email,
        'role': get_user_role(request.user),
    })


def ticket_list_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    tickets = visible_tickets_for(request.user)
    tickets = apply_ticket_filters(tickets, request.GET)
    tickets = tickets.annotate(comment_count=Count('comments')).order_by('-updated_at')

    return render(request, 'tickets/ticket_list.html', {
        'tickets': tickets,
        'units': Unit.objects.order_by('name'),
        'staff_users': staff_users(),
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'filters': request.GET,
        'role': get_user_role(request.user),
        'can_manage': can_manage_tickets(request.user),
    })


def tickets_board_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    if get_user_role(request.user) == 'Student':
        messages.warning(request, 'Tickets Board is available to staff and admins.')
        return redirect('ticket_list_page')

    tickets = visible_tickets_for(request.user).annotate(comment_count=Count('comments'))

    return render(request, 'tickets/tickets_board.html', {
        'columns': ticket_board_columns_for(tickets),
        'hide_user_identity': True,
        'role': get_user_role(request.user),
    })


def ticket_detail_page(request, ticket_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    ticket = (
        visible_tickets_for(request.user)
        .prefetch_related(
            'attachments__uploaded_by',
            'comments__user',
            'status_history__changed_by',
        )
        .filter(id=ticket_id)
        .first()
    )
    if ticket is None:
        return unavailable_ticket_response(request)

    return render(request, 'tickets/ticket_detail.html', {
        'ticket': ticket,
        'attachments': ticket.attachments.all().order_by('-uploaded_at'),
        'comments': ticket.comments.all().order_by('created_at'),
        'history': ticket.status_history.all().order_by('-changed_at'),
        'units': Unit.objects.order_by('name'),
        'topics': Topic.objects.select_related('unit').order_by('unit__name', 'name'),
        'staff_users': staff_users(),
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
        'role': get_user_role(request.user),
        'can_manage': can_manage_tickets(request.user),
    })


def add_comment_page(request, ticket_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    ticket = visible_tickets_for(request.user).filter(id=ticket_id).first()
    if ticket is None:
        return unavailable_ticket_response(request)

    if request.method == 'POST':
        content = request.POST.get('content')

        if content:
            Comment.objects.create(
                ticket=ticket,
                user=request.user,
                message=content
            )

    return redirect('ticket_detail_page', ticket_id=ticket.id)


def add_attachment_page(request, ticket_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    ticket = visible_tickets_for(request.user).filter(id=ticket_id).first()
    if ticket is None:
        return unavailable_ticket_response(request)

    if request.method == 'POST':
        save_ticket_attachments(ticket, request.FILES, request.user)

    return redirect('ticket_detail_page', ticket_id=ticket.id)


def route_ticket_page(request, ticket_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    if not can_manage_tickets(request.user):
        return redirect('ticket_detail_page', ticket_id=ticket_id)

    ticket = visible_tickets_for(request.user).filter(id=ticket_id).first()
    if ticket is None:
        return unavailable_ticket_response(request)

    if request.method == 'POST':
        unit_id = request.POST.get('unit')
        topic_id = request.POST.get('topic')
        topic = Topic.objects.filter(id=topic_id, unit_id=unit_id).select_related('unit').first()

        if topic:
            old_unit = ticket.unit
            old_topic = ticket.topic
            ticket.unit = topic.unit
            ticket.topic = topic
            ticket.save()

            if old_unit.id != ticket.unit_id or old_topic.id != ticket.topic_id:
                add_routing_comment(ticket, request.user, old_unit, old_topic)
                notify_ticket_routed(ticket, old_unit, old_topic, request.user)

    return redirect('ticket_detail_page', ticket_id=ticket.id)


def notification_list_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    notifications = request.user.notifications.select_related('ticket')
    return render(request, 'tickets/notifications.html', {
        'notifications': notifications,
        'unread_count': notifications.filter(is_read=False).count(),
        'role': get_user_role(request.user),
    })


def mark_notification_read_page(request, notification_id):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    notification = get_object_or_404(request.user.notifications, id=notification_id)

    if request.method == 'POST':
        notification.is_read = True
        notification.save(update_fields=['is_read'])

        if notification.ticket_id:
            return redirect('ticket_detail_page', ticket_id=notification.ticket_id)

    return redirect('notification_list_page')


def mark_all_notifications_read_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    if request.method == 'POST':
        request.user.notifications.filter(is_read=False).update(is_read=True)

    return redirect('notification_list_page')


def dashboard_page(request):
    if not request.user.is_authenticated:
        return redirect('/api/login/')

    role = get_user_role(request.user)
    tickets = visible_tickets_for(request.user)
    open_tickets = tickets.filter(status__in=['new', 'in_progress'])
    sla_risk_count = sum(1 for ticket in open_tickets if ticket.is_sla_breached)
    recent_tickets = tickets.order_by('-updated_at')[:6]

    return render(request, 'tickets/dashboard.html', {
        'role': role,
        'hide_user_identity': request.user.username == 'admin_demo',
        'total_units': Unit.objects.count(),
        'total_topics': Topic.objects.count(),
        'total_tickets': tickets.count(),
        'open_tickets': open_tickets.count(),
        'high_priority': open_tickets.filter(priority='high').count(),
        'sla_risk_count': sla_risk_count,
        'unassigned_tickets': tickets.filter(assigned_to__isnull=True).count(),
        'status_cards': status_cards_for(tickets),
        'recent_tickets': recent_tickets,
    })

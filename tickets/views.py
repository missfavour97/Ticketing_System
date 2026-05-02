from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from .models import Ticket, Unit, Topic, Comment, StatusHistory
import json
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect

def login_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("/api/ui/dashboard/")
        else:
            return render(request, "tickets/login.html", {
                "error": "Invalid username or password"
            })

    return render(request, "tickets/login.html")


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

            ticket = Ticket.objects.create(
                unit=unit,
                topic=topic,
                created_by=user,
                title=data['title'],
                description=data['description'],
                status=data.get('status', 'new'),
                priority=data.get('priority', 'medium')
            )

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

            ticket.status = new_status
            ticket.save()

            StatusHistory.objects.create(
                ticket=ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=changed_by
            )

            return JsonResponse({'message': 'Ticket status updated successfully'})

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Only PUT method allowed'}, status=405)

def update_ticket_status_page(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        old_status = ticket.status
        new_status = request.POST.get('status')

        if new_status and new_status != old_status:
            ticket.status = new_status
            ticket.save()

            StatusHistory.objects.create(
                ticket=ticket,
                old_status=old_status,
                new_status=new_status,
                changed_by=ticket.created_by
            )

    return redirect('ticket_list_page')


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
    units = Unit.objects.all()

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

    return render(request, 'tickets/create_unit.html', {'units': units})


def unit_list_page(request):
    units = Unit.objects.all()
    return render(request, 'tickets/unit_list.html', {'units': units})


def create_ticket_page(request):
    units = Unit.objects.all()
    topics = Topic.objects.all()
    users = User.objects.all()

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status')
        priority = request.POST.get('priority')
        unit_id = request.POST.get('unit')
        topic_id = request.POST.get('topic')
        created_by_id = request.POST.get('created_by')

        if title and description and unit_id and topic_id and created_by_id:
            Ticket.objects.create(
                title=title,
                description=description,
                status=status,
                priority=priority,
                unit_id=unit_id,
                topic_id=topic_id,
                created_by_id=created_by_id
            )
            return redirect('ticket_list_page')

    context = {
        'units': units,
        'topics': topics,
        'users': users,
    }
    return render(request, 'tickets/create_ticket.html', context)


def ticket_list_page(request):
    tickets = Ticket.objects.all().prefetch_related('comments__user')
    users = User.objects.all()
    return render(request, 'tickets/ticket_list.html', {'tickets': tickets, 'users': users})

def add_comment_page(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        user_id = request.POST.get('user')

        if content and user_id:
            Comment.objects.create(
                ticket=ticket,
                user_id=user_id,
                message=content
            )

    return redirect('ticket_list_page')

def dashboard_page(request):
    total_units = Unit.objects.count()
    total_tickets = Ticket.objects.count()
    total_topics = Topic.objects.count()

    return render(request, 'tickets/dashboard.html', {
        'total_units': total_units,
        'total_tickets': total_tickets,
        'total_topics': total_topics
    })

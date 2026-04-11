from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Ticket, Unit, Topic, Comment, StatusHistory
import json


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

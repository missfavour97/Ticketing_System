from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .models import Notification, Ticket


def ticket_link(ticket):
    return f"{settings.SITE_URL}{reverse('ticket_detail_page', args=[ticket.id])}"


def ticket_recipient(ticket):
    email = ticket.notification_email
    if not email:
        return []
    return [email]


def send_ticket_created_email(ticket):
    recipients = ticket_recipient(ticket)
    if not recipients:
        return False

    subject = f"{ticket.ticket_number} created: {ticket.title}"
    message = (
        f"Your support ticket has been created.\n\n"
        f"Ticket: {ticket.ticket_number}\n"
        f"Title: {ticket.title}\n"
        f"Status: {ticket.get_status_display()}\n"
        f"Priority: {ticket.get_priority_display()}\n"
        f"Unit: {ticket.unit.name}\n"
        f"Topic: {ticket.topic.name}\n"
        f"SLA target: {ticket.sla_due_at:%Y-%m-%d %H:%M}\n\n"
        f"View ticket: {ticket_link(ticket)}\n"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )
    return True


def send_ticket_status_email(ticket, old_status, new_status, changed_by):
    recipients = ticket_recipient(ticket)
    if not recipients:
        return False

    status_labels = dict(Ticket.STATUS_CHOICES)
    subject = f"{ticket.ticket_number} status changed to {status_labels.get(new_status, new_status)}"
    message = (
        f"Your support ticket status has changed.\n\n"
        f"Ticket: {ticket.ticket_number}\n"
        f"Title: {ticket.title}\n"
        f"Old status: {status_labels.get(old_status, old_status)}\n"
        f"New status: {status_labels.get(new_status, new_status)}\n"
        f"Changed by: {changed_by.username}\n\n"
        f"View ticket: {ticket_link(ticket)}\n"
    )

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )
    return True


def create_notification(user, title, message, ticket=None):
    if user is None:
        return None

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        ticket=ticket,
    )


def notify_ticket_created(ticket):
    return create_notification(
        ticket.created_by,
        f"{ticket.ticket_number} created",
        f"Your ticket was created and is currently {ticket.get_status_display()}.",
        ticket=ticket,
    )


def notify_ticket_status_changed(ticket, old_status, new_status, changed_by):
    status_labels = dict(Ticket.STATUS_CHOICES)
    old_label = status_labels.get(old_status, old_status)
    new_label = status_labels.get(new_status, new_status)

    return create_notification(
        ticket.created_by,
        f"{ticket.ticket_number} status changed to {new_label}",
        (
            f"Your ticket status changed from {old_label} to {new_label} "
            f"by {changed_by.username}."
        ),
        ticket=ticket,
    )


def notify_ticket_assigned(ticket, assigned_by):
    if ticket.assigned_to is None:
        return None

    return create_notification(
        ticket.assigned_to,
        f"{ticket.ticket_number} assigned to you",
        f"{assigned_by.username} assigned this ticket to you.",
        ticket=ticket,
    )


def notify_ticket_routed(ticket, old_unit, old_topic, routed_by):
    return create_notification(
        ticket.created_by,
        f"{ticket.ticket_number} routed",
        (
            f"{routed_by.username} routed your ticket from "
            f"{old_unit.name} / {old_topic.name} to {ticket.unit.name} / {ticket.topic.name}."
        ),
        ticket=ticket,
    )

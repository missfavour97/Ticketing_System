from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse

from .models import Ticket


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

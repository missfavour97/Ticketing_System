import os

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


SLA_HOURS_BY_PRIORITY = {
    'high': 8,
    'medium': 24,
    'low': 72,
}


class Unit(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Topic(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='topics')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.unit.name} - {self.name}"


class Ticket(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('canceled', 'Canceled'),
        ('withdrawn', 'Withdrawn'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tickets')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='tickets')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='assigned_tickets',
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    contact_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def ticket_number(self):
        if not self.id:
            return 'SUP-DRAFT'
        return f'SUP-{self.id:04d}'

    @property
    def sla_due_at(self):
        hours = SLA_HOURS_BY_PRIORITY.get(self.priority, 24)
        return self.created_at + timezone.timedelta(hours=hours)

    @property
    def is_open(self):
        return self.status in ['new', 'in_progress']

    @property
    def is_sla_breached(self):
        return self.is_open and timezone.now() > self.sla_due_at

    @property
    def status_badge_class(self):
        return {
            'new': 'bg-primary',
            'in_progress': 'bg-info text-dark',
            'done': 'bg-success',
            'canceled': 'bg-secondary',
            'withdrawn': 'bg-dark',
        }.get(self.status, 'bg-secondary')

    @property
    def priority_badge_class(self):
        return {
            'high': 'bg-danger',
            'medium': 'bg-warning text-dark',
            'low': 'bg-success',
        }.get(self.priority, 'bg-secondary')

    @property
    def notification_email(self):
        return self.contact_email or self.created_by.email


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.ticket.title}"


class Attachment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_attachments',
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.ticket.title}"

    @property
    def filename(self):
        return os.path.basename(self.file.name)


class StatusHistory(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='status_changes')
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.title}: {self.old_status} -> {self.new_status}"

    @property
    def old_status_label(self):
        return dict(Ticket.STATUS_CHOICES).get(self.old_status, self.old_status)

    @property
    def new_status_label(self):
        return dict(Ticket.STATUS_CHOICES).get(self.new_status, self.new_status)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

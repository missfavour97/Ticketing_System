from django.db import models
from django.contrib.auth.models import User

class Ticket(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('closed', 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

from django.contrib import admin
from .models import Attachment, Comment, Notification, StatusHistory, Ticket, Topic, Unit


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number',
        'title',
        'status',
        'priority',
        'unit',
        'assigned_to',
        'contact_email',
        'created_by',
        'updated_at',
    )
    list_filter = ('status', 'priority', 'unit', 'assigned_to')
    search_fields = ('title', 'description', 'created_by__username')


admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Comment)
admin.site.register(StatusHistory)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('filename', 'ticket', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('ticket__title', 'file')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'ticket', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username', 'ticket__title')

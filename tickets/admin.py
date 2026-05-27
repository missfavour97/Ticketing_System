from django.contrib import admin
from .models import Attachment, Comment, StatusHistory, Ticket, Topic, Unit


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number',
        'title',
        'status',
        'priority',
        'unit',
        'assigned_to',
        'created_by',
        'updated_at',
    )
    list_filter = ('status', 'priority', 'unit', 'assigned_to')
    search_fields = ('title', 'description', 'created_by__username')


admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Comment)
admin.site.register(StatusHistory)
admin.site.register(Attachment)

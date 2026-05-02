from django.contrib import admin
from .models import Ticket, Unit, Topic, Comment, StatusHistory

admin.site.register(Ticket)
admin.site.register(Unit)
admin.site.register(Topic)
admin.site.register(Comment)
admin.site.register(StatusHistory)
from django.urls import path
from . import views

urlpatterns = [
    # API
    path('tickets/create/', views.create_ticket, name='create_ticket'),
    path('tickets/', views.list_tickets, name='list_tickets'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/update-status/', views.update_ticket_status, name='update_ticket_status'),
    path('tickets/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),

    path('units/create/', views.create_unit, name='create_unit'),
    path('units/', views.list_units, name='list_units'),

    path('topics/create/', views.create_topic, name='create_topic'),
    path('topics/', views.list_topics, name='list_topics'),

    path('tickets/<int:ticket_id>/comments/create/', views.create_comment, name='create_comment'),

    # UI
    path('ui/units/create/', views.create_unit_page, name='create_unit_page'),
    path('ui/units/', views.unit_list_page, name='unit_list_page'),

    path('ui/tickets/create/', views.create_ticket_page, name='create_ticket_page'),
    path('ui/tickets/', views.ticket_list_page, name='ticket_list_page'),

    path('ui/tickets/<int:ticket_id>/comments/', views.add_comment_page, name='add_comment_page'),
    path('ui/tickets/<int:ticket_id>/update-status/', views.update_ticket_status_page, name='update_ticket_status_page'),

    path('ui/dashboard/', views.dashboard_page, name='dashboard'),
]
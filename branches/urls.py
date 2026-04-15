from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.branch_dashboard, name='branch_dashboard'),
    path('invoices/', views.branch_invoices, name='branch_invoices'),
    path('reports/', views.branch_reports, name='branch_reports'),
    path('users/', views.branch_users, name='branch_users'),
    path('users/<int:user_id>/toggle/', views.toggle_user, name='toggle_user'),
]
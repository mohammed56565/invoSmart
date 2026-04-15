from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('upload/', views.upload_invoice, name='upload_invoice'),
    path('<int:invoice_id>/review/', views.review_invoice, name='review_invoice'),
    path('<int:invoice_id>/delete/', views.delete_invoice, name='delete_invoice'),
]
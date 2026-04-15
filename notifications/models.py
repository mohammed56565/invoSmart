from django.db import models
from django.conf import settings
# Create your models here.

from django.conf import settings


class Notification(models.Model):

    TYPE_CHOICES = [
        ('invoice_processed', 'Invoice Processed'),
        ('invoice_error', 'Invoice Error'),
        ('high_error_rate', 'High Error Rate'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.type}"
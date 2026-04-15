from django.db import models
from django.conf import settings
# Create your models here.
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    
    ROLE_CHOICES = [
        ('accounting_staff', 'Accounting Staff'),
        ('branch_manager', 'Branch Manager'),
        ('system_admin', 'System Administrator'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    branch = models.ForeignKey(
        'branches.Branch', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

class ActivityLog(models.Model):

    ACTION_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('upload_invoice', 'Upload Invoice'),
        ('edit_invoice', 'Edit Invoice'),
        ('delete_invoice', 'Delete Invoice'),
        ('create_user', 'Create User'),
        ('delete_user', 'Delete User'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"    
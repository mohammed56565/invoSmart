from django.db import models
from django.conf import settings
# Create your models here.


class Branch(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,null=True,blank=True, related_name='managed_branches')
    

    def employees_count(self):
        return self.user_set.count()
    
    def __str__(self):
        return self.name
    
class Report(models.Model):

    TYPE_CHOICES = [
        ('monthly', 'Monthly'),
        ('error_summary', 'Error Summary'),
        ('invoice_summary', 'Invoice Summary'),
    ]

    branch = models.ForeignKey( Branch,on_delete=models.CASCADE,null=True,blank=True )
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    content = models.TextField()
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.branch} - {self.type} - {self.generated_at}"    
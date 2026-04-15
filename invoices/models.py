from django.db import models
from django.conf import settings

def invoice_upload_path(instance, filename):
    return f'invoices/user_{instance.uploaded_by.id}/{filename}'

class PurchaseOrder(models.Model):

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('closed', 'Closed'),
    ]

    po_number = models.CharField(max_length=100, unique=True)
    supplier_name = models.CharField(max_length=200)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount_used = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date_issued = models.DateField()
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    def __str__(self):
        return f"{self.po_number} - {self.supplier_name}"



class Invoice(models.Model):

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('reviewed', 'Reviewed'),
        ('error', 'Error'),
    ]
    
    file = models.FileField(upload_to=invoice_upload_path)
    supplier_name = models.CharField(max_length=200, blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    date_issued = models.DateField(null=True, blank=True)
    purchase_order = models.ForeignKey( PurchaseOrder,on_delete=models.SET_NULL, null=True,blank=True)
    confidence_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.supplier_name} - {self.total_amount}"
# Create your views here.
import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from .models import Invoice, PurchaseOrder
from core.document_ai_extractor import process_invoice_with_documentai
from users.decorators import role_required
from datetime import datetime


@role_required('accounting_staff')
def invoice_list(request):
    invoices = Invoice.objects.filter(
        uploaded_by=request.user
    ).order_by('-uploaded_at')

  
    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if status_filter:
        invoices = invoices.filter(status=status_filter)
    if search:
        invoices = invoices.filter(supplier_name__icontains=search)

    return render(request, 'invoices/invoice_list.html', {
        'invoices': invoices,
        'status_filter': status_filter,
        'search': search,
    })


@role_required('accounting_staff')
def upload_invoice(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            messages.error(request, 'Please select a file.')
            return render(request, 'invoices/upload.html')

  
        allowed_types = ['application/pdf', 'image/jpeg', 'image/png']
        if file.content_type not in allowed_types:
            messages.error(request, 'Only PDF, JPG, and PNG files are allowed.')
            return render(request, 'invoices/upload.html')

     
        invoice = Invoice.objects.create(
            file=file,
            status='processing',
            uploaded_by=request.user,
            branch=request.user.branch
        )

  
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, invoice.file.name)
            
          
            data = process_invoice_with_documentai(file_path)

            if data:
                invoice.invoice_number = data.get('invoice_number') or ''
                invoice.supplier_name = data.get('supplier_name') or ''
                invoice.total_amount = data.get('total_amount')
                
             
                invoice.confidence_data = {
                    'confidence_score': data.get('confidence_score', 0),
                    'field_confidences': data.get('field_confidences', {})
                }

          
                date_str = data.get('date_issued', '')
                if date_str:
                    try:
                        invoice.date_issued = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        pass

            
                po_number = data.get('po_number', '')
                if po_number:
                    try:
                        po = PurchaseOrder.objects.get(
                            po_number=po_number,
                            branch=request.user.branch
                        )
                        invoice.purchase_order = po
                    except PurchaseOrder.DoesNotExist:
                        pass

                invoice.status = 'pending'
                invoice.save()
            else:
             
                invoice.status = 'error'
                invoice.save()
                messages.error(request, 'Failed to extract data from invoice.')
                return redirect('invoice_list')

        except Exception as e:
            invoice.status = 'error'
            invoice.save()
            messages.error(request, f'Error processing invoice: {str(e)}')
            return redirect('invoice_list')

        messages.success(request, 'Invoice uploaded and processed successfully!')
        return redirect('review_invoice', invoice_id=invoice.id)

    return render(request, 'invoices/upload.html')


@role_required('accounting_staff')
def review_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, uploaded_by=request.user)


    comparison = {}
    if invoice.purchase_order:
        po = invoice.purchase_order
        comparison = {
            'supplier_match': invoice.supplier_name.lower() == po.supplier_name.lower(),
            'amount_match': invoice.total_amount == po.total_amount,
            'po_found': True,
        }
    else:
        comparison = {'po_found': False}

  
    try:
        field_conf = invoice.confidence_data.get('field_confidences', {}) if invoice.confidence_data else {}
        confidence_data = {
            'invoice_number': field_conf.get('invoice_number', 0) if field_conf else 0,
            'supplier_name': field_conf.get('supplier_name', 0) if field_conf else 0,
            'total_amount': field_conf.get('total_amount', 0) if field_conf else 0,
            'date_issued': field_conf.get('date_issued', 0) if field_conf else 0,
            'overall': invoice.confidence_data.get('confidence_score', 0) if invoice.confidence_data else 0,
        }
    except:
    
        confidence_data = {
            'invoice_number': 0,
            'supplier_name': 0,
            'total_amount': 0,
            'date_issued': 0,
            'overall': 0,
        }

    if request.method == 'POST':
        invoice.invoice_number = request.POST.get('invoice_number', '')
        invoice.supplier_name = request.POST.get('supplier_name', '')
        invoice.date_issued = request.POST.get('date_issued') or None

        amount = request.POST.get('total_amount', '')
        if amount:
            try:
                invoice.total_amount = float(amount)
            except:
                pass

    
        if invoice.purchase_order and invoice.total_amount:
            po = invoice.purchase_order
            po.amount_used += invoice.total_amount
            po.remaining_amount = po.total_amount - po.amount_used
            if po.remaining_amount <= 0:
                po.status = 'closed'
            po.save()

        invoice.status = 'reviewed'
        invoice.save()

        messages.success(request, 'Invoice reviewed successfully!')
        return redirect('invoice_list')

    return render(request, 'invoices/review.html', {
        'invoice': invoice,
        'comparison': comparison,
        'confidence_data': confidence_data,
    })


@role_required('accounting_staff')
def delete_invoice(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id, uploaded_by=request.user)

    if request.method == 'POST':
        invoice.file.delete()
        invoice.delete()
        messages.success(request, 'Invoice deleted successfully!')
        return redirect('invoice_list')

    return render(request, 'invoices/delete_confirm.html', {'invoice': invoice})
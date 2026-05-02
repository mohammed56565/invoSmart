from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from users.decorators import role_required
from users.models import User
from invoices.models import Invoice
from .models import Branch, Report


@role_required('branch_manager')
def branch_dashboard(request):
    from notifications.models import Notification
    from datetime import datetime, timedelta
    
    branch = request.user.branch
    yesterday = datetime.now() - timedelta(days=1)
    
    total_invoices_24h = Invoice.objects.filter(
        branch=branch,
        uploaded_at__gte=yesterday
    ).count()
    
    errors_24h = Invoice.objects.filter(
        branch=branch,
        uploaded_at__gte=yesterday,
        status='error'
    ).count()
    
    error_rate = 0
    if total_invoices_24h >= 5:
        error_rate = round((errors_24h / total_invoices_24h) * 100, 1)
 
    if error_rate > 20 and total_invoices_24h >= 5:
         messages.warning(request, 'High error rate detected!')

         
         unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:5]
    
    context = {
        'total_invoices': Invoice.objects.filter(branch=branch).count(),
        'pending': Invoice.objects.filter(branch=branch, status='pending').count(),
        'reviewed': Invoice.objects.filter(branch=branch, status='reviewed').count(),
        'errors': Invoice.objects.filter(branch=branch, status='error').count(),
        'notifications': unread_notifications,
        'total_invoices_24h': total_invoices_24h,
        'errors_24h': errors_24h,
        'error_rate': error_rate,
    }
    
    return render(request, 'branches/dashboard.html', context)

@role_required('branch_manager')
def branch_invoices(request):
    branch = request.user.branch
    invoices = Invoice.objects.filter(branch=branch).order_by('-uploaded_at')

    status_filter = request.GET.get('status', '')
    search = request.GET.get('search', '')

    if status_filter:
        invoices = invoices.filter(status=status_filter)
    if search:
        invoices = invoices.filter(supplier_name__icontains=search)

    return render(request, 'branches/invoices.html', {
        'invoices': invoices,
        'status_filter': status_filter,
        'search': search,
        'branch': branch,
    })


@role_required('branch_manager')
def branch_reports(request):
    branch = request.user.branch
    reports = Report.objects.filter(branch=branch).order_by('-generated_at')

    if request.method == 'POST':
        report_type = request.POST.get('type')
        invoices = Invoice.objects.filter(branch=branch)
        total = invoices.count()
        reviewed = invoices.filter(status='reviewed').count()
        errors = invoices.filter(status='error').count()
        pending = total - reviewed - errors
        
     
        content = f"""
Branch: {branch.name}
Report Type: {report_type}
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}
---
Total Invoices: {total}
Reviewed: {reviewed} ({reviewed/total*100 if total > 0 else 0:.1f}%)
Errors: {errors} ({errors/total*100 if total > 0 else 0:.1f}%)
Pending: {pending} ({pending/total*100 if total > 0 else 0:.1f}%)
"""
        
        if report_type == 'invoice_summary':
                total_sum = 0
                max_amount = 0
                min_amount = float('inf')
                count = 0
    
                for invoice in invoices:
                 if invoice.total_amount:
                   amount = float(invoice.total_amount)
                   total_sum += amount
                   max_amount = max(max_amount, amount)
                   min_amount = min(min_amount, amount)
                   count += 1
    
                avg_amount = total_sum / count if count > 0 else 0
                min_amount = min_amount if min_amount != float('inf') else 0
    
                content += f"""
---
 Financial Summary:
Total Amount: ${total_sum:,.2f}
Average Invoice: ${avg_amount:,.2f}
Highest Invoice: ${max_amount:,.2f}
Lowest Invoice: ${min_amount:,.2f}
"""
        
        elif report_type == 'monthly':
            from datetime import timedelta
            thirty_days_ago = timezone.now() - timedelta(days=30)
            monthly_invoices = invoices.filter(uploaded_at__gte=thirty_days_ago)
            monthly_count = monthly_invoices.count()
            
            content += f"""
---
 Last 30 Days:
Invoices: {monthly_count}
Daily Average: {monthly_count/30:.1f} invoices/day
Recent Activity: {'High' if monthly_count > total/2 else 'Normal'}
"""
        
        elif report_type == 'error_summary':
            error_rate = (errors / total * 100) if total > 0 else 0
            
            content += f"""
---
  Error Analysis:
Error Rate: {error_rate:.1f}%
Status: {' High' if error_rate > 20 else ' Normal'}
Failed Invoices: {errors} out of {total}
Success Rate: {100 - error_rate:.1f}%

Recommendation: {'Review invoice quality and supplier formats' if error_rate > 20 else 'Error rate is acceptable'}
"""
        
        Report.objects.create(
            branch=branch,
            generated_by=request.user,
            type=report_type,
            content=content
        )

        messages.success(request, 'Report generated successfully!')
        return redirect('branch_reports')

    return render(request, 'branches/reports.html', {
        'reports': reports,
        'branch': branch,
    })

@role_required('branch_manager')
def branch_users(request):
    branch = request.user.branch
    users = User.objects.filter(branch=branch, role='accounting_staff')

    return render(request, 'branches/users.html', {
        'users': users,
        'branch': branch,
    })


@role_required('branch_manager')
def toggle_user(request, user_id):
    user = get_object_or_404(User, id=user_id, branch=request.user.branch)

    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status} successfully!')

    return redirect('branch_users')
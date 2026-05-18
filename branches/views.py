from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from users.models import User
from invoices.models import Invoice
from .models import Branch, Report
from notifications.models import Notification
from datetime import timedelta

def branch_dashboard(request):
    branch = request.user.branch
    
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False,
        type='high_error_rate'
    ).order_by('-created_at')
    
    if unread_notifications.exists():
        latest = unread_notifications.first()
        messages.info(request, f'{latest.message}')
        latest.is_read = True
        latest.save()
    
    context = {
        'total_invoices': Invoice.objects.filter(branch=branch).count(),  
        'pending': Invoice.objects.filter(branch=branch, status='pending').count(),  
        'reviewed': Invoice.objects.filter(branch=branch, status='reviewed').count(),  
        'errors': Invoice.objects.filter(branch=branch, status='error').count(), 
        'notifications': unread_notifications,
    }
    
    return render(request, 'branches/dashboard.html', context)


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



def branch_reports(request):
    branch = request.user.branch
    reports = Report.objects.filter(branch=branch).order_by('-generated_at')

    if request.method == 'POST':
        report_type = request.POST.get('type')
        invoices = Invoice.objects.filter(branch=branch)
        total = invoices.count()
        reviewed = invoices.filter(status='reviewed').count()
        errors = invoices.filter(status='error').count()
        pending = invoices.filter(status='pending').count()
        
     
        content = f"""
Branch: {branch.name}
Report Type: {report_type}
Generated: str(timezone.now())[:10]

Total Invoices: {total}
Reviewed: {reviewed} ({reviewed/total*100 if total > 0 else 0:.1f}%)
Errors: {errors} ({errors/total*100 if total > 0 else 0:.1f}%)
Pending: {pending} ({pending/total*100 if total > 0 else 0:.1f}%)
"""
                
        if report_type == 'monthly':
           
            thirty_days_ago = timezone.now() - timedelta(days=30)
            monthly_invoices = invoices.filter(uploaded_at__gte=thirty_days_ago)
            monthly_count = monthly_invoices.count()
            
            content += f"""
---
 Last 30 Days:
Invoices: {monthly_count}
Daily Average: {monthly_count/30:.1f} invoices/day
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


def branch_users(request):
    branch = request.user.branch
    users = User.objects.filter(branch=branch, role='accounting_staff')

    return render(request, 'branches/users.html', {
        'users': users,
        'branch': branch,
    })



def toggle_user(request, user_id):
    user = User.objects.get(id=user_id, branch=request.user.branch)

    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} {status} successfully!')

    return redirect('branch_users')
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
    branch = request.user.branch

    total_invoices = Invoice.objects.filter(branch=branch).count()
    reviewed = Invoice.objects.filter(branch=branch, status='reviewed').count()
    pending = Invoice.objects.filter(branch=branch, status='pending').count()
    errors = Invoice.objects.filter(branch=branch, status='error').count()

    context = {
        'total_invoices': total_invoices,
        'reviewed': reviewed,
        'pending': pending,
        'errors': errors,
        'branch': branch,
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

        content = f"""
Branch: {branch.name}
Report Type: {report_type}
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}
---
Total Invoices: {total}
Reviewed: {reviewed}
Errors: {errors}
Pending: {total - reviewed - errors}
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
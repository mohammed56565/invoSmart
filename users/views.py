from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, ActivityLog
from branches.models import Branch
from .decorators import role_required
from invoices.models import Invoice
# Create your views here.





def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            ActivityLog.objects.create(
                user=user,
                action='login',
                description=f'{user.username} logged in'
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'users/login.html')

@login_required
def logout_view(request):
    ActivityLog.objects.create(
        user=request.user,
        action='logout',
        description=f'{request.user.username} logged out'
    )
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.email = request.POST['email']
        user.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    
    return render(request, 'users/profile.html')


    

def dashboard(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    role = request.user.role
    
    if role == 'accounting_staff':
        return redirect('invoice_list') 
    elif role == 'branch_manager':
         return redirect('branch_dashboard') 
    elif role == 'system_admin':
        return redirect('admin_dashboard')
    else:
        return render(request, 'users/dashboard.html') 

@role_required('system_admin')
def admin_dashboard(request):
    context = {
        'total_users': User.objects.count(),
        'total_branches': Branch.objects.count(),
        'total_invoices': Invoice.objects.count(),
        'total_errors': Invoice.objects.filter(status='error').count(),
    }
    return render(request, 'users/admin_dashboard.html', context)       
    

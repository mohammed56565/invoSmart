from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, ActivityLog
from branches.models import Branch
from .decorators import role_required
from invoices.models import Invoice

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
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', '')
        
      
        new_password = request.POST.get('new_password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        if new_password:
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                
                ActivityLog.objects.create(
                    user=user,
                    action='password_change',
                    description=f'{user.username} changed password'
                )
                
                messages.success(request, 'Profile and password updated successfully! Please login again.')
                logout(request)
                return redirect('login')
            else:
                messages.error(request, 'Passwords do not match!')
                return redirect('profile')
        
        user.save()
        
        ActivityLog.objects.create(
            user=user,
            action='profile_update',
            description=f'{user.username} updated profile'
        )
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')
    
    return render(request, 'users/profile.html')

@login_required    
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
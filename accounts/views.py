from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.db.models import Q, Count, Sum
from .models import User
from .forms import UserRegistrationForm, UserLoginForm, UserUpdateForm, AdminUserCreationForm, AdminUserEditForm
from academics.models import Course, Enrollment
from finance.models import Payment, FeeStructure

def user_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                # Check if account is approved
                if not user.is_approved and not user.is_superuser:
                    messages.error(request, 'Your account is pending admin approval. Please contact the administrator.')
                    return render(request, 'accounts/login.html', {'form': form})
                
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def user_register(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = False  # Require admin approval
            user.save()
            messages.success(request, 'Registration successful! Your account is pending admin approval. You will be notified once approved.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def user_logout(request):
    messages.info(request, f'Goodbye {request.user.first_name}! You have been logged out successfully.')
    logout(request)
    return redirect('accounts:login')

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}
    
    if user.is_admin:
        context.update({
            'total_students': User.objects.filter(user_type='student').count(),
            'total_teachers': User.objects.filter(user_type='teacher').count(),
            'total_courses': Course.objects.count(),
            'total_revenue': Payment.objects.filter(status='completed').aggregate(
                total=Sum('amount'))['total'] or 0,
            'pending_payments': Payment.objects.filter(status='pending').count(),
            'active_courses': Course.objects.filter(is_active=True).count(),
            'pending_approvals': User.objects.filter(is_approved=False, is_superuser=False).count(),
        })
    elif user.is_teacher:
        # FIXED: Use different name for annotation to avoid property conflict
        my_courses = Course.objects.filter(instructor=user).annotate(
            enrollment_count=Count('enrollments')  # Changed from enrolled_count to enrollment_count
        )
        context.update({
            'my_courses': my_courses,
            'total_students': Enrollment.objects.filter(
                course__instructor=user).values('student').distinct().count(),
        })
    elif user.is_student:
        context.update({
            'enrolled_courses': Enrollment.objects.filter(student=user).select_related('course'),
            'pending_payments': Payment.objects.filter(student=user, status='pending').count(),
            'total_paid': Payment.objects.filter(
                student=user, status='completed').aggregate(
                total=Sum('amount'))['total'] or 0,
        })
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def profile_settings(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'accounts/profile_settings.html', {'form': form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('accounts:profile_settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})

# Admin-only views
def admin_required(user):
    return user.is_authenticated and user.is_admin

@user_passes_test(admin_required)
def user_list(request):
    query = request.GET.get('q', '')
    user_type_filter = request.GET.get('type', '')
    approval_filter = request.GET.get('approval', '')
    
    users = User.objects.all().exclude(id=request.user.id)
    
    if query:
        users = users.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(student_id__icontains=query) |
            Q(teacher_id__icontains=query)
        )
    
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    if approval_filter == 'pending':
        users = users.filter(is_approved=False, is_superuser=False)
    elif approval_filter == 'approved':
        users = users.filter(is_approved=True)
    
    return render(request, 'accounts/admin/user_list.html', {
        'users': users,
        'query': query,
        'user_type_filter': user_type_filter,
        'approval_filter': approval_filter,
    })

@user_passes_test(admin_required)
def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    context = {'view_user': user}
    
    if user.is_student:
        context['enrollments'] = Enrollment.objects.filter(student=user).select_related('course')
        context['payments'] = Payment.objects.filter(student=user).order_by('-created_at')
    elif user.is_teacher:
        context['courses'] = Course.objects.filter(instructor=user).annotate(
            enrolled_count=Count('enrollments')
        )
    
    return render(request, 'accounts/admin/user_detail.html', context)

@user_passes_test(admin_required)
def create_user(request):
    if request.method == 'POST':
        form = AdminUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_approved = True  # Admin-created users are auto-approved
            user.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('accounts:user_detail', user_id=user.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserCreationForm()
    
    return render(request, 'accounts/admin/create_user.html', {'form': form})

@user_passes_test(admin_required)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = AdminUserEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('accounts:user_detail', user_id=user.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminUserEditForm(instance=user)
    
    return render(request, 'accounts/admin/edit_user.html', {
        'form': form,
        'view_user': user
    })

@user_passes_test(admin_required)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('accounts:user_list')
    
    return render(request, 'accounts/admin/delete_user_confirm.html', {'view_user': user})

@user_passes_test(admin_required)
def approve_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_approved = True
    user.is_active = True
    user.save()
    messages.success(request, f'User {user.username} has been approved!')
    return redirect('accounts:user_detail', user_id=user.id)

@user_passes_test(admin_required)
def pending_approvals(request):
    pending_users = User.objects.filter(is_approved=False, is_superuser=False)
    return render(request, 'accounts/admin/pending_approvals.html', {
        'pending_users': pending_users
    })
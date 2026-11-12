from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    
    # User Dashboard & Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.profile_settings, name='profile_settings'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Admin User Management
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/create/', views.create_user, name='create_user'),
    path('users/<int:user_id>/edit/', views.edit_user, name='edit_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/<int:user_id>/approve/', views.approve_user, name='approve_user'),
    path('users/pending/', views.pending_approvals, name='pending_approvals'),
]
from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.finance_dashboard, name='finance_dashboard'),
    
    # Student Payment Views
    path('my-payments/', views.student_payments, name='student_payments'),
    path('payment/<int:payment_id>/pay/', views.make_payment, name='make_payment'),
    path('payment/<int:payment_id>/receipt/', views.payment_receipt, name='payment_receipt'),
    
    # Admin Payment Management
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/pending/', views.pending_payments, name='pending_payments'),
    path('payments/<int:payment_id>/', views.payment_detail, name='payment_detail'),
    path('payments/create/', views.create_payment, name='create_payment'),
    path('payments/bulk-create/', views.create_bulk_payments, name='create_bulk_payments'),
    path('payments/<int:payment_id>/approve/', views.approve_payment, name='approve_payment'),
    path('payments/<int:payment_id>/reject/', views.reject_payment, name='reject_payment'),
    
    # Fee Structure
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/create/', views.fee_structure_create, name='fee_structure_create'),
    path('fee-structures/<int:fee_id>/edit/', views.fee_structure_update, name='fee_structure_update'),
]
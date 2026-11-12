from django.contrib import admin
from .models import FeeStructure, Payment, PaymentReceipt

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ['name', 'fee_type', 'amount', 'is_mandatory', 'is_active']
    list_filter = ['fee_type', 'is_mandatory', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_id', 'student', 'amount', 'status', 'payment_method', 
                    'due_date', 'payment_date']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['student__username', 'transaction_id', 'description']
    raw_id_fields = ['student', 'fee_structure', 'course', 'processed_by']
    date_hierarchy = 'created_at'

@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'payment', 'issued_date', 'issued_by']
    search_fields = ['receipt_number', 'payment__student__username']
    raw_id_fields = ['payment', 'issued_by']
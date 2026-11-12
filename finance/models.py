from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from academics.models import Course
import uuid

class FeeStructure(models.Model):
    FEE_TYPE_CHOICES = (
        ('tuition', 'Tuition Fee'),
        ('lab', 'Lab Fee'),
        ('library', 'Library Fee'),
        ('sports', 'Sports Fee'),
        ('technology', 'Technology Fee'),
        ('other', 'Other Fee'),
    )
    
    name = models.CharField(max_length=200)
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                                 validators=[MinValueValidator(0)])
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['fee_type', 'name']
    
    def __str__(self):
        return f"{self.name} - ${self.amount}"

class Payment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('online', 'Online Payment'),
    )
    
    payment_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, 
                                limit_choices_to={'user_type': 'student'},
                                related_name='payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.SET_NULL, 
                                      null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               help_text="Associated course (if applicable)")
    
    amount = models.DecimalField(max_digits=10, decimal_places=2, 
                                 validators=[MinValueValidator(0)])
    description = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, 
                                      default='cash')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField()
    
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                     related_name='payments_processed')
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.username} - ${self.amount} ({self.status})"
    
    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.status == 'pending' and self.due_date:
            return timezone.now().date() > self.due_date
        return False

#=========================================
#=========333333333333333================================
class PaymentReceipt(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE, 
                                   related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True)
    issued_date = models.DateTimeField(auto_now_add=True)
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Receipt #{self.receipt_number}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Auto-generate receipt number
            import datetime
            date_str = datetime.datetime.now().strftime('%Y%m%d')
            last_receipt = PaymentReceipt.objects.filter(
                receipt_number__startswith=f'REC-{date_str}'
            ).order_by('-receipt_number').first()
            
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.receipt_number = f'REC-{date_str}-{new_num:04d}'
    #=========================================
#=========================================
        
        super().save(*args, **kwargs)
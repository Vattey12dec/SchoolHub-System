from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from .models import Payment, FeeStructure, PaymentReceipt
from .forms import PaymentForm, StudentPaymentForm, FeeStructureForm, BulkPaymentForm, PaymentFilterForm
from accounts.models import User

def admin_required(user):
    return user.is_authenticated and user.is_admin

# Finance Dashboard
@user_passes_test(admin_required)
def finance_dashboard(request):
    total_revenue = Payment.objects.filter(status__in=['completed', 'approved']).aggregate(
        total=Sum('amount'))['total'] or 0
    pending_amount = Payment.objects.filter(status='pending').aggregate(
        total=Sum('amount'))['total'] or 0
    total_payments = Payment.objects.count()
    pending_count = Payment.objects.filter(status='pending').count()
    awaiting_approval = Payment.objects.filter(status='awaiting_approval').count()
    
    recent_payments = Payment.objects.all()[:10]
    
    context = {
        'total_revenue': total_revenue,
        'pending_amount': pending_amount,
        'total_payments': total_payments,
        'pending_count': pending_count,
        'awaiting_approval': awaiting_approval,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'finance/finance_dashboard.html', context)

# Student Payment Views
@login_required
def student_payments(request):
    if not request.user.is_student:
        messages.error(request, 'Only students can access this page.')
        return redirect('accounts:dashboard')
    
    payments = Payment.objects.filter(student=request.user).order_by('-created_at')
    
    total_paid = payments.filter(status='completed').aggregate(
        total=Sum('amount'))['total'] or 0
    total_pending = payments.filter(status='pending').aggregate(
        total=Sum('amount'))['total'] or 0
    
    context = {
        'payments': payments,
        'total_paid': total_paid,
        'total_pending': total_pending,
    }
    
    return render(request, 'finance/student_payments.html', context)

@login_required
def make_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.user.is_student and payment.student != request.user:
        messages.error(request, 'You can only make payments for your own account.')
        return redirect('finance:student_payments')
    
    if payment.status in ['completed', 'approved']:
        messages.info(request, 'This payment has already been processed.')
        return redirect('finance:payment_detail', payment_id=payment.id)
    
    if request.method == 'POST':
        form = StudentPaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            
            if request.user.is_admin:
                # Admin can directly complete payment
                payment.status = 'completed'
                payment.payment_date = timezone.now()
                payment.processed_by = request.user
                payment.save()
                
                # Create receipt
                receipt = PaymentReceipt.objects.create(
                    payment=payment,
                    issued_by=request.user
                )
                messages.success(request, f'Payment completed! Receipt #{receipt.receipt_number}')
            else:
                # Student submits for approval
                payment.status = 'awaiting_approval'
                payment.payment_date = timezone.now()
                payment.save()
                messages.success(request, 'Payment submitted for admin approval!')
            
            return redirect('finance:payment_detail', payment_id=payment.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentPaymentForm(instance=payment)
    
    return render(request, 'finance/make_payment.html', {
        'form': form,
        'payment': payment
    })

@login_required
def payment_receipt(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.user.is_student and payment.student != request.user:
        messages.error(request, 'You can only view your own receipts.')
        return redirect('finance:student_payments')
    
    try:
        receipt = payment.receipt
    except PaymentReceipt.DoesNotExist:
        messages.error(request, 'Receipt not found for this payment.')
        return redirect('finance:payment_detail', payment_id=payment.id)
    
    return render(request, 'finance/payment_receipt.html', {
        'payment': payment,
        'receipt': receipt
    })

#==================================
#=====777777777777777=============================
# Admin Payment Management
@user_passes_test(admin_required)
def payment_list(request):
    payments = Payment.objects.all()
    
    form = PaymentFilterForm(request.GET)
    
    if form.is_valid():
        status = form.cleaned_data.get('status')
        payment_method = form.cleaned_data.get('payment_method')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if status:
            payments = payments.filter(status=status)
        if payment_method:
            payments = payments.filter(payment_method=payment_method)
        if date_from:
            payments = payments.filter(created_at__date__gte=date_from)
        if date_to:
            payments = payments.filter(created_at__date__lte=date_to)
    
    query = request.GET.get('q', '')
    if query:
        payments = payments.filter(
            Q(student__username__icontains=query) |
            Q(student__first_name__icontains=query) |
            Q(student__last_name__icontains=query) |
            Q(description__icontains=query) |
            Q(transaction_id__icontains=query)
        )
#==================================
#==================================
    return render(request, 'finance/payment_list.html', {
        'payments': payments,
        'form': form,
        'query': query
    })


#=========================================
#===============666666666666666==========================
@user_passes_test(admin_required)
def payment_detail(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    try:
        receipt = payment.receipt
    except PaymentReceipt.DoesNotExist:
        receipt = None
    
    return render(request, 'finance/payment_detail.html', {
        'payment': payment,
        'receipt': receipt
    })

#=========================================
#=========================================

@user_passes_test(admin_required)
def create_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.processed_by = request.user
            payment.save()
            messages.success(request, 'Payment created successfully!')
            return redirect('finance:payment_detail', payment_id=payment.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PaymentForm()
    
    return render(request, 'finance/payment_form.html', {
        'form': form,
        'action': 'Create'
    })

#=========================================
#==========55555555555555555===============================
@user_passes_test(admin_required)
def create_bulk_payments(request):
    if request.method == 'POST':
        form = BulkPaymentForm(request.POST)
        if form.is_valid():
            students = form.cleaned_data['students']
            fee_structure = form.cleaned_data['fee_structure']
            due_date = form.cleaned_data['due_date']
            description = form.cleaned_data.get('description', '')
            
            created_count = 0
            for student in students:
                Payment.objects.create(
                    student=student,
                    fee_structure=fee_structure,
                    amount=fee_structure.amount,
                    description=description or f"{fee_structure.name} - {fee_structure.get_fee_type_display()}",
                    due_date=due_date,
                    status='pending',
                    processed_by=request.user
                )
                created_count += 1
            
            messages.success(request, f'Successfully created {created_count} payment records!')
#=========================================
#=========================================
            return redirect('finance:payment_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BulkPaymentForm()
    
    return render(request, 'finance/create_bulk_payment.html', {'form': form})

# Fee Structure Views
@user_passes_test(admin_required)
def fee_structure_list(request):
    fee_structures = FeeStructure.objects.all()
    return render(request, 'finance/fee_structure_list.html', {
        'fee_structures': fee_structures
    })

@user_passes_test(admin_required)
def fee_structure_create(request):
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fee_structure = form.save()
            messages.success(request, f'Fee structure {fee_structure.name} created successfully!')
            return redirect('finance:fee_structure_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeeStructureForm()
    
    return render(request, 'finance/fee_structure_form.html', {
        'form': form,
        'action': 'Create'
    })

@user_passes_test(admin_required)
def fee_structure_update(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id)
    
    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, f'Fee structure {fee_structure.name} updated successfully!')
            return redirect('finance:fee_structure_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = FeeStructureForm(instance=fee_structure)
    
    return render(request, 'finance/fee_structure_form.html', {
        'form': form,
        'fee_structure': fee_structure,
        'action': 'Update'
    })
#
#######===11111111111111111============##################
# Payment Approval Views
@user_passes_test(admin_required)
def approve_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status == 'awaiting_approval':
        payment.status = 'approved'
        payment.processed_by = request.user
        payment.payment_date = timezone.now()
        payment.save()
        
        try:
            receipt = PaymentReceipt.objects.create(
                payment=payment,
                issued_by=request.user
            )
            messages.success(request, f'Payment approved! Receipt #{receipt.receipt_number} generated.')
        except:
            messages.success(request, f'Payment approved! Receipt creation failed.')
        
    elif payment.status == 'approved':
        payment.status = 'completed'
        payment.save()
        messages.success(request, f'Payment marked as completed.')
    else:
        messages.warning(request, 'Payment is not awaiting approval.')
    
    return redirect('finance:payment_detail', payment_id=payment.id)
#==========================================================================================================
#
#
#
#================================================================================================
##==============================================
#===========22222222222222================================
@user_passes_test(admin_required)
def reject_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if payment.status == 'awaiting_approval':
        payment.status = 'rejected'
        payment.processed_by = request.user
        payment.save()
        
        messages.success(request, f'Payment for {payment.student.get_full_name()} rejected.')
    else:
        messages.warning(request, 'Payment is not awaiting approval.')
    
    return redirect('finance:payment_detail', payment_id=payment.id)
#===================================================================


#=========================================
#===========44444444444444==============================
@user_passes_test(admin_required)
def pending_payments(request):
    pending_payments = Payment.objects.filter(
        status='awaiting_approval'
    ).select_related('student', 'fee_structure').order_by('-created_at')
    
    context = {
        'pending_payments': pending_payments,
        'total_pending': pending_payments.count(),
    }
    return render(request, 'finance/pending_payments.html', context)

#=========================================
#=========================================
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from academics.models import Department, Major

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'Email Address'
    }))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control'
    }))
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        empty_label='Select Department',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    major = forms.ModelChoiceField(
        queryset=Major.objects.all(),
        required=False,
        empty_label='Select Major',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 
                  'department', 'major', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Username',
        'id': 'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Password',
        'id': 'password'
    }))

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 
                  'date_of_birth', 'profile_picture', 'department', 'major']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'major': forms.Select(attrs={'class': 'form-control'}),
        }

class AdminUserCreationForm(UserCreationForm):
    # Add teaching_majors field for teachers
    teaching_majors = forms.ModelMultipleChoiceField(
        queryset=Major.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select majors this teacher can teach (for teachers only)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 
                  'phone_number', 'address', 'date_of_birth', 'student_id', 'teacher_id', 
                  'department', 'major', 'teacher_department', 'teaching_majors',
                  'enrollment_date', 'hire_date', 'profile_picture',
                  'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'student_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave empty for auto-generation'
            }),
            'teacher_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Leave empty for auto-generation'
            }),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'major': forms.Select(attrs={'class': 'form-control'}),
            'teacher_department': forms.Select(attrs={'class': 'form-control'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Make IDs optional
        self.fields['student_id'].required = False
        self.fields['teacher_id'].required = False
        
        # Make dates optional
        self.fields['enrollment_date'].required = False
        self.fields['hire_date'].required = False
        self.fields['date_of_birth'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        # Validate student fields
        if user_type == 'student':
            if not cleaned_data.get('department'):
                self.add_error('department', 'Department is required for students')
            if not cleaned_data.get('major'):
                self.add_error('major', 'Major is required for students')
        
        # Validate teacher fields
        if user_type == 'teacher':
            if not cleaned_data.get('teacher_department'):
                self.add_error('teacher_department', 'Department is required for teachers')
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Save ManyToMany field
            if self.cleaned_data.get('teaching_majors'):
                user.teaching_majors.set(self.cleaned_data['teaching_majors'])
        
        return user

class AdminUserEditForm(forms.ModelForm):
    # Add teaching_majors field for teachers
    teaching_majors = forms.ModelMultipleChoiceField(
        queryset=Major.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple(),
        help_text="Select majors this teacher can teach (for teachers only)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'user_type', 
                  'phone_number', 'address', 'date_of_birth', 'is_active', 'is_approved', 
                  'student_id', 'teacher_id', 'department', 'major', 'teacher_department', 
                  'teaching_majors', 'enrollment_date', 'hire_date', 'profile_picture']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'teacher_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'major': forms.Select(attrs={'class': 'form-control'}),
            'teacher_department': forms.Select(attrs={'class': 'form-control'}),
            'enrollment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate teaching_majors if editing existing user
        if self.instance.pk:
            self.fields['teaching_majors'].initial = self.instance.teaching_majors.all()
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        if commit:
            user.save()
            # Save ManyToMany field
            if 'teaching_majors' in self.cleaned_data:
                user.teaching_majors.set(self.cleaned_data['teaching_majors'])
        
        return user
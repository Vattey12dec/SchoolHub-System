from django import forms
from .models import Course, Enrollment, Grade, Department, Major
from accounts.models import User

class CourseForm(forms.ModelForm):
    """Form for creating a new course (from Courses page)"""
    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'credits', 'department', 
                  'instructor', 'semester', 'year', 'capacity', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 6}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'instructor': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['instructor'].queryset = User.objects.filter(user_type='teacher')
        self.fields['department'].queryset = Department.objects.filter(is_active=True)

class AddCourseToMajorForm(forms.Form):
    """Form for adding existing courses to a major (from Major detail page)"""
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=True,
        label="Select courses to add to this major"
    )
    
    def __init__(self, major=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if major:
            # Exclude courses already in this major
            already_added = major.courses.all()
            self.fields['courses'].queryset = Course.objects.filter(
                is_active=True,
                department=major.department
            ).exclude(id__in=[c.id for c in already_added])

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'course']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].queryset = User.objects.filter(user_type='student')
        self.fields['course'].queryset = Course.objects.filter(is_active=True)

class StudentEnrollmentForm(forms.Form):
    course = forms.ModelChoiceField(
        queryset=Course.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a course"
    )

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['numeric_grade', 'midterm_score', 'final_score', 'assignment_score', 
                  'letter_grade', 'comments']
        widgets = {
            'numeric_grade': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': 0, 
                'max': 100
            }),
            'midterm_score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': 0, 
                'max': 100
            }),
            'final_score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': 0, 
                'max': 100
            }),
            'assignment_score': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': 0, 
                'max': 100
            }),
            'letter_grade': forms.Select(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        numeric_grade = cleaned_data.get('numeric_grade')
        
        if numeric_grade:
            grade_obj = Grade()
            grade_obj.numeric_grade = numeric_grade
            cleaned_data['letter_grade'] = grade_obj.calculate_letter_grade()
        
        return cleaned_data

class AddStudentToCourseForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='student'),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select a student"
    )

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'description', 'head_of_department', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computer Science'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'head_of_department': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['head_of_department'].queryset = User.objects.filter(user_type='teacher')
        self.fields['head_of_department'].required = False

class MajorForm(forms.ModelForm):
    class Meta:
        model = Major
        fields = ['name', 'code', 'department', 'description', 'required_credits', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Software Engineering'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., SWE'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'required_credits': forms.NumberInput(attrs={'class': 'form-control', 'value': 120}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].queryset = Department.objects.filter(is_active=True)
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User

class Department(models.Model):
    """Academic Department"""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, help_text="e.g., CS, MATH, ENG")
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        limit_choices_to={'user_type': 'teacher'},
        related_name='department_headed'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def major_count(self):
        return self.majors.count()
    
    @property
    def course_count(self):
        return self.courses.count()
    
    @property
    def student_count(self):
        return User.objects.filter(user_type='student', department=self).count()

class Major(models.Model):
    """Academic Major within a Department"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, help_text="e.g., SWE, DS, ACC")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='majors')
    description = models.TextField(blank=True)
    required_credits = models.IntegerField(default=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['department', 'name']
        unique_together = ['department', 'code']
    
    def __str__(self):
        return f"{self.department.code}-{self.code} - {self.name}"
    
    @property
    def course_count(self):
        return self.courses.count()
    
    @property
    def student_count(self):
        return User.objects.filter(user_type='student', major=self).count()

class Course(models.Model):
    SEMESTER_CHOICES = (
        ('fall', 'Fall'),
        ('spring', 'Spring'),
        ('summer', 'Summer'),
    )
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(6)])
    
    # Link to Department only (removed direct major ForeignKey)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    
    # CHANGED: Many-to-Many relationship with Major
    majors = models.ManyToManyField(Major, related_name='courses', blank=True,
                                    help_text="Which majors can take this course?")
    
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                   limit_choices_to={'user_type': 'teacher'},
                                   related_name='courses_teaching')
    semester = models.CharField(max_length=10, choices=SEMESTER_CHOICES)
    year = models.IntegerField()
    capacity = models.IntegerField(default=30)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year', 'semester', 'code']
        unique_together = ['code', 'semester', 'year']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    @property
    def enrolled_count(self):
        return self.enrollments.filter(status='enrolled').count()
    
    @property
    def is_full(self):
        return self.enrolled_count >= self.capacity
    
    @property
    def available_slots(self):
        return max(0, self.capacity - self.enrolled_count)

class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('enrolled', 'Enrolled'),
        ('dropped', 'Dropped'),
        ('completed', 'Completed'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, 
                                limit_choices_to={'user_type': 'student'},
                                related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, 
                               related_name='enrollments')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='enrolled')
    enrollment_date = models.DateTimeField(auto_now_add=True)
    drop_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-enrollment_date']
        unique_together = ['student', 'course']
    
    def __str__(self):
        return f"{self.student.username} - {self.course.code}"

class Grade(models.Model):
    GRADE_CHOICES = (
        ('A+', 'A+ (97-100)'),
        ('A', 'A (93-96)'),
        ('A-', 'A- (90-92)'),
        ('B+', 'B+ (87-89)'),
        ('B', 'B (83-86)'),
        ('B-', 'B- (80-82)'),
        ('C+', 'C+ (77-79)'),
        ('C', 'C (73-76)'),
        ('C-', 'C- (70-72)'),
        ('D+', 'D+ (67-69)'),
        ('D', 'D (63-66)'),
        ('D-', 'D- (60-62)'),
        ('F', 'F (<60)'),
    )
    
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE, 
                                      related_name='grade')
    letter_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, null=True)
    numeric_grade = models.DecimalField(max_digits=5, decimal_places=2, 
                                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                                        blank=True, null=True)
    
    midterm_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                                        blank=True, null=True,
                                        help_text="Weight: 30%")
    final_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                      validators=[MinValueValidator(0), MaxValueValidator(100)],
                                      blank=True, null=True,
                                      help_text="Weight: 40%")
    assignment_score = models.DecimalField(max_digits=5, decimal_places=2, 
                                           validators=[MinValueValidator(0), MaxValueValidator(100)],
                                           blank=True, null=True,
                                           help_text="Weight: 30%")
    
    comments = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='grades_given')
    graded_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-graded_at']
    
    def __str__(self):
        return f"{self.enrollment.student.username} - {self.enrollment.course.code}: {self.letter_grade or 'Not Graded'}"
    
    def calculate_numeric_grade(self):
        if all([self.midterm_score, self.final_score, self.assignment_score]):
            total = (
                float(self.midterm_score) * 0.30 +
                float(self.final_score) * 0.40 +
                float(self.assignment_score) * 0.30
            )
            return round(total, 2)
        return None
    
    def calculate_letter_grade(self, numeric=None):
        score = numeric if numeric is not None else self.numeric_grade
        if score is None:
            return None
        
        score = float(score)
        if score >= 97: return 'A+'
        elif score >= 93: return 'A'
        elif score >= 90: return 'A-'
        elif score >= 87: return 'B+'
        elif score >= 83: return 'B'
        elif score >= 80: return 'B-'
        elif score >= 77: return 'C+'
        elif score >= 73: return 'C'
        elif score >= 70: return 'C-'
        elif score >= 67: return 'D+'
        elif score >= 63: return 'D'
        elif score >= 60: return 'D-'
        else: return 'F'
    
    def save(self, *args, **kwargs):
        if not self.numeric_grade and all([self.midterm_score, self.final_score, self.assignment_score]):
            self.numeric_grade = self.calculate_numeric_grade()
        
        if self.numeric_grade:
            self.letter_grade = self.calculate_letter_grade(self.numeric_grade)
        
        super().save(*args, **kwargs)
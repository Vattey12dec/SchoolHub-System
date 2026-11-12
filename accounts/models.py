from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    # Account approval
    is_approved = models.BooleanField(default=False, help_text='Admin must approve new accounts')
    
    # Student specific - NOW with ForeignKey to Department and Major
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    enrollment_date = models.DateField(blank=True, null=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, 
                                   null=True, blank=True, related_name='students')
    major = models.ForeignKey('academics.Major', on_delete=models.SET_NULL, 
                              null=True, blank=True, related_name='students')
    
    # Teacher specific
    teacher_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    hire_date = models.DateField(blank=True, null=True)
    teacher_department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL,
                                          null=True, blank=True, related_name='teachers')
    # Teacher can teach multiple majors
    teaching_majors = models.ManyToManyField('academics.Major', blank=True, 
                                             related_name='teachers')
    
    class Meta:
        ordering = ['username']
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_admin(self):
        return self.user_type == 'admin'
    
    @property
    def is_teacher(self):
        return self.user_type == 'teacher'
    
    @property
    def is_student(self):
        return self.user_type == 'student'
    
    def save(self, *args, **kwargs):
        # Auto-generate IDs if not provided
        if self.user_type == 'student' and not self.student_id:
            from datetime import datetime
            year = datetime.now().year
            random_num = str(uuid.uuid4().int)[:4]
            self.student_id = f'STU{year}{random_num}'
        
        if self.user_type == 'teacher' and not self.teacher_id:
            from datetime import datetime
            year = datetime.now().year
            random_num = str(uuid.uuid4().int)[:3]
            self.teacher_id = f'TCH{year}{random_num}'
        
        # Auto-approve admins and superusers
        if self.is_superuser or self.user_type == 'admin':
            self.is_approved = True
        
        super().save(*args, **kwargs)
from django.contrib import admin
from .models import Course, Enrollment, Grade, Department, Major

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'head_of_department', 'major_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']

@admin.register(Major)
class MajorAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'department', 'required_credits', 'is_active']
    list_filter = ['department', 'is_active']
    search_fields = ['name', 'code']
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'instructor', 'semester', 'year', 'credits', 'is_active']
    list_filter = ['semester', 'year', 'is_active', 'instructor']
    search_fields = ['code', 'name', 'instructor__username']
    list_editable = ['is_active']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrollment_date']
    list_filter = ['status', 'enrollment_date']
    search_fields = ['student__username', 'course__code', 'course__name']
    raw_id_fields = ['student', 'course']

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'letter_grade', 'numeric_grade', 'graded_by', 'graded_at']
    list_filter = ['letter_grade', 'graded_at']
    search_fields = ['enrollment__student__username', 'enrollment__course__code']
    raw_id_fields = ['enrollment', 'graded_by']
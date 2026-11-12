from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from .models import Course, Department, Major, Enrollment, Grade
from .forms import (CourseForm, AddCourseToMajorForm, DepartmentForm, MajorForm,
                    StudentEnrollmentForm, GradeForm, AddStudentToCourseForm)
from accounts.models import User

# ==================== COURSE VIEWS ====================

@login_required
def course_list(request):
    courses = Course.objects.all().select_related('department', 'instructor')
    search = request.GET.get('search', '')
    if search:
        courses = courses.filter(Q(code__icontains=search) | Q(name__icontains=search))
    return render(request, 'academics/course_list.html', {'courses': courses, 'search': search})

@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.code}" created!')
            return redirect('academics:course_detail', course_id=course.id)
    else:
        form = CourseForm()
    return render(request, 'academics/course_form.html', {'form': form, 'action': 'Create'})

@login_required
def course_update(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, f'Course "{course.code}" updated!')
            return redirect('academics:course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'academics/course_form.html', {'form': form, 'course': course, 'action': 'Edit'})

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = course.enrollments.filter(status='enrolled').select_related('student')
    return render(request, 'academics/course_detail.html', {'course': course, 'enrollments': enrollments})

@login_required
def course_delete(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        course_code = course.code
        course.delete()
        messages.success(request, f'Course "{course_code}" deleted!')
        return redirect('academics:course_list')
    return render(request, 'academics/course_confirm_delete.html', {'course': course})

# ==================== MAJOR VIEWS ====================

@login_required
def major_detail(request, major_id):
    major = get_object_or_404(Major.objects.select_related('department'), id=major_id)
    courses = major.courses.all().select_related('instructor')
    students = User.objects.filter(user_type='student', major=major)
    return render(request, 'academics/major_detail.html', {'major': major, 'courses': courses, 'students': students})

@login_required
def add_course_to_major(request, major_id):
    major = get_object_or_404(Major, id=major_id)
    if request.method == 'POST':
        form = AddCourseToMajorForm(major=major, data=request.POST)
        if form.is_valid():
            selected_courses = form.cleaned_data['courses']
            for course in selected_courses:
                major.courses.add(course)
            messages.success(request, f'{selected_courses.count()} course(s) added to {major.name}!')
            return redirect('academics:major_detail', major_id=major.id)
    else:
        form = AddCourseToMajorForm(major=major)
    return render(request, 'academics/add_course_to_major.html', {'form': form, 'major': major})

@login_required
def remove_course_from_major(request, major_id, course_id):
    major = get_object_or_404(Major, id=major_id)
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        major.courses.remove(course)
        messages.success(request, f'Course "{course.code}" removed from {major.name}!')
        return redirect('academics:major_detail', major_id=major.id)
    return render(request, 'academics/remove_course_from_major_confirm.html', {'major': major, 'course': course})

@login_required
def major_create(request, dept_id=None):
    if request.method == 'POST':
        form = MajorForm(request.POST)
        if form.is_valid():
            major = form.save()
            messages.success(request, f'Major "{major.name}" created!')
            return redirect('academics:major_detail', major_id=major.id)
    else:
        initial = {'department': dept_id} if dept_id else {}
        form = MajorForm(initial=initial)
    return render(request, 'academics/major_form.html', {'form': form, 'action': 'Create'})

@login_required
def major_update(request, major_id):
    major = get_object_or_404(Major, id=major_id)
    if request.method == 'POST':
        form = MajorForm(request.POST, instance=major)
        if form.is_valid():
            form.save()
            messages.success(request, f'Major "{major.name}" updated!')
            return redirect('academics:major_detail', major_id=major.id)
    else:
        form = MajorForm(instance=major)
    return render(request, 'academics/major_form.html', {'form': form, 'major': major, 'action': 'Edit'})

@login_required
def major_delete(request, major_id):
    major = get_object_or_404(Major, id=major_id)
    department = major.department
    if request.method == 'POST':
        major_name = major.name
        major.delete()
        messages.success(request, f'Major "{major_name}" deleted!')
        return redirect('academics:department_detail', dept_id=department.id)
    return render(request, 'academics/major_confirm_delete.html', {'major': major})

# ==================== DEPARTMENT VIEWS ====================

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'academics/department_list.html', {'departments': departments})

@login_required
def department_detail(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    majors = department.majors.all()
    courses = department.courses.all()
    return render(request, 'academics/department_detail.html', {'department': department, 'majors': majors, 'courses': courses})

@login_required
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            messages.success(request, f'Department "{department.name}" created!')
            return redirect('academics:department_detail', dept_id=department.id)
    else:
        form = DepartmentForm()
    return render(request, 'academics/department_form.html', {'form': form, 'action': 'Create'})

@login_required
def department_update(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, f'Department "{department.name}" updated!')
            return redirect('academics:department_detail', dept_id=department.id)
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'academics/department_form.html', {'form': form, 'department': department, 'action': 'Edit'})

@login_required
def department_delete(request, dept_id):
    department = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        dept_name = department.name
        department.delete()
        messages.success(request, f'Department "{dept_name}" deleted!')
        return redirect('academics:department_list')
    return render(request, 'academics/department_confirm_delete.html', {'department': department})

# ==================== ENROLLMENT VIEWS ====================

@login_required
def student_enrollment(request):
    if request.method == 'POST':
        form = StudentEnrollmentForm(request.POST)
        if form.is_valid():
            course = form.cleaned_data['course']
            if Enrollment.objects.filter(student=request.user, course=course).exists():
                messages.error(request, 'Already enrolled in this course.')
            elif course.is_full:
                messages.error(request, 'Course is full.')
            else:
                Enrollment.objects.create(student=request.user, course=course)
                messages.success(request, f'Enrolled in {course.code}!')
            return redirect('academics:student_enrollment')
    else:
        form = StudentEnrollmentForm()
    enrollments = Enrollment.objects.filter(student=request.user, status='enrolled').select_related('course')
    return render(request, 'academics/student_enrollment.html', {'form': form, 'enrollments': enrollments})

@login_required
def drop_course(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    if request.method == 'POST':
        enrollment.status = 'dropped'
        enrollment.drop_date = timezone.now()
        enrollment.save()
        messages.success(request, f'Dropped {enrollment.course.code}.')
        return redirect('academics:student_enrollment')
    return render(request, 'academics/drop_course_confirm.html', {'enrollment': enrollment})

@login_required
def add_student_to_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = AddStudentToCourseForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            if Enrollment.objects.filter(student=student, course=course).exists():
                messages.error(request, f'{student.get_full_name()} already enrolled.')
            elif course.is_full:
                messages.error(request, 'Course is full.')
            else:
                Enrollment.objects.create(student=student, course=course)
                messages.success(request, f'{student.get_full_name()} enrolled!')
            return redirect('academics:course_detail', course_id=course.id)
    else:
        form = AddStudentToCourseForm()
    return render(request, 'academics/add_student_to_course.html', {'form': form, 'course': course})

# ==================== GRADE VIEWS ====================

@login_required
def grade_student(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    grade, created = Grade.objects.get_or_create(enrollment=enrollment, defaults={'graded_by': request.user})
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.graded_by = request.user
            grade.save()
            messages.success(request, f'Grade saved for {enrollment.student.get_full_name()}.')
            return redirect('academics:course_detail', course_id=enrollment.course.id)
    else:
        form = GradeForm(instance=grade)
    return render(request, 'academics/grade_form.html', {'form': form, 'enrollment': enrollment, 'grade': grade})

@login_required
def student_grades(request):
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course', 'grade').order_by('-enrollment_date')
    return render(request, 'academics/student_grades.html', {'enrollments': enrollments})

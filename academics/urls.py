from django.urls import path
from . import views

app_name = 'academics'

urlpatterns = [
    # Department URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:dept_id>/', views.department_detail, name='department_detail'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:dept_id>/edit/', views.department_update, name='department_update'),
    path('departments/<int:dept_id>/delete/', views.department_delete, name='department_delete'),
    
    # Major URLs
    path('majors/<int:major_id>/', views.major_detail, name='major_detail'),
    path('majors/create/', views.major_create, name='major_create'),
    path('departments/<int:dept_id>/majors/create/', views.major_create, name='major_create_in_dept'),
    path('majors/<int:major_id>/edit/', views.major_update, name='major_update'),
    path('majors/<int:major_id>/delete/', views.major_delete, name='major_delete'),
    
    # NEW: Add/Remove courses to/from major
    path('majors/<int:major_id>/add-course/', views.add_course_to_major, name='add_course_to_major'),
    path('majors/<int:major_id>/remove-course/<int:course_id>/', views.remove_course_from_major, name='remove_course_from_major'),
    
    # Course URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:course_id>/edit/', views.course_update, name='course_update'),
    path('courses/<int:course_id>/delete/', views.course_delete, name='course_delete'),
    
    # Enrollment URLs
    path('enroll/', views.student_enrollment, name='student_enrollment'),
    path('enrollment/<int:enrollment_id>/drop/', views.drop_course, name='drop_course'),
    path('courses/<int:course_id>/add-student/', views.add_student_to_course, name='add_student_to_course'),
    
    # Grade URLs
    path('enrollment/<int:enrollment_id>/grade/', views.grade_student, name='grade_student'),
    path('my-grades/', views.student_grades, name='student_grades'),
]
from django.urls import path

from . import views

app_name = "training_app"
urlpatterns = [
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Cadet URLs
    # path('cadet/dashboard/', views.cadet_dashboard, name='cadet_dashboard'),
    path('cadet/test/<int:test_id>/', views.take_test, name='take_test'),
    path('cadet/test/<int:test_id>/submit/', views.submit_test, name='submit_test'),
    path('cadet/test/<int:test_id>/save-progress/', views.save_test_progress, name='save_test_progress'),
    
    # Instructor URLs
    # path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('instructor/cadet/<int:cadet_id>/progress/', views.view_cadet_progress, name='view_cadet_progress'),
    path('instructor/cadet/<int:cadet_id>/test-history/', views.view_cadet_test_history, name='view_cadet_test_history'),
    
    # Admin URLs
    # path('administration/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('administration/courses/', views.manage_courses, name='manage_courses'),
    path('administration/courses/create/', views.create_course, name='create_course'),
    path('administration/courses/<int:course_id>/edit/', views.edit_course, name='edit_course'),
    path('administration/courses/<int:course_id>/delete/', views.delete_course, name='delete_course'),
    path('administration/<int:course_id>/tests/', views.manage_tests, name='manage_tests'),
    path('administration/<int:course_id>/tests/create/', views.create_test, name='create_test'),
    path('administration/<int:course_id>/tests/<int:test_id>/edit/', views.edit_test, name='edit_test'),
    path('administration/<int:course_id>/tests/<int:test_id>/delete/', views.delete_test, name='delete_test'),
    path('administration/<int:course_id>/tests/<int:test_id>/questions/', views.manage_test_questions, name='manage_test_questions'),
    path('administration/<int:course_id>/tests/<int:test_id>/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    path('administration/users/', views.manage_users, name='manage_users'),
    path('administration/users/<int:user_id>/progress/', views.view_user_progress, name='view_user_progress'),
    path('administration/assign-instructor/', views.assign_instructor, name='assign_instructor'),
    
    # API URLs
    path('api/test/<int:test_id>/questions/', views.get_test_questions, name='get_test_questions'),
    path('api/test/<int:test_id>/progress/', views.save_test_progress, name='save_test_progress'),
    path('api/course/<int:course_id>/progress/', views.get_course_progress, name='get_course_progress'),
    
    # Legacy URLs (from the tutorial)
    path("", views.IndexView.as_view(), name="index"),
    # ex: /polls/5/
    # path("question/<int:pk>/", views.DetailView.as_view(), name="detail"),
    # ex: /polls/5/results/
    path("question/<int:pk>/results/", views.ResultsView.as_view(), name="results"),
    # ex: /polls/5/vote/
    path("question/<int:question_id>/vote/", views.vote, name="vote"),
]

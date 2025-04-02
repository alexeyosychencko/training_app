from django.db.models import F
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q

from .models import (
    User, Organization, Course, Test, Question, 
    Choice, TestAttempt, CourseProgress, TestUnlock, 
    InstructorAssignment
)
from .forms import (
    UserRegistrationForm, TestSubmissionForm, 
    CourseCreationForm, QuestionForm, ChoiceFormSet, TestCreationForm
)

class IndexView(generic.TemplateView):
    template_name = "training_app/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            # Get user type from the user object
            user_type = getattr(self.request.user, 'user_type', None)
            
            if user_type == 'admin':
                # Admin dashboard data
                context['stats'] = {
                    'total_cadets': User.objects.filter(user_type='cadet').count(),
                    'total_instructors': User.objects.filter(user_type='instructor').count(),
                    'total_courses': Course.objects.count(),
                    'total_tests': Test.objects.count(),
                }
                context['recent_attempts'] = TestAttempt.objects.select_related(
                    'cadet', 'test'
                ).order_by('-completed_at')[:5]
                
            elif user_type == 'instructor':
                # Instructor dashboard data
                context['assigned_cadets'] = InstructorAssignment.objects.filter(
                    instructor=self.request.user
                ).select_related('cadet', 'course')[:5]
                
            elif user_type == 'cadet':
                # Cadet dashboard data
                context['course_progress'] = CourseProgress.objects.filter(
                    cadet=self.request.user
                ).select_related('course')[:5]
                context['available_tests'] = TestUnlock.objects.filter(
                    cadet=self.request.user,
                    is_unlocked=True
                ).select_related('test')[:5]
        
        return context

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(
            request,
            "training/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("training:results", args=(question.id,)))
    
class ResultsView(generic.DetailView):
    model = Question
    template_name = "training/results.html"

# def results(request, question_id):
#     question = get_object_or_404(Question, pk=question_id)
#     return render(request, "training/results.html", {"question": question})

# Authentication Views
def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save(commit=False)
                # user.user_type = 'cadet'  # Default to cadet
                # user.username = user.email
                user.save()
                login(request, user)
                messages.success(request, 'Registration successful! Welcome to your dashboard.')
                return redirect('training_app:cadet_dashboard')
            except Exception as e:
                messages.error(request, f'An error occurred during registration: {str(e)}')
                return render(request, 'training_app/register.html', {'form': form})
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserRegistrationForm()
    return render(request, 'training_app/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('training_app:index')
        else:
            messages.error(request, 'Invalid email or password.')
    return render(request, 'training_app/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('training_app:login')

# Cadet Views
# @login_required
# def cadet_dashboard(request):
#     if request.user.user_type != 'cadet':
#         return HttpResponseForbidden("Access denied")
    
#     # Get cadet's progress
#     course_progress = CourseProgress.objects.filter(cadet=request.user)
#     # Get available tests
#     available_tests = TestUnlock.objects.filter(
#         cadet=request.user,
#         is_unlocked=True
#     ).select_related('test')
    
#     context = {
#         'course_progress': course_progress,
#         'available_tests': available_tests,
#     }
#     return render(request, 'training_app/cadet/dashboard.html', context)

@login_required
def take_test(request, test_id):
    if request.user.user_type != 'cadet':
        return HttpResponseForbidden("Access denied")
    
    test = get_object_or_404(Test, id=test_id)
    # Check if test is unlocked
    if not TestUnlock.objects.filter(cadet=request.user, test=test, is_unlocked=True).exists():
        messages.error(request, "This test is not available yet.")
        return redirect('cadet_dashboard')
    
    # Check if user has attempts remaining
    attempts = TestAttempt.objects.filter(cadet=request.user, test=test).count()
    if attempts >= test.max_attempts:
        messages.error(request, "You have no attempts remaining for this test.")
        return redirect('cadet_dashboard')
    
    if request.method == 'POST':
        form = TestSubmissionForm(request.POST, test=test)
        if form.is_valid():
            # Calculate score
            score = form.calculate_score()
            # Create test attempt
            attempt = TestAttempt.objects.create(
                cadet=request.user,
                test=test,
                score=score,
                is_passed=score >= test.passing_score,
                completed_at=timezone.now()
            )
            
            if attempt.is_passed:
                # Unlock next test if applicable
                next_test = Test.objects.filter(
                    course=test.course,
                    test_type='midterm' if test.test_type == 'entrance' else 'exit'
                ).first()
                if next_test:
                    TestUnlock.objects.create(cadet=request.user, test=next_test)
            
            messages.success(request, f"Test completed! Score: {score}%")
            return redirect('cadet_dashboard')
    else:
        form = TestSubmissionForm(test=test)
    
    return render(request, 'training_app/cadet/take_test.html', {
        'test': test,
        'form': form,
        'time_remaining': test.duration_minutes * 60
    })

@login_required
def submit_test(request, test_id):
    if request.user.user_type != 'cadet':
        return HttpResponseForbidden("Access denied")
    
    test = get_object_or_404(Test, id=test_id)
    
    # Check if test is unlocked
    if not TestUnlock.objects.filter(cadet=request.user, test=test, is_unlocked=True).exists():
        messages.error(request, "This test is not available yet.")
        return redirect('training_app:cadet_dashboard')
    
    # Check if user has attempts remaining
    attempts = TestAttempt.objects.filter(cadet=request.user, test=test).count()
    if attempts >= test.max_attempts:
        messages.error(request, "You have no attempts remaining for this test.")
        return redirect('training_app:cadet_dashboard')
    
    if request.method == 'POST':
        form = TestSubmissionForm(request.POST, test=test)
        if form.is_valid():
            # Calculate score
            score = form.calculate_score()
            
            # Create test attempt
            attempt = TestAttempt.objects.create(
                cadet=request.user,
                test=test,
                score=score,
                is_passed=score >= test.passing_score,
                completed_at=timezone.now()
            )
            
            if attempt.is_passed:
                # Unlock next test if applicable
                next_test = Test.objects.filter(
                    course=test.course,
                    test_type='midterm' if test.test_type == 'entrance' else 'exit'
                ).first()
                if next_test:
                    TestUnlock.objects.create(cadet=request.user, test=next_test)
            
            messages.success(request, f"Test completed! Score: {score}%")
            return redirect('training_app:cadet_dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = TestSubmissionForm(test=test)
    
    return render(request, 'training_app/cadet/take_test.html', {
        'test': test,
        'form': form,
        'time_remaining': test.duration_minutes * 60
    })

# Instructor Views
# @login_required
# def instructor_dashboard(request):
#     if request.user.user_type != 'instructor':
#         return HttpResponseForbidden("Access denied")
    
#     # Get assigned cadets
#     assigned_cadets = InstructorAssignment.objects.filter(
#         instructor=request.user
#     ).select_related('cadet', 'course')
    
#     # Get cadet progress
#     cadet_progress = {}
#     for assignment in assigned_cadets:
#         cadet_progress[assignment.cadet] = {
#             'course': assignment.course,
#             'progress': CourseProgress.objects.filter(
#                 cadet=assignment.cadet,
#                 course=assignment.course
#             ).first(),
#             'test_attempts': TestAttempt.objects.filter(
#                 cadet=assignment.cadet,
#                 test__course=assignment.course
#             ).order_by('-completed_at')
#         }
    
#     context = {
#         'assigned_cadets': assigned_cadets,
#         'cadet_progress': cadet_progress,
#     }
#     return render(request, 'training_app/instructor/dashboard.html', context)

@login_required
def view_cadet_progress(request, cadet_id):
    if request.user.user_type != 'instructor':
        return HttpResponseForbidden("Access denied")
    
    cadet = get_object_or_404(User, id=cadet_id, user_type='cadet')
    # Verify instructor is assigned to this cadet
    if not InstructorAssignment.objects.filter(
        instructor=request.user,
        cadet=cadet
    ).exists():
        return HttpResponseForbidden("Access denied")
    
    # Get cadet's progress
    course_progress = CourseProgress.objects.filter(cadet=cadet)
    test_attempts = TestAttempt.objects.filter(cadet=cadet).order_by('-completed_at')
    
    context = {
        'cadet': cadet,
        'course_progress': course_progress,
        'test_attempts': test_attempts,
    }
    return render(request, 'training_app/instructor/cadet_progress.html', context)

@login_required
def view_cadet_test_history(request, cadet_id):
    if request.user.user_type != 'instructor':
        return HttpResponseForbidden("Access denied")
    
    cadet = get_object_or_404(User, id=cadet_id, user_type='cadet')
    
    # Verify instructor is assigned to this cadet
    if not InstructorAssignment.objects.filter(
        instructor=request.user,
        cadet=cadet
    ).exists():
        return HttpResponseForbidden("Access denied")
    
    # Get all test attempts for this cadet
    test_attempts = TestAttempt.objects.filter(
        cadet=cadet
    ).select_related(
        'test', 'test__course'
    ).order_by('-completed_at')
    
    # Group attempts by course
    attempts_by_course = {}
    for attempt in test_attempts:
        course = attempt.test.course
        if course not in attempts_by_course:
            attempts_by_course[course] = []
        attempts_by_course[course].append(attempt)
    
    context = {
        'cadet': cadet,
        'attempts_by_course': attempts_by_course,
    }
    return render(request, 'training_app/instructor/cadet_test_history.html', context)

# Admin Views
# @login_required
# @user_passes_test(lambda u: u.user_type == 'admin')
# def admin_dashboard(request):
#     # Get system statistics
#     stats = {
#         'total_cadets': User.objects.filter(user_type='cadet').count(),
#         'total_instructors': User.objects.filter(user_type='instructor').count(),
#         'total_courses': Course.objects.count(),
#         'total_tests': Test.objects.count(),
#         'active_courses': Course.objects.filter(is_active=True).count(),
#     }
    
#     # Get recent test attempts
#     recent_attempts = TestAttempt.objects.select_related(
#         'cadet', 'test'
#     ).order_by('-completed_at')[:10]
    
#     context = {
#         'stats': stats,
#         'recent_attempts': recent_attempts,
#     }
#     return render(request, 'training_app/admin/dashboard.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_courses(request):
    if request.method == 'POST':
        form = CourseCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course created successfully.')
            return redirect('training_app:manage_courses')
    else:
        form = CourseCreationForm()
    
    courses = Course.objects.all()
    return render(request, 'training_app/admin/manage_courses.html', {
        'courses': courses,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_tests(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = course.tests.first()  # Or get specific test
            question.save()
            messages.success(request, 'Question added successfully.')
            return redirect('training_app:manage_tests', course_id=course_id)
    else:
        form = QuestionForm()
    
    tests = course.tests.all()
    return render(request, 'training_app/admin/manage_tests.html', {
        'course': course,
        'tests': tests,
        'form': form
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_users(request):
    cadets = User.objects.filter(user_type='cadet')
    instructors = User.objects.filter(user_type='instructor')
    
    return render(request, 'training_app/admin/manage_users.html', {
        'cadets': cadets,
        'instructors': instructors
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def assign_instructor(request):
    if request.method == 'POST':
        instructor_id = request.POST.get('instructor')
        cadet_id = request.POST.get('cadet')
        course_id = request.POST.get('course')
        
        instructor = get_object_or_404(User, id=instructor_id, user_type='instructor')
        cadet = get_object_or_404(User, id=cadet_id, user_type='cadet')
        course = get_object_or_404(Course, id=course_id)
        
        InstructorAssignment.objects.create(
            instructor=instructor,
            cadet=cadet,
            course=course
        )
        messages.success(request, 'Instructor assigned successfully.')
        return redirect('training_app:manage_users')
    
    instructors = User.objects.filter(user_type='instructor')
    cadets = User.objects.filter(user_type='cadet')
    courses = Course.objects.filter(is_active=True)
    
    return render(request, 'training_app/admin/assign_instructor.html', {
        'instructors': instructors,
        'cadets': cadets,
        'courses': courses
    })

# API Views for AJAX requests
@login_required
def get_test_questions(request, test_id):
    test = get_object_or_404(Test, id=test_id)
    questions = test.questions.all()
    
    data = []
    for question in questions:
        choices = [
            {'id': choice.id, 'text': choice.choice_text}
            for choice in question.choices.all()
        ]
        data.append({
            'id': question.id,
            'text': question.question_text,
            'type': question.question_type,
            'points': question.points,
            'choices': choices
        })
    
    return JsonResponse({'questions': data})

@login_required
def save_test_progress(request, test_id):
    if request.method == 'POST':
        test = get_object_or_404(Test, id=test_id)
        answers = request.POST.get('answers')
        
        # Save progress (implement as needed)
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def manage_test_questions(request, course_id, test_id):
    course = get_object_or_404(Course, id=course_id)
    test = get_object_or_404(Test, id=test_id, course=course)
    
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            
            # Handle choices if it's a multiple choice or true/false question
            print(question.question_type)
            if question.question_type in ['multiple_choice', 'true_false']:
                choice_formset = ChoiceFormSet(request.POST, instance=question)
                print(choice_formset.is_valid())
                if choice_formset.is_valid():
                    choice_formset.save()
                    messages.success(request, 'Question and choices added successfully.')
                else:
                    messages.error(request, 'Error saving choices.')
            else:
                messages.success(request, 'Question added successfully.')
            
            return redirect('training_app:manage_test_questions', course_id=course_id, test_id=test_id)
        else:
            messages.error(request, 'Error adding question.')
    else:
        form = QuestionForm()
    
    # Get all questions for this test
    questions = Question.objects.filter(test=test).prefetch_related('choices')
    
    context = {
        'course': course,
        'test': test,
        'form': form,
        'questions': questions,
    }
    return render(request, 'training_app/admin/manage_test_questions.html', context)

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def view_user_progress(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    # Get user's course progress
    course_progress = CourseProgress.objects.filter(
        cadet=user
    ).select_related('course')
    
    # Get user's test attempts
    test_attempts = TestAttempt.objects.filter(
        cadet=user
    ).select_related(
        'test', 'test__course'
    ).order_by('-completed_at')
    
    # Get user's test unlocks
    test_unlocks = TestUnlock.objects.filter(
        cadet=user
    ).select_related('test')
    
    # Get instructor assignments
    instructor_assignments = InstructorAssignment.objects.filter(
        cadet=user
    ).select_related('instructor', 'course')
    
    # Group test attempts by course
    attempts_by_course = {}
    for attempt in test_attempts:
        course = attempt.test.course
        if course not in attempts_by_course:
            attempts_by_course[course] = []
        attempts_by_course[course].append(attempt)
    
    context = {
        'user': user,
        'course_progress': course_progress,
        'attempts_by_course': attempts_by_course,
        'test_unlocks': test_unlocks,
        'instructor_assignments': instructor_assignments,
    }
    return render(request, 'training_app/admin/user_progress.html', context)

@login_required
def get_course_progress(request, course_id):
    """API endpoint to get course progress data for the current user."""
    if request.user.user_type != 'cadet':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    course = get_object_or_404(Course, id=course_id)
    
    # Get user's progress for this course
    progress = CourseProgress.objects.filter(
        cadet=request.user,
        course=course
    ).first()
    
    if not progress:
        return JsonResponse({
            'error': 'No progress found for this course'
        }, status=404)
    
    # Get test attempts for this course
    test_attempts = TestAttempt.objects.filter(
        cadet=request.user,
        test__course=course
    ).select_related('test').order_by('-completed_at')
    
    # Format test attempts data
    attempts_data = [{
        'test_title': attempt.test.title,
        'test_type': attempt.test.get_test_type_display(),
        'score': attempt.score,
        'is_passed': attempt.is_passed,
        'completed_at': attempt.completed_at.strftime('%Y-%m-%d %H:%M:%S') if attempt.completed_at else None
    } for attempt in test_attempts]
    
    return JsonResponse({
        'course_name': course.name,
        'current_level': progress.current_level,
        'is_completed': progress.is_completed,
        'completed_at': progress.completed_at.strftime('%Y-%m-%d %H:%M:%S') if progress.completed_at else None,
        'test_attempts': attempts_data
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def create_course(request):
    """Create a new course."""
    if request.method == 'POST':
        form = CourseCreationForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" has been created successfully.')
            return redirect('training_app:manage_courses')
    else:
        form = CourseCreationForm()
    
    return render(request, 'training_app/admin/create_course.html', {
        'form': form,
        'title': 'Create New Course'
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def edit_course(request, course_id):
    """Edit an existing course."""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseCreationForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course "{course.name}" has been updated successfully.')
            return redirect('training_app:manage_courses')
    else:
        form = CourseCreationForm(instance=course)
    
    return render(request, 'training_app/admin/create_course.html', {
        'form': form,
        'title': f'Edit Course: {course.name}',
        'course': course
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def delete_course(request, course_id):
    """Delete a course."""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_name = course.name
        course.delete()
        messages.success(request, f'Course "{course_name}" has been deleted successfully.')
        return redirect('training_app:manage_courses')
    
    return render(request, 'training_app/admin/delete_course.html', {
        'course': course
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def create_test(request, course_id):
    """Create a new test."""
    if request.method == 'POST':
        form = TestCreationForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.course_id = course_id
            test.save()
            messages.success(request, f'Test "{test.title}" has been created successfully.')
            return redirect('training_app:manage_tests', course_id=course_id)
    else:
        form = TestCreationForm()
    
    return render(request, 'training_app/admin/create_test.html', {
        'form': form,
        'title': 'Create New Test',
        'course_id': course_id
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def edit_test(request, test_id):
    """Edit an existing test."""
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        form = TestCreationForm(request.POST, instance=test)
        if form.is_valid():
            test = form.save()
            messages.success(request, f'Test "{test.title}" has been updated successfully.')
            return redirect('training_app:manage_tests')
    else:
        form = TestCreationForm(instance=test)
    
    return render(request, 'training_app/admin/create_test.html', {
        'form': form,
        'title': f'Edit Test: {test.title}',
        'test': test
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def delete_test(request, test_id):
    """Delete a test."""
    test = get_object_or_404(Test, id=test_id)
    
    if request.method == 'POST':
        test_title = test.title
        test.delete()
        messages.success(request, f'Test "{test_title}" has been deleted successfully.')
        return redirect('training_app:manage_tests')
    
    return render(request, 'training_app/admin/delete_test.html', {
        'test': test
    })

@login_required
@user_passes_test(lambda u: u.user_type == 'admin')
def delete_question(request, course_id, test_id, question_id):
    """Delete a question from a test."""
    question = get_object_or_404(Question, id=question_id, test_id=test_id)
    
    if request.method == 'POST':
        question_text = question.question_text
        question.delete()
        messages.success(request, f'Question "{question_text[:50]}..." has been deleted successfully.')
    return redirect('training_app:manage_test_questions', course_id=course_id, test_id=test_id)

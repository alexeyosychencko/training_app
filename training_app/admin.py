from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Organization, Course, Test, Question, 
    Choice, TestAttempt, CourseProgress, TestUnlock, 
    InstructorAssignment
)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'organization')
    list_filter = ('user_type', 'organization', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone_number')}),
        ('Role & Organization', {'fields': ('user_type', 'organization')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type', 'organization'),
        }),
    )

    def log_deletion(self, request, object, object_repr):
        pass  # Override to skip logging

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'referral_code', 'created_at')
    search_fields = ('name', 'referral_code')
    ordering = ('name',)

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('name',)

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_type', 'course', 'duration_minutes', 'passing_score', 'is_active')
    list_filter = ('test_type', 'course', 'is_active')
    search_fields = ('title', 'description')
    inlines = [QuestionInline]
    ordering = ('title',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question_text', 'test', 'question_type', 'points')
    list_filter = ('question_type', 'test')
    search_fields = ('question_text',)
    inlines = [ChoiceInline]
    ordering = ('test', 'question_text')

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('choice_text', 'question', 'is_correct')
    list_filter = ('is_correct', 'question__test')
    search_fields = ('choice_text', 'question__question_text')
    ordering = ('question', 'choice_text')

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('cadet', 'test', 'started_at', 'completed_at', 'score', 'is_passed')
    list_filter = ('is_passed', 'test__test_type', 'test__course')
    search_fields = ('cadet__email', 'cadet__first_name', 'cadet__last_name', 'test__title')
    readonly_fields = ('started_at', 'completed_at')
    ordering = ('-started_at',)

@admin.register(CourseProgress)
class CourseProgressAdmin(admin.ModelAdmin):
    list_display = ('cadet', 'course', 'current_level', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'course')
    search_fields = ('cadet__email', 'cadet__first_name', 'cadet__last_name', 'course__name')
    readonly_fields = ('completed_at',)
    ordering = ('cadet', 'course')

@admin.register(TestUnlock)
class TestUnlockAdmin(admin.ModelAdmin):
    list_display = ('cadet', 'test', 'unlocked_at', 'is_unlocked')
    list_filter = ('is_unlocked', 'test__test_type', 'test__course')
    search_fields = ('cadet_emaile', 'cadet__first_name', 'cadet__last_name', 'test__title')
    readonly_fields = ('unlocked_at',)
    ordering = ('-unlocked_at',)

@admin.register(InstructorAssignment)
class InstructorAssignmentAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'cadet', 'course', 'assigned_at')
    list_filter = ('course', 'assigned_at')
    search_fields = (
        'instructor__email', 'instructor__first_name', 'instructor__last_name',
        'cadet__email', 'cadet__first_name', 'cadet__last_name',
        'course__name'
    )
    readonly_fields = ('assigned_at',)
    ordering = ('-assigned_at',)

# class NoLogUserAdmin(UserAdmin):
#     model = User
#     ordering = ['email']
#     list_display = ['email', 'is_staff', 'is_active']
    
#     fieldsets = (
#         (None, {'fields': ('email', 'password')}),
#         ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
#         ('Important dates', {'fields': ('last_login',)}),
#     )
    
#     add_fieldsets = (
#         (None, {
#             'classes': ('wide',),
#             'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
#         ),
#     )

#     def log_deletion(self, request, object, object_repr):
#         pass  # Override to skip logging

# Unregister the default User admin
admin.site.unregister(User)

# Register your custom User admin
admin.site.register(User, CustomUserAdmin)
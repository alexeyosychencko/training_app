from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class Organization(models.Model):
    name = models.CharField(max_length=200)
    referral_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.referral_code})"

class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, user_type, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, first_name=first_name, last_name=last_name, user_type=user_type, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, user_type, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        return self.create_user(email, first_name, last_name, user_type, password, **extra_fields)


class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('cadet', 'Cadet'),
        ('instructor', 'Instructor'),
        ('admin', 'Admin'),
    )
    
    # Override default fields
    first_name = models.CharField(max_length=150, blank=False)
    last_name = models.CharField(max_length=150, blank=False)
    email = models.EmailField(unique=True, blank=False)

    # Remove username field override; use email as the identifier
    username = None
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='cadet')
    organization = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    # Resolve reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='training_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='training_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    objects = UserManager()

    # Set email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'user_type']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name

class Course(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Test(models.Model):
    TEST_TYPE_CHOICES = (
        ('entrance', 'Entrance Exam'),
        ('midterm', 'Midterm Exam'),
        ('exit', 'Exit Exam'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    test_type = models.CharField(max_length=10, choices=TEST_TYPE_CHOICES)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name='tests')
    duration_minutes = models.IntegerField()
    passing_score = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_attempts = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_test_type_display()})"

class Question(models.Model):
    QUESTION_TYPE_CHOICES = (
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
    )
    
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='questions', null=True)
    question_text = models.TextField()
    question_type = models.CharField(max_length=15, choices=QUESTION_TYPE_CHOICES, default='multiple_choice')
    points = models.IntegerField(default=1)
    
    def __str__(self):
        return f"{self.question_text[:50]}..."

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    choice_text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return self.choice_text

class TestAttempt(models.Model):
    cadet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_attempts')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.cadet.username} - {self.test.title}"

class CourseProgress(models.Model):
    cadet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_progress')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    current_level = models.IntegerField(default=1)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['cadet', 'course']
    
    def __str__(self):
        return f"{self.cadet.username} - {self.course.name}"

class TestUnlock(models.Model):
    cadet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='test_unlocks')
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    is_unlocked = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['cadet', 'test']
    
    def __str__(self):
        return f"{self.cadet.username} - {self.test.title}"

class InstructorAssignment(models.Model):
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_cadets')
    cadet = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_instructors')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['instructor', 'cadet', 'course']
    
    def __str__(self):
        return f"{self.instructor.username} -> {self.cadet.username} ({self.course.name})"
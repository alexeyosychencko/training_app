from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import inlineformset_factory
from .models import User, Course, Test, Question, Choice, TestAttempt

class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'organization', 'phone_number', 'password1', 'password2')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already registered. Please use another one.')
        return email

class CourseCreationForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('name', 'description', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TestCreationForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'description', 'test_type', 'course', 'duration_minutes', 'passing_score', 'max_attempts']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'duration_minutes': forms.NumberInput(attrs={'min': 1}),
            'passing_score': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'max_attempts': forms.NumberInput(attrs={'min': 1}),
        }
        help_texts = {
            'duration_minutes': 'Duration of the test in minutes',
            'passing_score': 'Minimum score required to pass (0-100)',
            'max_attempts': 'Maximum number of attempts allowed',
        }

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question_text', 'question_type', 'points')
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'points': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ('choice_text', 'is_correct')
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control'}),
            'is_correct': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class TestSubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.test = kwargs.pop('test', None)
        super().__init__(*args, **kwargs)
        
        if self.test:
            for question in self.test.questions.all():
                if question.question_type == 'multiple_choice':
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        choices=[(choice.id, choice.choice_text) for choice in question.choices.all()],
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )
                elif question.question_type == 'true_false':
                    self.fields[f'question_{question.id}'] = forms.ChoiceField(
                        choices=[('true', 'True'), ('false', 'False')],
                        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
                    )
                else:
                    self.fields[f'question_{question.id}'] = forms.CharField(
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )

    def calculate_score(self):
        if not self.test:
            return 0
        
        total_points = 0
        earned_points = 0
        
        for question in self.test.questions.all():
            total_points += question.points
            answer = self.cleaned_data.get(f'question_{question.id}')
            
            if question.question_type == 'multiple_choice':
                choice = question.choices.get(id=answer)
                if choice.is_correct:
                    earned_points += question.points
            elif question.question_type == 'true_false':
                correct_answer = question.choices.first().is_correct
                if (answer == 'true' and correct_answer) or (answer == 'false' and not correct_answer):
                    earned_points += question.points
            else:
                # For short answer, we'll need to implement custom validation
                # This is a placeholder for future implementation
                earned_points += question.points
        
        return int((earned_points / total_points) * 100) if total_points > 0 else 0

# Formset for managing choices for a question
ChoiceFormSet = inlineformset_factory(
    Question,
    Choice,
    form=ChoiceForm,
    extra=4,
    can_delete=True,
    min_num=2,
    validate_min=True
) 
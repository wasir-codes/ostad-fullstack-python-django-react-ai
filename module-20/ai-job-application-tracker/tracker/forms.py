from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import JobApplication, Interview, Category, Tag


class RegisterForm(UserCreationForm):
    # UserCreationForm already gives us username + password1 + password2,
    # just adding email on top since the default one doesn't ask for it
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # loop over every field instead of setting the bootstrap class on
        # each one by hand - saves repeating the same widget attrs 4 times
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-control'})


class JobApplicationForm(forms.ModelForm):
    # tags is a ManyToMany field - CheckboxSelectMultiple felt more obvious
    # for a student form than the default multi-select box
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = JobApplication
        # excluding user on purpose - that gets set in the view from
        # request.user, never from a form field a user could tamper with
        fields = [
            'job_title', 'company_name', 'job_description', 'location',
            'salary', 'job_url', 'application_date', 'status', 'notes',
            'category', 'tags',
        ]
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'job_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 60k-80k BDT'}),
            # using TextInput instead of URLInput on purpose - a browser's
            # built-in type="url" input refuses to submit a bare domain like
            # "www.example.com" (it demands a scheme, http:// or https://,
            # before you even hit submit). Django's URLField is more lenient
            # server-side and auto-adds http:// if it's missing, so plain
            # text here + real validation in the model field is the actual
            # fix, not a workaround.
            'job_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. www.company.com/careers/123'}),
            'application_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }


class InterviewForm(forms.ModelForm):
    class Meta:
        model = Interview
        # application isn't here either - it comes from the URL (which
        # application's "add interview" page we're on), set in the view
        fields = ['interview_datetime', 'interview_type', 'meeting_link', 'notes']
        widgets = {
            'interview_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'interview_type': forms.Select(attrs={'class': 'form-select'}),
            # same reasoning as job_url above - TextInput, not URLInput, so a
            # bare domain/link doesn't get blocked by the browser before the
            # form even submits
            'meeting_link': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. meet.google.com/abc-defg-hij'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CategoryForm(forms.ModelForm):
    # tiny form, just used on a "quick add category" popup-style page
    class Meta:
        model = Category
        fields = ['name']
        widgets = {'name': forms.TextInput(attrs={'class': 'form-control'})}

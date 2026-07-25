from django import forms

from .models import JobApplication


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'company_name', 'position', 'job_location', 'salary',
            'status', 'application_date', 'deadline', 'notes',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Google'}),
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Junior Django Developer'}),
            'job_location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dhaka, Remote'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'application_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Maximum 500 characters'}),
        }
        labels = {
            'company_name': 'Company Name',
            'job_location': 'Job Location',
            'salary': 'Salary (optional)',
            'application_date': 'Application Date',
        }
        error_messages = {
            'company_name': {'required': 'Company name is required.'},
            'position': {'required': 'Position is required.'},
            'notes': {'max_length': 'Notes cannot exceed 500 characters.'},
        }

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 0:
            raise forms.ValidationError('Salary cannot be negative.')
        return salary

    def clean_notes(self):
        notes = self.cleaned_data.get('notes', '')
        if len(notes) > 500:
            raise forms.ValidationError('Notes cannot exceed 500 characters.')
        return notes

    # clean() is used here because this check needs two fields together
    def clean(self):
        cleaned_data = super().clean()
        application_date = cleaned_data.get('application_date')
        deadline = cleaned_data.get('deadline')

        if application_date and deadline and deadline < application_date:
            self.add_error('deadline', 'Deadline cannot be earlier than the application date.')

        return cleaned_data

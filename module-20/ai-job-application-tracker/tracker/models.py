from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    """
    A broad bucket for a job, e.g. "Backend", "Frontend", "Data".
    Kept as its own model (not just a text field) so it can be reused
    across many applications and filtered on in the search view.
    """
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        # otherwise the admin list shows them in whatever order they were created
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Tag(models.Model):
    """
    Freeform labels like "Remote", "Startup", "Django". Separate from
    Category because a job can have several tags but usually only fits
    one category - that's a many-to-many relationship, not a foreign key.
    """
    name = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name


class JobApplication(models.Model):
    """
    The main thing this whole app is about. One row = one job someone applied
    (or is planning to apply) to.
    """

    # status choices - written as a list of tuples like Django docs show.
    # the order here matters for display purposes only, the actual "sequence"
    # from the assignment (Wishlist -> Applied -> ... ) isn't enforced by the
    # database, it's just what the dropdown shows in that order.
    WISHLIST = 'WISHLIST'
    APPLIED = 'APPLIED'
    SCREENING = 'SCREENING'
    INTERVIEW = 'INTERVIEW'
    SELECTED = 'SELECTED'
    REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (WISHLIST, 'Wishlist'),
        (APPLIED, 'Applied'),
        (SCREENING, 'Screening'),
        (INTERVIEW, 'Interview'),
        (SELECTED, 'Selected'),
        (REJECTED, 'Rejected'),
    ]

    # every application belongs to exactly one user, and a user can have many
    # applications - that's a ForeignKey (many-to-one), not OneToOne.
    # related_name lets us do user.applications.all() instead of the clunkier
    # default jobapplication_set.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')

    job_title = models.CharField(max_length=150)
    company_name = models.CharField(max_length=150)
    job_description = models.TextField(blank=True, help_text='Paste the full job description here - needed for the AI analyzer.')
    location = models.CharField(max_length=100, blank=True)

    # salary as free text (e.g. "80k-100k BDT", "Negotiable") instead of a
    # number, since job postings almost never give a clean single figure
    salary = models.CharField(max_length=100, blank=True)

    job_url = models.URLField(blank=True)
    application_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=WISHLIST)
    notes = models.TextField(blank=True)

    # category is one-per-job (ForeignKey), tags are many-per-job (ManyToMany)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications')
    tags = models.ManyToManyField(Tag, blank=True, related_name='applications')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # most recently created application shows up first by default
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.job_title} at {self.company_name}'


class Interview(models.Model):
    """
    An interview tied to one job application. One application can have
    several interviews (phone screen, technical round, final round, etc.)
    so this is a ForeignKey, not OneToOne.
    """

    INTERVIEW_TYPES = [
        ('PHONE', 'Phone Screen'),
        ('VIDEO', 'Video Call'),
        ('ONSITE', 'Onsite'),
        ('TECHNICAL', 'Technical Round'),
        ('HR', 'HR Round'),
        ('OTHER', 'Other'),
    ]

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews')
    interview_datetime = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=INTERVIEW_TYPES, default='VIDEO')
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # soonest interview first - easier to see what's coming up next
        ordering = ['interview_datetime']

    def __str__(self):
        return f'{self.get_interview_type_display()} for {self.application.job_title} on {self.interview_datetime:%d %b %Y}'


class JobAnalysis(models.Model):
    """
    Stores the result of sending an application's job description to the AI
    API, so we don't have to call the API again every time the page is
    reloaded. One application can only have one saved analysis - if the user
    re-runs it, we just overwrite this (see the view).
    """
    application = models.OneToOneField(JobApplication, on_delete=models.CASCADE, related_name='analysis')

    summary = models.TextField(blank=True)
    required_skills = models.TextField(blank=True)
    required_experience = models.TextField(blank=True)
    important_technologies = models.TextField(blank=True)
    interview_prep = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'AI analysis for {self.application}'

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone

from .forms import RegisterForm, JobApplicationForm, InterviewForm
from .models import JobApplication, Interview, Category, JobAnalysis
from .ai_analyzer import analyze_job_description


# ---------- Auth ----------

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # log them straight in, no point making them log in twice
            messages.success(request, 'Account created! Start adding your job applications below.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()
    return render(request, 'tracker/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'tracker/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


# ---------- Dashboard ----------

@login_required
def dashboard(request):
    # everything below is scoped to request.user - this is the whole reason
    # each user only ever sees their own applications
    applications = JobApplication.objects.filter(user=request.user)

    total_applications = applications.count()

    # group by status and count, using the ORM instead of looping in python.
    # this gives back a list of dicts like [{'status': 'APPLIED', 'total': 3}, ...]
    by_status = applications.values('status').annotate(total=Count('id')).order_by('status')

    # turn the STATUS_CHOICES tuples into a dict so the template can show
    # "Applied" instead of the raw "APPLIED" code
    status_labels = dict(JobApplication.STATUS_CHOICES)
    status_counts = [
        {'label': status_labels.get(row['status'], row['status']), 'total': row['total']}
        for row in by_status
    ]

    recent_applications = applications[:5]  # already ordered newest-first via Meta.ordering

    # upcoming interviews = interviews on applications belonging to this user,
    # with a date/time still in the future. filtering through the FK with
    # application__user works because of the relationship we set up in models.py
    upcoming_interviews = Interview.objects.filter(
        application__user=request.user,
        interview_datetime__gte=timezone.now(),
    ).order_by('interview_datetime')[:5]

    context = {
        'total_applications': total_applications,
        'status_counts': status_counts,
        'recent_applications': recent_applications,
        'upcoming_interviews': upcoming_interviews,
    }
    return render(request, 'tracker/dashboard.html', context)


# ---------- Job Application CRUD ----------

@login_required
def application_list(request):
    # start from only this user's applications - never show anyone else's
    applications = JobApplication.objects.filter(user=request.user)

    # --- search by job title or company ---
    query = request.GET.get('q', '').strip()
    if query:
        # Q lets us OR two conditions together in one query instead of
        # running two separate lookups and combining them in python
        applications = applications.filter(
            Q(job_title__icontains=query) | Q(company_name__icontains=query)
        )

    # --- filter by status ---
    status = request.GET.get('status', '')
    if status:
        applications = applications.filter(status=status)

    # --- filter by location ---
    location = request.GET.get('location', '')
    if location:
        applications = applications.filter(location__icontains=location)

    # --- filter by category ---
    category_id = request.GET.get('category', '')
    if category_id:
        applications = applications.filter(category_id=category_id)

    context = {
        'applications': applications,
        'query': query,
        'status': status,
        'location': location,
        'category_id': category_id,
        'status_choices': JobApplication.STATUS_CHOICES,
        'categories': Category.objects.all(),
    }
    return render(request, 'tracker/application_list.html', context)


@login_required
def application_detail(request, pk):
    # get_object_or_404 with user=request.user in the same lookup means a
    # user can never view someone else's application, not even by guessing
    # the URL /applications/7/ - it just 404s instead of leaking data
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    return render(request, 'tracker/application_detail.html', {'application': application})


@login_required
def application_create(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)  # don't hit the DB yet, need to set user first
            application.user = request.user
            application.save()
            form.save_m2m()  # ModelForm needs this explicitly when commit=False and there's a M2M field (tags)
            messages.success(request, 'Application added.')
            return redirect('application_detail', pk=application.pk)
    else:
        form = JobApplicationForm()
    return render(request, 'tracker/application_form.html', {'form': form, 'is_edit': False})


@login_required
def application_edit(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated.')
            return redirect('application_detail', pk=application.pk)
    else:
        form = JobApplicationForm(instance=application)
    return render(request, 'tracker/application_form.html', {'form': form, 'is_edit': True, 'application': application})


@login_required
def application_delete(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Application deleted.')
        return redirect('application_list')
    # GET just shows a confirm page - don't delete on a GET request
    return render(request, 'tracker/application_confirm_delete.html', {'application': application})


# ---------- Interviews ----------

@login_required
def interview_create(request, application_pk):
    application = get_object_or_404(JobApplication, pk=application_pk, user=request.user)
    if request.method == 'POST':
        form = InterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.application = application  # comes from the URL, not the form
            interview.save()
            messages.success(request, 'Interview added.')
            return redirect('application_detail', pk=application.pk)
    else:
        form = InterviewForm()
    return render(request, 'tracker/interview_form.html', {'form': form, 'application': application})


# ---------- AI Job Description Analyzer ----------

@login_required
def analyze_job(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)

    if request.method == 'POST':
        if not application.job_description.strip():
            messages.error(request, 'Add a job description to this application before analyzing it.')
            return redirect('application_detail', pk=application.pk)

        result, error = analyze_job_description(application.job_description)

        if error:
            messages.error(request, f'AI analysis failed: {error}')
            return redirect('application_detail', pk=application.pk)

        # update_or_create so re-running the analysis overwrites the old one
        # instead of creating a second row (application has OneToOneField -> analysis)
        JobAnalysis.objects.update_or_create(
            application=application,
            defaults={
                'summary': result['summary'],
                'required_skills': result['required_skills'],
                'required_experience': result['required_experience'],
                'important_technologies': result['important_technologies'],
                'interview_prep': result['interview_prep'],
            },
        )
        messages.success(request, 'Job description analyzed.')
        # send them to the dedicated analysis page, not back to the detail
        # page - the assignment lists "AI Analysis" as its own page
        return redirect('analysis_detail', pk=application.pk)

    return render(request, 'tracker/analyze_confirm.html', {'application': application})


@login_required
def analysis_detail(request, pk):
    # the dedicated "AI Analysis" page - shows the saved result (if any) and
    # a button to run/re-run it. Kept separate from application_detail so
    # there's one clear page to point at for this feature.
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    return render(request, 'tracker/analysis_detail.html', {'application': application})

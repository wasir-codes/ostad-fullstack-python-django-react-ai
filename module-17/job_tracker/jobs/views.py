from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import JobApplicationForm
from .models import JobApplication


def home(request):
    applications = JobApplication.objects.all()

    context = {
        'total': applications.count(),
        'applied': applications.filter(status='applied').count(),
        'interview': applications.filter(status='interview').count(),
        'offer': applications.filter(status='offer').count(),
        'accepted': applications.filter(status='accepted').count(),
        'rejected': applications.filter(status='rejected').count(),
        'recent': applications[:5],
    }
    return render(request, 'home.html', context)


def job_list(request):
    applications = JobApplication.objects.all()
    return render(request, 'jobs/list.html', {'applications': applications})


def job_detail(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)
    return render(request, 'jobs/detail.html', {'application': application})


def job_create(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application added successfully.')
            return redirect('jobs:job_list')
    else:
        form = JobApplicationForm()

    return render(request, 'jobs/create.html', {'form': form})


def job_update(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)

    if request.method == 'POST':
        # instance tells the form to update this row instead of creating a new one
        form = JobApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated successfully.')
            return redirect('jobs:job_list')
    else:
        form = JobApplicationForm(instance=application)

    return render(request, 'jobs/update.html', {'form': form, 'application': application})


def job_delete(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)

    # GET shows the confirmation page, POST actually deletes
    if request.method == 'POST':
        application.delete()
        messages.success(request, 'Application deleted successfully.')
        return redirect('jobs:job_list')

    return render(request, 'jobs/delete.html', {'application': application})

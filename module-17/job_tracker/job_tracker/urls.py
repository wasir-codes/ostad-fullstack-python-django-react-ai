from django.contrib import admin
from django.urls import include, path

from jobs import views as job_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', job_views.home, name='home'),        # /
    path('jobs/', include('jobs.urls')),          # /jobs/... (see jobs/urls.py)
]

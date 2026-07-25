from django.urls import path

from . import views

# app_name gives us the "jobs:" prefix used in {% url 'jobs:job_list' %}
app_name = 'jobs'

urlpatterns = [
    path('', views.job_list, name='job_list'),               # /jobs/
    path('add/', views.job_create, name='job_create'),       # /jobs/add/
    path('<int:pk>/', views.job_detail, name='job_detail'),  # /jobs/1/
    path('<int:pk>/edit/', views.job_update, name='job_update'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
]

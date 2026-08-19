from django.urls import path
from . import views

urlpatterns = [
    # auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # dashboard
    path('', views.dashboard, name='dashboard'),

    # job application CRUD
    path('applications/', views.application_list, name='application_list'),
    path('applications/new/', views.application_create, name='application_create'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
    path('applications/<int:pk>/edit/', views.application_edit, name='application_edit'),
    path('applications/<int:pk>/delete/', views.application_delete, name='application_delete'),

    # interviews (tied to an application)
    path('applications/<int:application_pk>/interviews/new/', views.interview_create, name='interview_create'),

    # AI analyzer - one page to trigger it, one page to view the result
    path('applications/<int:pk>/analyze/', views.analyze_job, name='analyze_job'),
    path('applications/<int:pk>/analysis/', views.analysis_detail, name='analysis_detail'),
]

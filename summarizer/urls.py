from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('summarize/', views.summarize, name='summarize'),
    path('about/', views.about, name='about'),
    
    # Summary management
    path('summaries/', views.summary_list, name='summary-list'),
    path('summaries/<int:pk>/', views.summary_detail, name='summary-detail'),
    path('summaries/<int:pk>/feedback/', views.summary_feedback, name='summary-feedback'),
    path('summaries/<int:pk>/delete/', views.summary_delete, name='summary-delete'),
    path('summaries/<int:pk>/regenerate/', views.summary_regenerate, name='summary-regenerate'),
    path('summaries/<int:pk>/download/', views.summary_download, name='summary-download'),
    
    # Example sets
    path('examples/', views.example_list, name='example-list'),
    path('examples/create/', views.example_set_create, name='example-set-create'),
    path('examples/<int:pk>/', views.example_set_detail, name='example-set-detail'),
    path('examples/<int:pk>/add/', views.example_add, name='example-add'),
    path('examples/<int:pk>/delete/', views.example_set_delete, name='example-set-delete'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('reports/errors/', views.error_report, name='error-report'),
    path('reports/accuracy/', views.accuracy_report, name='accuracy-report'),
    
    # API endpoints for AJAX operations
    path('api/summary-status/<int:pk>/', views.summary_status, name='summary-status'),
]
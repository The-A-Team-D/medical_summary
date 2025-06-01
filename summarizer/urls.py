from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Home and About
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Summary URLs
    path('summarize/', views.summarize, name='summarize'),
    path('summaries/', views.summary_list, name='summary-list'),
    path('summaries/<int:pk>/', views.summary_detail, name='summary-detail'),
    path('summaries/<int:pk>/status/', views.summary_status, name='summary-status'),
    path('summaries/<int:pk>/feedback/', views.summary_feedback, name='summary-feedback'),
    path('summaries/<int:pk>/delete/', views.summary_delete, name='summary-delete'),
    path('summaries/<int:pk>/regenerate/', views.summary_regenerate, name='summary-regenerate'),
    path('summaries/<int:pk>/download/', views.summary_download, name='summary-download'),
    
    # Example Set URLs
    path('examples/', views.example_list, name='example-list'),
    path('examples/create/', views.example_set_create, name='example-set-create'),
    path('examples/<int:pk>/', views.example_set_detail, name='example-set-detail'),
    path('examples/<int:pk>/add/', views.example_add, name='example-add'),
    path('examples/<int:pk>/delete/', views.example_set_delete, name='example-set-delete'),
    
    # Reports URLs
    path('reports/', views.reports, name='reports'),
    path('reports/errors/', views.error_report, name='error-report'),
    path('reports/accuracy/', views.accuracy_report, name='accuracy-report'),
    
    # Batch operations
    path('batch-download/<str:batch_id>/', views.batch_download, name='batch-download'),

    # Authentication URLs - UPDATED
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', views.logout_view, name='logout'),  # NEW: Custom logout view
    path('register/', views.register, name='register'),  # NEW: User registration
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


















# from django.contrib import admin
# from django.urls import path, include
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib.auth import views as auth_views
# from . import views

# urlpatterns = [
#     path('', views.home, name='home'),
#     path('about/', views.about, name='about'),
#     path('summarize/', views.summarize, name='summarize'),
#     path('summaries/', views.summary_list, name='summary-list'),
#     path('summaries/<int:pk>/', views.summary_detail, name='summary-detail'),
#     path('summaries/<int:pk>/status/', views.summary_status, name='summary-status'),
#     path('summaries/<int:pk>/feedback/', views.summary_feedback, name='summary-feedback'),
#     path('summaries/<int:pk>/delete/', views.summary_delete, name='summary-delete'),
#     path('summaries/<int:pk>/regenerate/', views.summary_regenerate, name='summary-regenerate'),
#     path('summaries/<int:pk>/download/', views.summary_download, name='summary-download'),
#     path('examples/', views.example_list, name='example-list'),
#     path('examples/create/', views.example_set_create, name='example-set-create'),
#     path('examples/<int:pk>/', views.example_set_detail, name='example-set-detail'),
#     path('examples/<int:pk>/add/', views.example_add, name='example-add'),
#     path('examples/<int:pk>/delete/', views.example_set_delete, name='example-set-delete'),
#     path('reports/', views.reports, name='reports'),
#     path('reports/errors/', views.error_report, name='error-report'),
#     path('reports/accuracy/', views.accuracy_report, name='accuracy-report'),
#     path('batch-download/<str:batch_id>/', views.batch_download, name='batch-download'),
    
    
#     # Authentication URLs
#     path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
#     path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
# ]

# # Serve media files in development
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
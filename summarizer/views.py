# import os
# from django.shortcuts import render, redirect, get_object_or_404
# from django.contrib import messages
# from django.conf import settings
# from django.http import HttpResponse, JsonResponse
# from django.utils.text import slugify
# from django.core.paginator import Paginator
# from django.urls import reverse
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth.decorators import login_required
# from .models import Summary, ExampleSet, DocumentExample, ErrorPattern
# from .forms import UploadPDFForm, SummaryFeedbackForm, ExampleSetForm
# from .summarizer_engine.medical_summarizer import MedicalSummarizer
# from .summarizer_engine.summary_accuracy_tracker import SummaryAccuracyTracker
# import threading
# import uuid
# import json
# from django.db import models

# # Global dictionary to store the examples for each project type
# PROJECT_EXAMPLES = {
#     'ah': [],
#     'tlc': [],
#     'sa': [],
#     'lw': [],
# }

# def load_example_data():
#     """Load example data for each project type from the database"""
#     for project_type in PROJECT_EXAMPLES.keys():
#         example_sets = ExampleSet.objects.filter(project_type=project_type)
#         for example_set in example_sets:
#             examples = example_set.examples.all()
#             for example in examples:
#                 PROJECT_EXAMPLES[project_type].append({
#                     'pdf': example.pdf_file.path,
#                     'summary': example.summary_file.path
#                 })

# # Load example data when the server starts
# load_example_data()

# # Home view
# def home(request):
#     """Home page with statistics and quick links"""
#     # Get summarization statistics
#     total_summaries = Summary.objects.count()
#     completed_summaries = Summary.objects.filter(status='completed').count()
#     corrected_summaries = Summary.objects.filter(status='corrected').count()
    
#     # Get recent summaries
#     recent_summaries = Summary.objects.order_by('-created_at')[:5]
    
#     # Get examples by project type
#     ah_examples = len(PROJECT_EXAMPLES['ah'])
#     tlc_examples = len(PROJECT_EXAMPLES['tlc'])
#     sa_examples = len(PROJECT_EXAMPLES['sa'])
#     lw_examples = len(PROJECT_EXAMPLES['lw'])
    
#     context = {
#         'total_summaries': total_summaries,
#         'completed_summaries': completed_summaries,
#         'corrected_summaries': corrected_summaries,
#         'recent_summaries': recent_summaries,
#         'ah_examples': ah_examples,
#         'tlc_examples': tlc_examples,
#         'sa_examples': sa_examples,
#         'lw_examples': lw_examples,
#     }
#     return render(request, 'home.html', context)

# # About page
# def about(request):
#     """About page with information about the system"""
#     return render(request, 'about.html')

# # Summarization process function
# def process_summary(summary_id):
#     """Background process to generate a summary"""
#     # Get the summary object
#     summary = Summary.objects.get(id=summary_id)
#     summary.status = 'processing'
#     summary.save()
    
#     try:
#         # Configure the summarizer
#         config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
#         config['openai_api_key'] = settings.OPENAI_API_KEY
        
#         # Get examples for the project type
#         example_without_password = PROJECT_EXAMPLES.get(summary.project_type, [])
        
#         # Initialize the summarizer
#         summarizer = MedicalSummarizer(
#             config=config,
#             new_pdf=summary.pdf_file.path,
#             example_without_password=example_without_password
#         )
        
#         # Set new PDF password if provided
#         if summary.pdf_password:
#             config['new_pdf_password'] = summary.pdf_password
        
#         # Generate the summary
#         result, original_text = summarizer.summarize(
#             project_name=summary.project_type, 
#             output_file=f"{summary.document_name}.txt"
#         )
        
#         # Update the summary object
#         summary.summary_text = result
#         summary.original_text = original_text
#         summary.status = 'completed'
#         summary.save()
        
#     except Exception as e:
#         # Handle errors
#         summary.status = 'error'
#         summary.summary_text = f"Error generating summary: {str(e)}"
#         summary.save()

# # Summarize view
# def summarize(request):
#     """View for uploading a PDF to summarize"""
#     if request.method == 'POST':
#         form = UploadPDFForm(request.POST, request.FILES)
#         if form.is_valid():
#             # Create a new summary object
#             summary = form.save(commit=False)
            
#             # Set document name based on file name
#             file_name = os.path.basename(request.FILES['pdf_file'].name)
#             summary.document_name = os.path.splitext(file_name)[0]
            
#             # Save the summary
#             summary.save()
            
#             # Start the summarization process in a background thread
#             summary_thread = threading.Thread(
#                 target=process_summary, 
#                 args=(summary.id,)
#             )
#             summary_thread.daemon = True
#             summary_thread.start()
            
#             # Redirect to the summary detail page
#             messages.success(request, "Your PDF has been submitted for summarization.")
#             return redirect('summary-detail', pk=summary.id)
#     else:
#         form = UploadPDFForm()
    
#     return render(request, 'summarize.html', {'form': form})

# # Summary status view (for AJAX calls)
# @csrf_exempt
# def summary_status(request, pk):
#     """AJAX endpoint to check the status of a summary"""
#     summary = get_object_or_404(Summary, pk=pk)
#     data = {
#         'status': summary.status,
#         'summary_text': summary.summary_text if summary.status == 'completed' else '',
#         'document_name': summary.document_name,
#     }
#     return JsonResponse(data)

# # Summary list view
# def summary_list(request):
#     """View to display all summaries with filtering and pagination"""
#     summaries_list = Summary.objects.all().order_by('-created_at')
    
#     # Filter by project type if provided
#     project_type = request.GET.get('project_type')
#     if project_type:
#         summaries_list = summaries_list.filter(project_type=project_type)
    
#     # Filter by status if provided
#     status = request.GET.get('status')
#     if status:
#         summaries_list = summaries_list.filter(status=status)
    
#     # Search by document name if provided
#     search = request.GET.get('search')
#     if search:
#         summaries_list = summaries_list.filter(document_name__icontains=search)
    
#     # Pagination
#     paginator = Paginator(summaries_list, 10)
#     page = request.GET.get('page')
#     summaries = paginator.get_page(page)
    
#     context = {
#         'summaries': summaries,
#         'project_types': [('ah', 'AH PLLC'), ('tlc', 'TLC S PLLC'), ('sa', 'SA PLLC'), ('lw', 'LW PLLC')],
#         'statuses': [('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), 
#                     ('corrected', 'Corrected'), ('error', 'Error')],
#         'selected_project_type': project_type,
#         'selected_status': status,
#         'search_query': search,
#     }
    
#     return render(request, 'summaries.html', context)

# # Summary detail view
# def summary_detail(request, pk):
#     """View to display a summary's details"""
#     summary = get_object_or_404(Summary, pk=pk)
#     context = {
#         'summary': summary,
#     }
#     return render(request, 'summary_detail.html', context)

# # Summary feedback view
# def summary_feedback(request, pk):
#     """View to provide feedback on a summary"""
#     summary = get_object_or_404(Summary, pk=pk)
    
#     if request.method == 'POST':
#         form = SummaryFeedbackForm(request.POST, instance=summary)
#         if form.is_valid():
#             # Save the corrected text
#             corrected_summary = form.save(commit=False)
#             corrected_summary.status = 'corrected'
#             corrected_summary.save()
            
#             # Process the correction
#             config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
#             config['openai_api_key'] = settings.OPENAI_API_KEY
            
#             # Initialize the summarizer
#             summarizer = MedicalSummarizer(
#                 config=config,
#                 new_pdf=summary.pdf_file.path
#             )
            
#             # Process the correction
#             error_report = summarizer.process_human_correction(
#                 f"{summary.document_name}.txt",
#                 corrected_summary.corrected_text
#             )
            
#             # Calculate accuracy metrics
#             accuracy_tracker = SummaryAccuracyTracker()
#             metrics = accuracy_tracker.calculate_metrics(
#                 summary.summary_text,
#                 corrected_summary.corrected_text
#             )
            
#             # Save accuracy score
#             corrected_summary.accuracy_score = metrics['overall_score']
#             corrected_summary.save()
            
#             # Create error patterns
#             # Extract error patterns and save them
#             try:
#                 error_data = json.loads(error_report)
#                 for error in error_data.get('section_errors', []):
#                     ErrorPattern.objects.create(
#                         error_type=error['type'],
#                         section=error['section'],
#                         summary=summary
#                     )
                
#                 for error in error_data.get('content_errors', []):
#                     ErrorPattern.objects.create(
#                         error_type=error['error_type'],
#                         section=error['section'],
#                         original_text=error.get('original', ''),
#                         corrected_text=error.get('correction', ''),
#                         summary=summary
#                     )
#             except:
#                 # If error report is not JSON, just continue
#                 pass
            
#             messages.success(request, "Thank you for your feedback! It will be used to improve future summaries.")
#             return redirect('summary-detail', pk=summary.id)
#     else:
#         form = SummaryFeedbackForm(instance=summary)
#         if not summary.corrected_text:
#             # Pre-fill with the generated summary text
#             form.initial['corrected_text'] = summary.summary_text
    
#     context = {
#         'summary': summary,
#         'form': form,
#     }
#     return render(request, 'summary_feedback.html', context)

# # Delete summary view
# def summary_delete(request, pk):
#     """View to delete a summary"""
#     summary = get_object_or_404(Summary, pk=pk)
    
#     if request.method == 'POST':
#         summary.delete()
#         messages.success(request, "Summary deleted successfully.")
#         return redirect('summary-list')
    
#     context = {
#         'summary': summary,
#     }
#     return render(request, 'summary_delete.html', context)

# # Regenerate summary view
# def summary_regenerate(request, pk):
#     """View to regenerate a summary"""
#     summary = get_object_or_404(Summary, pk=pk)
    
#     if request.method == 'POST':
#         # Reset the summary status
#         summary.status = 'pending'
#         summary.summary_text = ''
#         summary.save()
        
#         # Start the summarization process in a background thread
#         summary_thread = threading.Thread(
#             target=process_summary, 
#             args=(summary.id,)
#         )
#         summary_thread.daemon = True
#         summary_thread.start()
        
#         messages.success(request, "Your summary is being regenerated.")
#         return redirect('summary-detail', pk=summary.id)
    
#     context = {
#         'summary': summary,
#     }
#     return render(request, 'summary_regenerate.html', context)

# # Download summary view
# def summary_download(request, pk):
#     """View to download a summary as a text file"""
#     summary = get_object_or_404(Summary, pk=pk)
    
#     # Create the response with the summary text
#     response = HttpResponse(summary.summary_text, content_type='text/plain')
#     filename = f"{slugify(summary.document_name)}_summary.txt"
#     response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
#     return response

# # Example list view
# def example_list(request):
#     """View to display all example sets"""
#     example_sets = ExampleSet.objects.all().order_by('-created_at')
    
#     context = {
#         'example_sets': example_sets,
#     }
#     return render(request, 'example_list.html', context)

# # Example set create view
# def example_set_create(request):
#     """View to create a new example set"""
#     if request.method == 'POST':
#         form = ExampleSetForm(request.POST)
#         if form.is_valid():
#             example_set = form.save()
#             messages.success(request, "Example set created successfully.")
#             return redirect('example-set-detail', pk=example_set.id)
#     else:
#         form = ExampleSetForm()
    
#     context = {
#         'form': form,
#     }
#     return render(request, 'example_set_create.html', context)

# # Example set detail view
# def example_set_detail(request, pk):
#     """View to display an example set's details"""
#     example_set = get_object_or_404(ExampleSet, pk=pk)
#     examples = example_set.examples.all().order_by('-uploaded_at')
    
#     context = {
#         'example_set': example_set,
#         'examples': examples,
#     }
#     return render(request, 'example_set_detail.html', context)

# # Add example to set view
# def example_add(request, pk):
#     """View to add an example to an example set"""
#     example_set = get_object_or_404(ExampleSet, pk=pk)
    
#     if request.method == 'POST':
#         pdf_file = request.FILES.get('pdf_file')
#         summary_file = request.FILES.get('summary_file')
        
#         if pdf_file and summary_file:
#             # Create a new example
#             example = DocumentExample(
#                 name=os.path.splitext(pdf_file.name)[0],
#                 example_set=example_set,
#                 pdf_file=pdf_file,
#                 summary_file=summary_file
#             )
#             example.save()
            
#             # Update the PROJECT_EXAMPLES dictionary
#             PROJECT_EXAMPLES[example_set.project_type].append({
#                 'pdf': example.pdf_file.path,
#                 'summary': example.summary_file.path
#             })
            
#             messages.success(request, f"Example '{example.name}' added successfully.")
#         else:
#             messages.error(request, "Please provide both a PDF file and a summary file.")
        
#         return redirect('example-set-detail', pk=example_set.id)
    
#     context = {
#         'example_set': example_set,
#     }
#     return render(request, 'example_add.html', context)

# # Delete example set view
# def example_set_delete(request, pk):
#     """View to delete an example set"""
#     example_set = get_object_or_404(ExampleSet, pk=pk)
    
#     if request.method == 'POST':
#         # Get the project type before deleting
#         project_type = example_set.project_type
        
#         # Delete the example set
#         example_set.delete()
        
#         # Update the PROJECT_EXAMPLES dictionary
#         load_example_data()  # Reload the examples
        
#         messages.success(request, "Example set deleted successfully.")
#         return redirect('example-list')
    
#     context = {
#         'example_set': example_set,
#     }
#     return render(request, 'example_set_delete.html', context)

# # Reports view
# def reports(request):
#     """View to display available reports"""
#     # Get basic stats
#     total_summaries = Summary.objects.count()
#     completed_summaries = Summary.objects.filter(status='completed').count()
#     corrected_summaries = Summary.objects.filter(status='corrected').count()
    
#     # Get accuracy statistics
#     summaries_with_accuracy = Summary.objects.filter(accuracy_score__isnull=False)
#     avg_accuracy = summaries_with_accuracy.values_list('accuracy_score', flat=True).aggregate(
#         avg=models.Avg('accuracy_score')
#     )
    
    
#     context = {
#         'total_summaries': total_summaries,
#         'completed_summaries': completed_summaries,
#         'corrected_summaries': corrected_summaries,
#         'summaries_with_accuracy': summaries_with_accuracy.count(),
#         'avg_accuracy': avg_accuracy['avg'] if avg_accuracy['avg'] else 0,
#     }
#     return render(request, 'reports.html', context)

# # Error report view
# def error_report(request):
#     """View to display the error analysis report"""
#     # Get the error patterns
#     errors = ErrorPattern.objects.all()
    
#     # Count by error type
#     error_types = errors.values('error_type').annotate(count=models.Count('id'))
    
#     # Count by section
#     error_sections = errors.values('section').annotate(count=models.Count('id'))
    
#     # Generate the report
#     config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
#     config['openai_api_key'] = settings.OPENAI_API_KEY
    
#     # Initialize the summarizer
#     summarizer = MedicalSummarizer(
#         config=config,
#         new_pdf=None
#     )
    
#     # Generate the error analysis report
#     error_report = summarizer.generate_error_analysis_report()
    
#     context = {
#         'error_types': error_types,
#         'error_sections': error_sections,
#         'error_report': error_report,
#     }
#     return render(request, 'error_report.html', context)

# # Accuracy report view
# def accuracy_report(request):
#     """View to display the accuracy trend report"""
#     # Get summaries with accuracy scores
#     summaries_with_accuracy = Summary.objects.filter(accuracy_score__isnull=False)
    
#     # Initialize the accuracy tracker
#     accuracy_tracker = SummaryAccuracyTracker()
    
#     # Generate trend report if there are enough data points
#     trend_report = "Not enough data to generate trends. Need at least 2 data points."
#     if summaries_with_accuracy.count() >= 2:
#         # Prepare data for the tracker
#         for summary in summaries_with_accuracy:
#             if summary.summary_text and summary.corrected_text:
#                 metrics = accuracy_tracker.calculate_metrics(
#                     summary.summary_text,
#                     summary.corrected_text
#                 )
#                 accuracy_tracker.add_metrics(
#                     summary.id,
#                     summary.summary_text,
#                     summary.corrected_text
#                 )
        
#         # Generate the report
#         trend_report = accuracy_tracker.generate_trend_report()
    
#     context = {
#         'summaries_with_accuracy': summaries_with_accuracy,
#         'trend_report': trend_report,
#     }
#     return render(request, 'accuracy_report.html', context)



import os
import io
import re
import uuid
import zipfile
import tempfile
from datetime import datetime
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.text import slugify
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import Summary, ExampleSet, DocumentExample, ErrorPattern
from .forms import UploadPDFForm, SummaryFeedbackForm, ExampleSetForm
from .tasks import process_summary, process_human_correction, load_example_data
from .summarizer_engine.summary_accuracy_tracker import SummaryAccuracyTracker
import json
from django.db import models
from django.contrib.auth import logout
from django.contrib.auth.models import User
from .forms import UploadPDFForm, SummaryFeedbackForm, ExampleSetForm, CustomUserCreationForm  

# Function to determine project type from filename
def determine_project_type(filename):
    """Determine project type based on filename"""
    filename = filename.lower()
    
    if 'ah' in filename:
        return 'ah'
    elif 'tlc' in filename:
        return 'tlc'
    elif 'sa' in filename:
        return 'sa'
    elif 'lw' in filename:
        return 'lw'
    else:
        # Default to 'ah' if no match
        return 'ah'

# Home view
@login_required
def home(request):
    """Home page with statistics and quick links"""
    # Get summarization statistics for the current user
    if request.user.is_superuser:
        user_summaries = Summary.objects.all()
    else:
        user_summaries = Summary.objects.filter(user=request.user)
        
    total_summaries = user_summaries.count()
    completed_summaries = user_summaries.filter(status='completed').count()
    corrected_summaries = user_summaries.filter(status='corrected').count()
    
    # Get recent summaries
    recent_summaries = user_summaries.order_by('-created_at')[:5]
    
    # Get examples by project type
    from .tasks import PROJECT_EXAMPLES
    ah_examples = len(PROJECT_EXAMPLES['ah'])
    tlc_examples = len(PROJECT_EXAMPLES['tlc'])
    sa_examples = len(PROJECT_EXAMPLES['sa'])
    lw_examples = len(PROJECT_EXAMPLES['lw'])
    
    context = {
        'total_summaries': total_summaries,
        'completed_summaries': completed_summaries,
        'corrected_summaries': corrected_summaries,
        'recent_summaries': recent_summaries,
        'ah_examples': ah_examples,
        'tlc_examples': tlc_examples,
        'sa_examples': sa_examples,
        'lw_examples': lw_examples,
    }
    return render(request, 'home.html', context)

# About page
def about(request):
    """About page with information about the system"""
    return render(request, 'about.html')

# Summarize view
@login_required
def summarize(request):
    """View for uploading PDFs to summarize"""
    if request.method == 'POST':
        # Handle multiple file uploads
        files = request.FILES.getlist('pdf_files')
        pdf_password = request.POST.get('pdf_password', '')
        
        if files:
            # Generate a batch ID for multiple files
            is_batch = len(files) > 1
            batch_id = uuid.uuid4() if is_batch else None
            batch_name = f"Batch Upload - {datetime.now().strftime('%Y-%m-%d %H:%M')}" if is_batch else None
            
            created_summaries = []
            
            for pdf_file in files:
                # Create a new summary object
                summary = Summary(
                    user=request.user,
                    pdf_file=pdf_file,
                    pdf_password=pdf_password if pdf_password else None,
                    batch_id=batch_id or uuid.uuid4(),  # Single files also get a batch_id
                    batch_name=batch_name,
                    is_batch=is_batch
                )
                
                # Set document name based on file name
                file_name = os.path.basename(pdf_file.name)
                summary.document_name = os.path.splitext(file_name)[0]
                
                # Determine project type from filename
                summary.project_type = determine_project_type(file_name)
                
                # Save the summary
                summary.save()
                created_summaries.append(summary)
                
                # Start the summarization process as a Celery task
                process_summary.delay(summary.id)
            
            # Show success message based on number of files
            if len(files) == 1:
                messages.success(request, "Your PDF has been submitted for summarization.")
            else:
                messages.success(request, f"{len(files)} PDFs have been submitted for summarization as a batch.")
            
            return redirect('summary-list')
        else:
            messages.error(request, "Please select at least one PDF file to upload.")
    
    return render(request, 'summarize.html')

# Summary status view (for AJAX calls)
@csrf_exempt
@login_required
def summary_status(request, pk):
    """AJAX endpoint to check the status of a summary"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to view this summary
    if not request.user.is_superuser and summary.user != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    data = {
        'status': summary.status,
        'summary_text': summary.summary_text if summary.status == 'completed' else '',
        'document_name': summary.document_name,
    }
    return JsonResponse(data)

# Summary list view
@login_required
def summary_list(request):
    """View to display all summaries with filtering, pagination, and batch grouping"""
    # Filter summaries based on user permissions
    if request.user.is_superuser:
        summaries_queryset = Summary.objects.all()
    else:
        summaries_queryset = Summary.objects.filter(user=request.user)
    
    # Apply filters
    project_type = request.GET.get('project_type')
    if project_type:
        summaries_queryset = summaries_queryset.filter(project_type=project_type)
    
    status = request.GET.get('status')
    if status:
        summaries_queryset = summaries_queryset.filter(status=status)
    
    search = request.GET.get('search')
    if search:
        summaries_queryset = summaries_queryset.filter(
            Q(document_name__icontains=search) | Q(batch_name__icontains=search)
        )
    
    user_id = request.GET.get('user_id')
    if user_id and request.user.is_superuser:
        summaries_queryset = summaries_queryset.filter(user_id=user_id)
    
    # Group summaries by batch_id
    batch_groups = {}
    single_summaries = []
    
    for summary in summaries_queryset.order_by('-created_at'):
        if summary.is_batch:
            if summary.batch_id not in batch_groups:
                batch_groups[summary.batch_id] = {
                    'batch_info': summary,  # Use first summary for batch info
                    'summaries': [],
                    'total_count': 0,
                    'completed_count': 0,
                    'all_completed': True
                }
            
            batch_groups[summary.batch_id]['summaries'].append(summary)
            batch_groups[summary.batch_id]['total_count'] += 1
            
            if summary.status == 'completed':
                batch_groups[summary.batch_id]['completed_count'] += 1
            else:
                batch_groups[summary.batch_id]['all_completed'] = False
        else:
            single_summaries.append(summary)
    
    # Combine batches and single summaries for pagination
    display_items = []
    
    # Add batch groups (sorted by creation time of first item)
    for batch_id, batch_data in sorted(batch_groups.items(), 
                                     key=lambda x: x[1]['batch_info'].created_at, 
                                     reverse=True):
        display_items.append({
            'type': 'batch',
            'data': batch_data,
            'created_at': batch_data['batch_info'].created_at
        })
    
    # Add single summaries
    for summary in single_summaries:
        display_items.append({
            'type': 'single',
            'data': summary,
            'created_at': summary.created_at
        })
    
    # Sort all items by creation time
    display_items.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Pagination
    paginator = Paginator(display_items, 10)
    page = request.GET.get('page')
    items = paginator.get_page(page)
    
    context = {
        'items': items,
        'project_types': [('ah', 'AH PLLC'), ('tlc', 'TLC S PLLC'), ('sa', 'SA PLLC'), ('lw', 'LW PLLC')],
        'statuses': [('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), 
                    ('corrected', 'Corrected'), ('error', 'Error')],
        'selected_project_type': project_type,
        'selected_status': status,
        'search_query': search,
    }
    
    return render(request, 'summaries.html', context)


@login_required
def batch_download(request, batch_id):
    """Download all completed summaries in a batch as a zip file"""
    try:
        batch_uuid = uuid.UUID(batch_id)
    except ValueError:
        messages.error(request, "Invalid batch ID.")
        return redirect('summary-list')
    
    # Get all completed summaries in the batch
    if request.user.is_superuser:
        summaries = Summary.objects.filter(batch_id=batch_uuid, status='completed')
    else:
        summaries = Summary.objects.filter(batch_id=batch_uuid, status='completed', user=request.user)
    
    if not summaries.exists():
        messages.error(request, "No completed summaries found in this batch.")
        return redirect('summary-list')
    
    # Create zip file in memory instead of using temporary file
    import io
    
    # Create a BytesIO buffer to hold the zip data
    zip_buffer = io.BytesIO()
    
    # Create the zip file in memory
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for summary in summaries:
            if summary.summary_text:
                # Create filename for this summary
                filename = f"{slugify(summary.document_name)}_summary.txt"
                
                # Add summary text to zip
                zip_file.writestr(filename, summary.summary_text)
    
    # Get the zip data
    zip_data = zip_buffer.getvalue()
    zip_buffer.close()
    
    # Create the response
    response = HttpResponse(zip_data, content_type='application/zip')
    
    # Create zip filename from batch name or use default
    batch_name = summaries.first().batch_name or f"Batch_{batch_id[:8]}"
    zip_filename = f"{slugify(batch_name)}_summaries.zip"
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    
    return response

# Summary detail view
@login_required
def summary_detail(request, pk):
    """View to display a summary's details"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to view this summary
    if not request.user.is_superuser and summary.user != request.user:
        messages.error(request, "You do not have permission to view this summary.")
        return redirect('summary-list')
    
    context = {
        'summary': summary,
    }
    return render(request, 'summary_detail.html', context)

# Summary feedback view
@login_required
def summary_feedback(request, pk):
    """View to provide feedback on a summary"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to provide feedback on this summary
    if not request.user.is_superuser and summary.user != request.user:
        messages.error(request, "You do not have permission to provide feedback on this summary.")
        return redirect('summary-list')
    
    if request.method == 'POST':
        form = SummaryFeedbackForm(request.POST, instance=summary)
        if form.is_valid():
            # Save the corrected text
            corrected_summary = form.save(commit=False)
            corrected_summary.status = 'corrected'
            corrected_summary.save()
            
            # Process the correction in a Celery task
            process_human_correction.delay(summary.id)
            
            messages.success(request, "Thank you for your feedback! It will be used to improve future summaries.")
            return redirect('summary-detail', pk=summary.id)
    else:
        form = SummaryFeedbackForm(instance=summary)
        if not summary.corrected_text:
            # Pre-fill with the generated summary text
            form.initial['corrected_text'] = summary.summary_text
    
    context = {
        'summary': summary,
        'form': form,
    }
    return render(request, 'summary_feedback.html', context)

# Delete summary view
@login_required
def summary_delete(request, pk):
    """View to delete a summary"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to delete this summary
    if not request.user.is_superuser and summary.user != request.user:
        messages.error(request, "You do not have permission to delete this summary.")
        return redirect('summary-list')
    
    if request.method == 'POST':
        summary.delete()
        messages.success(request, "Summary deleted successfully.")
        return redirect('summary-list')
    
    context = {
        'summary': summary,
    }
    return render(request, 'summary_delete.html', context)

# Regenerate summary view
@login_required
def summary_regenerate(request, pk):
    """View to regenerate a summary"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to regenerate this summary
    if not request.user.is_superuser and summary.user != request.user:
        messages.error(request, "You do not have permission to regenerate this summary.")
        return redirect('summary-list')
    
    if request.method == 'POST':
        # Reset the summary status
        summary.status = 'pending'
        summary.summary_text = ''
        summary.save()
        
        # Start the summarization process as a Celery task
        process_summary.delay(summary.id)
        
        messages.success(request, "Your summary is being regenerated.")
        return redirect('summary-detail', pk=summary.id)
    
    context = {
        'summary': summary,
    }
    return render(request, 'summary_regenerate.html', context)

# Download summary view
@login_required
def summary_download(request, pk):
    """View to download a summary as a text file"""
    summary = get_object_or_404(Summary, pk=pk)
    
    # Check if the user is authorized to download this summary
    if not request.user.is_superuser and summary.user != request.user:
        messages.error(request, "You do not have permission to download this summary.")
        return redirect('summary-list')
    
    # Create the response with the summary text
    response = HttpResponse(summary.summary_text, content_type='text/plain')
    filename = f"{slugify(summary.document_name)}_summary.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

# Example list view (superuser only)
@login_required
def example_list(request):
    """View to display all example sets"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access example sets.")
        return redirect('home')
    
    example_sets = ExampleSet.objects.all().order_by('-created_at')
    
    context = {
        'example_sets': example_sets,
    }
    return render(request, 'example_list.html', context)

# The rest of the views remain mostly the same but with superuser checks added
# I'll include the remaining views for completeness

# Example set create view (superuser only)
@login_required
def example_set_create(request):
    """View to create a new example set"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to create example sets.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ExampleSetForm(request.POST)
        if form.is_valid():
            example_set = form.save()
            messages.success(request, "Example set created successfully.")
            return redirect('example-set-detail', pk=example_set.id)
    else:
        form = ExampleSetForm()
    
    context = {
        'form': form,
    }
    return render(request, 'example_set_create.html', context)

# Example set detail view (superuser only)
@login_required
def example_set_detail(request, pk):
    """View to display an example set's details"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to view example sets.")
        return redirect('home')
    
    example_set = get_object_or_404(ExampleSet, pk=pk)
    examples = example_set.examples.all().order_by('-uploaded_at')
    
    context = {
        'example_set': example_set,
        'examples': examples,
    }
    return render(request, 'example_set_detail.html', context)

# Add example to set view (superuser only)
@login_required
def example_add(request, pk):
    """View to add an example to an example set"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to add examples.")
        return redirect('home')
    
    example_set = get_object_or_404(ExampleSet, pk=pk)
    
    if request.method == 'POST':
        pdf_file = request.FILES.get('pdf_file')
        summary_file = request.FILES.get('summary_file')
        
        if pdf_file and summary_file:
            # Create a new example
            example = DocumentExample(
                name=os.path.splitext(pdf_file.name)[0],
                example_set=example_set,
                pdf_file=pdf_file,
                summary_file=summary_file
            )
            example.save()
            
            # Update the PROJECT_EXAMPLES dictionary
            load_example_data()
            
            messages.success(request, f"Example '{example.name}' added successfully.")
        else:
            messages.error(request, "Please provide both a PDF file and a summary file.")
        
        return redirect('example-set-detail', pk=example_set.id)
    
    context = {
        'example_set': example_set,
    }
    return render(request, 'example_add.html', context)

# Delete example set view (superuser only)
@login_required
def example_set_delete(request, pk):
    """View to delete an example set"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to delete example sets.")
        return redirect('home')
    
    example_set = get_object_or_404(ExampleSet, pk=pk)
    
    if request.method == 'POST':
        # Delete the example set
        example_set.delete()
        
        # Update the PROJECT_EXAMPLES dictionary
        load_example_data()
        
        messages.success(request, "Example set deleted successfully.")
        return redirect('example-list')
    
    context = {
        'example_set': example_set,
    }
    return render(request, 'example_set_delete.html', context)

# Reports view (superuser only)
@login_required
def reports(request):
    """View to display available reports"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access reports.")
        return redirect('home')
    
    # Get basic stats
    total_summaries = Summary.objects.count()
    completed_summaries = Summary.objects.filter(status='completed').count()
    corrected_summaries = Summary.objects.filter(status='corrected').count()
    
    # Get accuracy statistics
    summaries_with_accuracy = Summary.objects.filter(accuracy_score__isnull=False)
    avg_accuracy = summaries_with_accuracy.values_list('accuracy_score', flat=True).aggregate(
        avg=models.Avg('accuracy_score')
    )
    
    context = {
        'total_summaries': total_summaries,
        'completed_summaries': completed_summaries,
        'corrected_summaries': corrected_summaries,
        'summaries_with_accuracy': summaries_with_accuracy.count(),
        'avg_accuracy': avg_accuracy['avg'] if avg_accuracy['avg'] else 0,
    }
    return render(request, 'reports.html', context)

# Error report view (superuser only)
@login_required
def error_report(request):
    """View to display the error analysis report"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access error reports.")
        return redirect('home')
    
    # Get the error patterns
    errors = ErrorPattern.objects.all()
    
    # Count by error type
    error_types = errors.values('error_type').annotate(count=models.Count('id'))
    
    # Count by section
    error_sections = errors.values('section').annotate(count=models.Count('id'))
    
    # Generate the report
    config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
    config['openai_api_key'] = settings.OPENAI_API_KEY
    
    # Initialize the summarizer (without a PDF file for report generation)
    from .summarizer_engine.medical_summarizer import MedicalSummarizer
    summarizer = MedicalSummarizer(
        config=config,
        new_pdf=None
    )
    
    # Generate the error analysis report
    error_report = summarizer.generate_error_analysis_report()
    
    context = {
        'error_types': error_types,
        'error_sections': error_sections,
        'error_report': error_report,
    }
    return render(request, 'error_report.html', context)

# Accuracy report view (superuser only)
@login_required
def accuracy_report(request):
    """View to display the accuracy trend report"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to access accuracy reports.")
        return redirect('home')
    
    # Get summaries with accuracy scores
    summaries_with_accuracy = Summary.objects.filter(accuracy_score__isnull=False)
    
    # Initialize the accuracy tracker
    accuracy_tracker = SummaryAccuracyTracker()
    
    # Generate trend report if there are enough data points
    trend_report = "Not enough data to generate trends. Need at least 2 data points."
    if summaries_with_accuracy.count() >= 2:
        # Prepare data for the tracker
        for summary in summaries_with_accuracy:
            if summary.summary_text and summary.corrected_text:
                metrics = accuracy_tracker.calculate_metrics(
                    summary.summary_text,
                    summary.corrected_text
                )
                accuracy_tracker.add_metrics(
                    summary.id,
                    summary.summary_text,
                    summary.corrected_text
                )
        
        # Generate the report
        trend_report = accuracy_tracker.generate_trend_report()
    
    context = {
        'summaries_with_accuracy': summaries_with_accuracy,
        'trend_report': trend_report,
    }
    return render(request, 'accuracy_report.html', context)

# NEW: Authentication views
@login_required
def register(request):
    """View for creating new user accounts (superuser only)"""
    if not request.user.is_superuser:
        messages.error(request, "You do not have permission to create user accounts.")
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_type = form.cleaned_data['user_type']
            
            # Success message with user type info
            if user_type == 'admin':
                messages.success(
                    request, 
                    f"Administrator account '{user.username}' created successfully with full system access."
                )
            else:
                messages.success(
                    request, 
                    f"Staff account '{user.username}' created successfully with limited access."
                )
            
            return redirect('register')  # Redirect to create another user
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()
    
    # Get existing users for context
    users = User.objects.all().order_by('-date_joined')[:10]  # Show last 10 created users
    
    context = {
        'form': form,
        'recent_users': users,
    }
    return render(request, 'register.html', context)

def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('login')
from celery import shared_task
import os
import json
from django.conf import settings
from .models import Summary, ErrorPattern
from .summarizer_engine.medical_summarizer import MedicalSummarizer
from .summarizer_engine.summary_accuracy_tracker import SummaryAccuracyTracker

# Global dictionary to store the examples for each project type
PROJECT_EXAMPLES = {
    'ah': [],
    'tlc': [],
    'sa': [],
    'lw': [],
}

def load_example_data():
    """Load example data for each project type from the database"""
    from .models import ExampleSet
    
    for project_type in PROJECT_EXAMPLES.keys():
        PROJECT_EXAMPLES[project_type] = []
        example_sets = ExampleSet.objects.filter(project_type=project_type)
        for example_set in example_sets:
            examples = example_set.examples.all()
            for example in examples:
                PROJECT_EXAMPLES[project_type].append({
                    'pdf': example.pdf_file.path,
                    'summary': example.summary_file.path
                })

@shared_task
def process_summary(summary_id):
    """Background task to generate a summary"""
    from .models import Summary  # Import here to avoid circular imports
    
    # Load example data if needed
    if not any(PROJECT_EXAMPLES.values()):
        load_example_data()
    
    # Get the summary object
    summary = Summary.objects.get(id=summary_id)
    summary.status = 'processing'
    summary.save()
    
    try:
        # Configure the summarizer
        config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
        config['openai_api_key'] = settings.OPENAI_API_KEY
        
        # Get examples for the project type
        example_without_password = PROJECT_EXAMPLES.get(summary.project_type, [])
        
        # Initialize the summarizer
        summarizer = MedicalSummarizer(
            config=config,
            new_pdf=summary.pdf_file.path,
            example_without_password=example_without_password
        )
        
        # Set new PDF password if provided
        if summary.pdf_password:
            config['new_pdf_password'] = summary.pdf_password
        
        # Generate the summary
        result, original_text = summarizer.summarize(
            project_name=summary.project_type, 
            output_file=f"{summary.document_name}.txt"
        )
        
        # Update the summary object
        summary.summary_text = result
        summary.original_text = original_text
        summary.status = 'completed'
        summary.save()
        
    except Exception as e:
        # Handle errors
        summary.status = 'error'
        summary.summary_text = f"Error generating summary: {str(e)}"
        summary.save()

@shared_task
def process_human_correction(summary_id):
    """Process a human correction to improve future summaries"""
    from .models import Summary, ErrorPattern  # Import here to avoid circular imports
    
    summary = Summary.objects.get(id=summary_id)
    
    # Configure the summarizer
    config = settings.MEDICAL_SUMMARIZER_CONFIG.copy()
    config['openai_api_key'] = settings.OPENAI_API_KEY
    
    # Initialize the summarizer
    summarizer = MedicalSummarizer(
        config=config,
        new_pdf=summary.pdf_file.path
    )
    
    # Process the correction
    error_report = summarizer.process_human_correction(
        f"{summary.document_name}.txt",
        summary.corrected_text
    )
    
    # Calculate accuracy metrics
    accuracy_tracker = SummaryAccuracyTracker()
    metrics = accuracy_tracker.calculate_metrics(
        summary.summary_text,
        summary.corrected_text
    )
    
    # Save accuracy score
    summary.accuracy_score = metrics['overall_score']
    summary.save()
    
    # Create error patterns
    try:
        error_data = json.loads(error_report)
        for error in error_data.get('section_errors', []):
            ErrorPattern.objects.create(
                error_type=error['type'],
                section=error['section'],
                summary=summary
            )
        
        for error in error_data.get('content_errors', []):
            ErrorPattern.objects.create(
                error_type=error['error_type'],
                section=error['section'],
                original_text=error.get('original', ''),
                corrected_text=error.get('correction', ''),
                summary=summary
            )
    except:
        # If error report is not JSON, just continue
        pass
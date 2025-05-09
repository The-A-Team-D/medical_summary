from django.db import models
from django.urls import reverse
import os

def example_upload_path(instance, filename):
    """Generate upload path for document examples"""
    return f'examples/{instance.example_set.name}/{filename}'

def summary_upload_path(instance, filename):
    """Generate upload path for documents to summarize"""
    return f'documents/{instance.project_type}/{filename}'

class ExampleSet(models.Model):
    """Collection of examples for a specific project type"""
    name = models.CharField(max_length=100)
    project_type = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} ({self.project_type})"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Example Set'
        verbose_name_plural = 'Example Sets'

class DocumentExample(models.Model):
    """Example document with its summary for training"""
    name = models.CharField(max_length=255)
    example_set = models.ForeignKey(ExampleSet, on_delete=models.CASCADE, related_name='examples')
    pdf_file = models.FileField(upload_to=example_upload_path)
    summary_file = models.FileField(upload_to=example_upload_path)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('example-detail', args=[str(self.id)])
    
    def filename(self):
        return os.path.basename(self.pdf_file.name)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Document Example'
        verbose_name_plural = 'Document Examples'

class Summary(models.Model):
    """Summary of a medical document"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('corrected', 'Corrected'),
        ('error', 'Error'),
    ]
    
    document_name = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to=summary_upload_path)
    project_type = models.CharField(max_length=50)
    pdf_password = models.CharField(max_length=100, blank=True)
    summary_text = models.TextField(blank=True)
    original_text = models.TextField(blank=True)
    corrected_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    accuracy_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.document_name
    
    def get_absolute_url(self):
        return reverse('summary-detail', args=[str(self.id)])
    
    def filename(self):
        return os.path.basename(self.pdf_file.name)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Medical Summary'
        verbose_name_plural = 'Medical Summaries'

class ErrorPattern(models.Model):
    """Error patterns identified during corrections"""
    ERROR_TYPES = [
        ('missing_section', 'Missing Section'),
        ('extra_section', 'Extra Section'),
        ('missing_content', 'Missing Content'),
        ('incorrect_information', 'Incorrect Information'),
        ('removed_content', 'Removed Content'),
    ]
    
    error_type = models.CharField(max_length=50, choices=ERROR_TYPES)
    section = models.CharField(max_length=100)
    original_text = models.TextField(blank=True)
    corrected_text = models.TextField(blank=True)
    summary = models.ForeignKey(Summary, on_delete=models.CASCADE, related_name='errors')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.error_type} in {self.section}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Error Pattern'
        verbose_name_plural = 'Error Patterns'
from django.contrib import admin
from .models import DocumentExample, Summary, ExampleSet, ErrorPattern

@admin.register(DocumentExample)
class DocumentExampleAdmin(admin.ModelAdmin):
    list_display = ('name', 'example_set', 'uploaded_at')
    list_filter = ('example_set', 'uploaded_at')
    search_fields = ('name', 'description')

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    list_display = ('document_name', 'project_type', 'created_at', 'status')
    list_filter = ('project_type', 'created_at', 'status')
    search_fields = ('document_name', 'summary_text')

@admin.register(ExampleSet)
class ExampleSetAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_type', 'created_at')
    list_filter = ('project_type', 'created_at')
    search_fields = ('name', 'description')

@admin.register(ErrorPattern)
class ErrorPatternAdmin(admin.ModelAdmin):
    list_display = ('error_type', 'section', 'created_at')
    list_filter = ('error_type', 'section', 'created_at')
    search_fields = ('error_type', 'section', 'original_text', 'corrected_text')
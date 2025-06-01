#!/usr/bin/env python
"""
Script to manually create the database tables for the Medical Summarizer app.
This is a last resort if migrations aren't working.
"""
import os
import sqlite3
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medical_summarizer.settings')
django.setup()

from django.conf import settings

def create_tables_manually():
    """Create the database tables manually using SQL"""
    db_path = settings.DATABASES['default']['NAME']
    
    print(f"Creating tables in database: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create ExampleSet table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS summarizer_exampleset (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name VARCHAR(100) NOT NULL,
    #     project_type VARCHAR(50) NOT NULL,
    #     description TEXT NOT NULL,
    #     created_at DATETIME NOT NULL
    # );
    # ''')

    cursor.execute('''
    view tables;
    ''')
    
    # Create Summary table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS summarizer_summary (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     document_name VARCHAR(255) NOT NULL,
    #     pdf_file VARCHAR(100) NOT NULL,
    #     project_type VARCHAR(50) NOT NULL,
    #     pdf_password VARCHAR(100) NOT NULL,
    #     summary_text TEXT NOT NULL,
    #     original_text TEXT NOT NULL,
    #     corrected_text TEXT NOT NULL,
    #     status VARCHAR(20) NOT NULL,
    #     accuracy_score REAL NULL,
    #     created_at DATETIME NOT NULL,
    #     updated_at DATETIME NOT NULL
    # );
    # ''')

  
    
    # Create DocumentExample table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS summarizer_documentexample (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     name VARCHAR(255) NOT NULL,
    #     pdf_file VARCHAR(100) NOT NULL,
    #     summary_file VARCHAR(100) NOT NULL,
    #     description TEXT NOT NULL,
    #     uploaded_at DATETIME NOT NULL,
    #     example_set_id INTEGER NOT NULL,
    #     FOREIGN KEY (example_set_id) REFERENCES summarizer_exampleset (id)
    # );
    # ''')

    # Create ErrorPattern table
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS summarizer_errorpattern (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     error_type VARCHAR(50) NOT NULL,
    #     section VARCHAR(100) NOT NULL,
    #     original_text TEXT NOT NULL,
    #     corrected_text TEXT NOT NULL,
    #     created_at DATETIME NOT NULL,
    #     summary_id INTEGER NOT NULL,
    #     FOREIGN KEY (summary_id) REFERENCES summarizer_summary (id)
    # );
    # ''')


    # Create the django_migrations table if it doesn't exist
    # cursor.execute('''
    # CREATE TABLE IF NOT EXISTS django_migrations (
    #     id INTEGER PRIMARY KEY AUTOINCREMENT,
    #     app VARCHAR(255) NOT NULL,
    #     name VARCHAR(255) NOT NULL,
    #     applied DATETIME NOT NULL
    # );
    # ''')
  
    
    # Insert a fake migration record for our app
    # cursor.execute('''
    # INSERT INTO django_migrations (app, name, applied)
    # VALUES ('summarizer', 'manual_migration', CURRENT_TIMESTAMP);
    # ''')
    
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables_manually()
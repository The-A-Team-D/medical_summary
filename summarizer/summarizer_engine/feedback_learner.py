import os
from datetime import datetime
from .error_tracker import ErrorTracker

class FeedbackLearner:
    """
    Manages the feedback loop between generated summaries and human corrections
    """
    def __init__(self, feedback_directory="./feedback"):
        self.feedback_directory = feedback_directory
        self.original_dir = os.path.join(feedback_directory, "original")
        self.corrected_dir = os.path.join(feedback_directory, "corrected")
        self.error_tracker = ErrorTracker()
        
        # Create directories if they don't exist
        os.makedirs(self.original_dir, exist_ok=True)
        os.makedirs(self.corrected_dir, exist_ok=True)
    
    def store_original_summary(self, filename, summary):
        """Store the originally generated summary"""
        with open(os.path.join(self.original_dir, filename), 'w') as f:
            f.write(summary)
    
    def register_correction(self, filename, corrected_summary):
        """Register a human correction to a summary"""
        # Read the original summary
        original_path = os.path.join(self.original_dir, filename)
        if not os.path.exists(original_path):
            raise FileNotFoundError(f"Original summary {filename} not found")
        
        with open(original_path, 'r') as f:
            original_summary = f.read()
        
        # Store the corrected summary
        with open(os.path.join(self.corrected_dir, filename), 'w') as f:
            f.write(corrected_summary)
        
        # Analyze differences and update error patterns
        error_report = self.error_tracker.analyze_differences(original_summary, corrected_summary)
        
        return error_report
    
    def scan_for_new_corrections(self):
        """
        Scan the corrected directory for new corrections not yet processed
        and analyze them
        """
        # Get all corrected files
        corrected_files = os.listdir(self.corrected_dir)
        for filename in corrected_files:
            original_path = os.path.join(self.original_dir, filename)
            corrected_path = os.path.join(self.corrected_dir, filename)
            
            # Check if this correction has been processed
            processed_marker = os.path.join(self.corrected_dir, f".{filename}.processed")
            
            if filename.startswith(".") or filename == ".ipynb_checkpoints":
                continue
            
            if os.path.exists(original_path) and not os.path.exists(processed_marker):
                # Read original and corrected summaries
                with open(original_path, 'r') as f:
                    original_summary = f.read()
                
                with open(corrected_path, 'r') as f:
                    corrected_summary = f.read()
                
                # Analyze differences
                self.error_tracker.analyze_differences(original_summary, corrected_summary)
                
                # Mark as processed
                with open(processed_marker, 'w') as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def get_improvement_prompt(self):
        """Get prompt additions based on historical errors"""
        return self.error_tracker.generate_improvement_prompt()
    
    def generate_error_analysis_report(self):
        """Generate a comprehensive error analysis report"""
        # Count error types
        error_counts = {
            "missing_sections": len([e for e in self.error_tracker.error_patterns["section_errors"] 
                                  if e["type"] == "missing_section"]),
            "extra_sections": len([e for e in self.error_tracker.error_patterns["section_errors"] 
                                if e["type"] == "extra_section"]),
            "missing_content": len([e for e in self.error_tracker.error_patterns["content_errors"] 
                                 if e["error_type"] == "missing_content"]),
            "incorrect_information": len([e for e in self.error_tracker.error_patterns["content_errors"] 
                                       if e["error_type"] == "incorrect_information"]),
            "removed_content": len([e for e in self.error_tracker.error_patterns["content_errors"] 
                                 if e["error_type"] == "removed_content"]),
        }
        
        # Generate section-specific error counts
        section_errors = {}
        for error in self.error_tracker.error_patterns["content_errors"]:
            section = error["section"]
            if section not in section_errors:
                section_errors[section] = 0
            section_errors[section] += 1
        
        # Generate report
        report = "# Error Analysis Report\n\n"
        report += "## Error Type Counts\n\n"
        report += f"- Missing Sections: {error_counts['missing_sections']}\n"
        report += f"- Extra Sections: {error_counts['extra_sections']}\n"
        report += f"- Missing Content: {error_counts['missing_content']}\n"
        report += f"- Incorrect Information: {error_counts['incorrect_information']}\n"
        report += f"- Removed Content: {error_counts['removed_content']}\n\n"
        
        report += "## Errors by Section\n\n"
        for section, count in section_errors.items():
            report += f"- {section}: {count} errors\n"
        
        report += "\n## Common Mistakes\n\n"
        for original, correction in self.error_tracker.error_patterns["common_mistakes"].items():
            report += f"- '{original}' should be '{correction}'\n"
        
        return report
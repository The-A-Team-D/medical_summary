import os
import json
import re
import difflib
from datetime import datetime

class ErrorTracker:
    """
    Tracks and analyzes errors in generated summaries compared to human corrections.
    """
    def __init__(self, feedback_db_path="./feedback_database.json"):
        self.feedback_db_path = feedback_db_path
        self.error_patterns = self.load_error_database()
        
    def load_error_database(self):
        """Load existing error patterns from database file"""
        if os.path.exists(self.feedback_db_path):
            with open(self.feedback_db_path, 'r') as f:
                return json.load(f)
        return {
            "section_errors": [],  # Missing or incorrect sections
            "content_errors": [],  # Incorrect or missing content within sections
            "format_errors": [],   # Formatting issues
            "common_mistakes": {}, # Dictionary of common mistakes and their corrections
            "error_examples": []   # Full examples of errors and their corrections
        }
    
    def save_error_database(self):
        """Save error patterns to database file"""
        with open(self.feedback_db_path, 'w') as f:
            json.dump(self.error_patterns, f, indent=2)
    
    def analyze_differences(self, original_summary, corrected_summary):
        """
        Analyze differences between original and corrected summaries
        to identify patterns of errors
        """
        # Split into sections for section-level comparison
        original_sections = self._split_into_sections(original_summary)
        corrected_sections = self._split_into_sections(corrected_summary)
        
        # Identify missing or extra sections
        original_section_titles = set(original_sections.keys())
        corrected_section_titles = set(corrected_sections.keys())
        
        missing_sections = corrected_section_titles - original_section_titles
        extra_sections = original_section_titles - corrected_section_titles
        
        # Add to section errors
        for section in missing_sections:
            self.error_patterns["section_errors"].append({
                "type": "missing_section",
                "section": section,
                "content": corrected_sections.get(section, "")
            })
        
        for section in extra_sections:
            self.error_patterns["section_errors"].append({
                "type": "extra_section",
                "section": section,
            })
        
        # Compare content of each section that exists in both
        for section in original_section_titles.intersection(corrected_section_titles):
            self._compare_section_content(
                section,
                original_sections[section], 
                corrected_sections[section]
            )
        
        # Store the full example for reference
        self.error_patterns["error_examples"].append({
            "original": original_summary,
            "corrected": corrected_summary,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # Save updated error patterns
        self.save_error_database()
        
        return self._generate_error_report(original_summary, corrected_summary)
    
    def _split_into_sections(self, text):
        """
        Split a summary into sections based on headers
        Returns a dictionary of section_name: section_content
        """
        # Common section headers in medical summaries
        section_headers = [
            "CHIEF COMPLAINT",
            "HISTORY OF PRESENT ILLNESS",
            "REVIEW OF SYSTEMS",
            "MEDICATIONS",
            "ALLERGIES",
            "PAST MEDICAL HISTORY",
            "PAST SURGICAL HISTORY",
            "FAMILY HISTORY",
            "SOCIAL HISTORY",
            "PHYSICAL EXAMINATION",
            "VITAL SIGNS",
            "DIAGNOSTIC STUDIES",
            "LABORATORY RESULTS",
            "DIAGNOSIS AND MEDICAL DECISION MAKING",
            "TREATMENTS",
            "DISPOSITION",
            "FOLLOWUP"
        ]
        
        # Create a dictionary to store sections
        sections = {}
        current_section = "PREAMBLE"  # Default section for content before any header
        sections[current_section] = ""
        
        lines = text.split('\n')
        
        for line in lines:
            is_header = False
            for header in section_headers:
                # Check if line contains a section header
                if re.search(rf'\b{re.escape(header)}\b', line, re.IGNORECASE):
                    current_section = header
                    sections[current_section] = line + "\n"
                    is_header = True
                    break
            
            if not is_header and current_section in sections:
                sections[current_section] += line + "\n"
        
        return sections
    
    def _compare_section_content(self, section_name, original_content, corrected_content):
        """Compare content within a section to identify specific errors"""
        # Use difflib to find differences
        d = difflib.Differ()
        diff = list(d.compare(original_content.splitlines(), corrected_content.splitlines()))
        
        # Extract differences
        for line in diff:
            if line.startswith('- '):  # Line in original but not in corrected
                # Check if there's a similar line in the corrected content
                original_line = line[2:]
                matching_line = self._find_closest_match(original_line, corrected_content.splitlines())
                
                if matching_line:
                    # Found a similar line - this suggests a correction rather than deletion
                    word_diff = self._compare_words(original_line, matching_line)
                    
                    for removed, added in word_diff:
                        if removed and added:
                            # Add to common mistakes dictionary
                            self.error_patterns["common_mistakes"][removed] = added
                            
                            # Add to content errors for this section
                            self.error_patterns["content_errors"].append({
                                "section": section_name,
                                "error_type": "incorrect_information",
                                "original": removed,
                                "correction": added
                            })
                else:
                    # No similar line found - this suggests a deletion
                    self.error_patterns["content_errors"].append({
                        "section": section_name,
                        "error_type": "removed_content",
                        "content": original_line
                    })
            
            elif line.startswith('+ '):  # Line in corrected but not in original
                added_line = line[2:]
                matching_line = self._find_closest_match(added_line, original_content.splitlines())
                
                if not matching_line:
                    # No similar line found - this suggests an addition
                    self.error_patterns["content_errors"].append({
                        "section": section_name,
                        "error_type": "missing_content",
                        "content": added_line
                    })
    
    def _find_closest_match(self, line, line_list, threshold=0.7):
        """Find the closest matching line in a list of lines"""
        best_match = None
        best_ratio = 0
        
        for candidate in line_list:
            ratio = difflib.SequenceMatcher(None, line, candidate).ratio()
            if ratio > best_ratio and ratio > threshold:
                best_ratio = ratio
                best_match = candidate
        
        return best_match
    
    def _compare_words(self, original, corrected):
        """
        Compare words between two strings to identify specific word changes
        Returns a list of (removed, added) pairs
        """
        original_words = original.split()
        corrected_words = corrected.split()
        
        # Calculate word-level diff
        word_diff = []
        matcher = difflib.SequenceMatcher(None, original_words, corrected_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                removed = ' '.join(original_words[i1:i2])
                added = ' '.join(corrected_words[j1:j2])
                word_diff.append((removed, added))
            elif tag == 'delete':
                removed = ' '.join(original_words[i1:i2])
                word_diff.append((removed, ""))
            elif tag == 'insert':
                added = ' '.join(corrected_words[j1:j2])
                word_diff.append(("", added))
        
        return word_diff
    
    def _generate_error_report(self, original, corrected):
        """Generate a human-readable report of the errors found"""
        report = "Error Analysis Report:\n\n"
        
        # Section-level errors
        missing_sections = [e["section"] for e in self.error_patterns["section_errors"] 
                         if e["type"] == "missing_section"]
        extra_sections = [e["section"] for e in self.error_patterns["section_errors"] 
                        if e["type"] == "extra_section"]
        
        if missing_sections:
            report += "Missing Sections:\n"
            for section in missing_sections:
                report += f"- {section}\n"
            report += "\n"
        
        if extra_sections:
            report += "Extra Sections (not required):\n"
            for section in extra_sections:
                report += f"- {section}\n"
            report += "\n"
        
        # Content errors
        content_errors = [e for e in self.error_patterns["content_errors"] 
                         if e["section"] in missing_sections]
        
        if content_errors:
            report += "Content Errors:\n"
            for error in content_errors:
                report += f"- Section: {error['section']}, Type: {error['error_type']}\n"
                if error['error_type'] == 'incorrect_information':
                    report += f"  Original: '{error['original']}'\n"
                    report += f"  Corrected: '{error['correction']}'\n"
                else:
                    report += f"  Content: '{error['content']}'\n"
            report += "\n"
        
        # Show diff
        d = difflib.unified_diff(
            original.splitlines(),
            corrected.splitlines(),
            lineterm='',
            n=3  # Context lines
        )
        
        diff_text = '\n'.join(list(d)[2:])  # Skip the first two lines (--- and +++)
        
        if diff_text:
            report += "Detailed Differences:\n"
            report += diff_text
        
        return report
    
    def generate_improvement_prompt(self):
        """
        Generate a prompt addition based on historical errors
        to improve future summaries
        """
        improvement_prompt = "\n\nADDITIONAL CORRECTION GUIDANCE BASED ON PAST ERRORS:\n"
        
        # Add section errors guidance
        missing_sections = set(e["section"] for e in self.error_patterns["section_errors"] 
                             if e["type"] == "missing_section")
        
        if missing_sections:
            improvement_prompt += "1. FREQUENTLY MISSING SECTIONS: Always include these commonly missed sections:\n"
            for section in missing_sections:
                improvement_prompt += f"   - {section}\n"
        
        # Add common mistakes
        if self.error_patterns["common_mistakes"]:
            improvement_prompt += "\n2. COMMON TERMINOLOGY CORRECTIONS:\n"
            for original, correction in self.error_patterns["common_mistakes"].items():
                improvement_prompt += f"   - Replace '{original}' with '{correction}'\n"
        
        # Add content error patterns
        content_error_types = {}
        for error in self.error_patterns["content_errors"]:
            section = error["section"]
            error_type = error["error_type"]
            
            if section not in content_error_types:
                content_error_types[section] = []
            
            content_error_types[section].append(error)
        
        if content_error_types:
            improvement_prompt += "\n3. SECTION-SPECIFIC IMPROVEMENTS:\n"
            for section, errors in content_error_types.items():
                improvement_prompt += f"   For {section}:\n"
                for error in errors[:5]:  # Limit to 5 examples per section
                    if error["error_type"] == "missing_content":
                        improvement_prompt += f"   - Include: '{error['content']}'\n"
                    elif error["error_type"] == "incorrect_information":
                        improvement_prompt += f"   - Replace '{error['original']}' with '{error['correction']}'\n"
        
        return improvement_prompt
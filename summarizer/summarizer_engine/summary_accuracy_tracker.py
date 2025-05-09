import os
import re
import difflib
import pandas as pd
from datetime import datetime

class SummaryAccuracyTracker:
    """
    Tracks accuracy metrics over time to measure system improvement
    """
    def __init__(self, metrics_file="summary_accuracy_metrics.csv"):
        self.metrics_file = metrics_file
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        if os.path.exists(self.metrics_file):
            return pd.read_csv(self.metrics_file)
        else:
            return pd.DataFrame(columns=[
                'date', 'file_id', 'sections_accuracy', 'content_accuracy', 
                'format_accuracy', 'overall_score', 'correction_count'
            ])
    
    def calculate_metrics(self, original_summary, corrected_summary):
        """Calculate accuracy metrics between original and corrected summaries"""
        # Calculate section accuracy
        original_sections = self._extract_sections(original_summary)
        corrected_sections = self._extract_sections(corrected_summary)
        
        total_sections = len(corrected_sections)
        matching_sections = len(set(original_sections) & set(corrected_sections))
        sections_accuracy = matching_sections / total_sections if total_sections > 0 else 0
        
        # Calculate content accuracy based on edit distance
        content_similarity = difflib.SequenceMatcher(None, original_summary, corrected_summary).ratio()
        content_accuracy = content_similarity
        
        # Format accuracy (simplified)
        format_accuracy = self._calculate_format_accuracy(original_summary, corrected_summary)
        
        # Overall score (weighted average)
        overall_score = 0.3 * sections_accuracy + 0.5 * content_accuracy + 0.2 * format_accuracy
        
        return {
            'sections_accuracy': sections_accuracy,
            'content_accuracy': content_accuracy,
            'format_accuracy': format_accuracy,
            'overall_score': overall_score,
            'correction_count': self._count_corrections(original_summary, corrected_summary)
        }
    
    def _extract_sections(self, text):
        """Extract section headers from text"""
        section_pattern = r'^([A-Z][A-Z\s]+)(?::|\n)'
        return re.findall(section_pattern, text, re.MULTILINE)
    
    def _calculate_format_accuracy(self, original, corrected):
        """Calculate format accuracy based on structural elements"""
        # Count structural elements in both texts
        original_paragraphs = len(original.split('\n\n'))
        corrected_paragraphs = len(corrected.split('\n\n'))
        
        original_lists = len(re.findall(r'^\s*[-*•]\s', original, re.MULTILINE))
        corrected_lists = len(re.findall(r'^\s*[-*•]\s', corrected, re.MULTILINE))
        
        # Calculate similarity ratio
        paragraph_ratio = min(original_paragraphs, corrected_paragraphs) / max(original_paragraphs, corrected_paragraphs)
        list_ratio = min(original_lists, corrected_lists) / max(original_lists, corrected_lists) if max(original_lists, corrected_lists) > 0 else 1.0
        
        # Combine metrics
        return 0.7 * paragraph_ratio + 0.3 * list_ratio
    
    def _count_corrections(self, original, corrected):
        """Count the number of corrections made"""
        diff = list(difflib.ndiff(original.splitlines(), corrected.splitlines()))
        corrections = len([line for line in diff if line.startswith('+ ') or line.startswith('- ')])
        return corrections
    
    def add_metrics(self, file_id, original_summary, corrected_summary):
        """Add metrics for a newly corrected summary"""
        metrics = self.calculate_metrics(original_summary, corrected_summary)
        
        new_row = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'file_id': file_id,
            **metrics
        }
        
        self.metrics = pd.concat([self.metrics, pd.DataFrame([new_row])], ignore_index=True)
        self.metrics.to_csv(self.metrics_file, index=False)
        
        return metrics
    
    def generate_trend_report(self):
        """Generate a report showing accuracy trends over time"""
        if len(self.metrics) < 2:
            return "Not enough data to generate trends. Need at least 2 data points."
        
        # Convert date to datetime for time-based analysis
        self.metrics['date'] = pd.to_datetime(self.metrics['date'])
        
        # Group by date (day) and calculate mean scores
        daily_metrics = self.metrics.set_index('date').resample('D').mean()
        
        report = "# Summary Accuracy Trend Report\n\n"
        
        # Overall trend
        first_score = self.metrics.iloc[0]['overall_score']
        last_score = self.metrics.iloc[-1]['overall_score']
        score_change = last_score - first_score
        
        report += f"## Overall Accuracy Trend\n\n"
        report += f"From {self.metrics['date'].min().strftime('%Y-%m-%d')} to {self.metrics['date'].max().strftime('%Y-%m-%d')}:\n"
        report += f"- Starting overall score: {first_score:.2%}\n"
        report += f"- Current overall score: {last_score:.2%}\n"
        report += f"- Change: {score_change:.2%} ({'improvement' if score_change > 0 else 'decline'})\n\n"
        
        # Breakdown by component
        report += "## Component Trends\n\n"
        
        for component in ['sections_accuracy', 'content_accuracy', 'format_accuracy']:
            first = self.metrics.iloc[0][component]
            last = self.metrics.iloc[-1][component]
            change = last - first
            
            report += f"### {component.replace('_', ' ').title()}\n"
            report += f"- Starting: {first:.2%}\n"
            report += f"- Current: {last:.2%}\n"
            report += f"- Change: {change:.2%} ({'improvement' if change > 0 else 'decline'})\n\n"
        
        # Number of corrections needed over time
        avg_corrections_first_half = self.metrics.iloc[:len(self.metrics)//2]['correction_count'].mean()
        avg_corrections_second_half = self.metrics.iloc[len(self.metrics)//2:]['correction_count'].mean()
        correction_change = avg_corrections_second_half - avg_corrections_first_half
        
        report += "## Correction Trend\n\n"
        report += f"- Average corrections needed (first half): {avg_corrections_first_half:.1f}\n"
        report += f"- Average corrections needed (second half): {avg_corrections_second_half:.1f}\n"
        report += f"- Change: {correction_change:.1f} ({'improvement' if correction_change < 0 else 'increase'})\n\n"
        
        report += "## Conclusion\n\n"
        if score_change > 0.05 and correction_change < 0:
            report += "The system is showing significant improvement over time with fewer corrections needed."
        elif score_change > 0:
            report += "The system is improving gradually, but still requires optimization."
        else:
            report += "The system is not showing improvement. Consider revisiting the learning approach."
        
        return report
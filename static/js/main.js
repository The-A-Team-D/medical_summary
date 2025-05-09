/**
 * Main JavaScript file for Medical Summarizer
 */

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // File input change event for showing selected filename
    $('.custom-file-input').on('change', function() {
        var fileName = $(this).val().split('\\').pop();
        $(this).next('.custom-file-label').addClass("selected").html(fileName);
    });
    
    // Highlight navigation based on current page
    highlightNavigation();
    
    // Handle upload area drag and drop
    initializeUploadArea();
    
    // Initialize summary status polling if on summary detail page
    initializeSummaryStatusPolling();
    
    // Initialize diff viewer for feedback page
    initializeDiffViewer();
    
    // Initialize code highlighting
    $('pre code').each(function(i, block) {
        if (typeof hljs !== 'undefined') {
            hljs.highlightBlock(block);
        }
    });
    
    // Add smooth scrolling to anchor links
    $('a[href^="#"]').on('click', function(event) {
        event.preventDefault();
        $('html, body').animate({
            scrollTop: $($.attr(this, 'href')).offset().top - 70
        }, 500);
    });
    
    // Add fade-in animation to cards
    animateContent();
});

/**
 * Highlight the current navigation item based on URL
 */
function highlightNavigation() {
    const currentPath = window.location.pathname;
    
    $('.navbar-nav .nav-link').each(function() {
        const navLink = $(this).attr('href');
        
        // Check if the current path starts with this nav link
        if (currentPath === navLink || 
            (navLink !== '/' && currentPath.startsWith(navLink))) {
            $(this).addClass('active');
        } else {
            $(this).removeClass('active');
        }
    });
}

/**
 * Initialize drag and drop for upload areas
 */
function initializeUploadArea() {
    const uploadArea = $('.upload-area');
    if (uploadArea.length === 0) return;
    
    // Prevent default browser behavior for drag events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.on(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
        });
    });
    
    // Add/remove dragover class
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.on(eventName, function() {
            $(this).addClass('dragover');
        });
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.on(eventName, function() {
            $(this).removeClass('dragover');
        });
    });
    
    // Handle file drop
    uploadArea.on('drop', function(e) {
        const files = e.originalEvent.dataTransfer.files;
        const fileInput = $(this).find('input[type="file"]');
        
        // Update the file input with the dropped file
        fileInput[0].files = files;
        fileInput.trigger('change');
    });
}

/**
 * Poll for summary status updates
 */
function initializeSummaryStatusPolling() {
    const summaryStatusElement = $('#summary-status');
    if (summaryStatusElement.length === 0) return;
    
    const summaryId = summaryStatusElement.data('summary-id');
    const statusUrl = `/api/summary-status/${summaryId}/`;
    
    if (!summaryId) return;
    
    function checkStatus() {
        $.ajax({
            url: statusUrl,
            type: 'GET',
            dataType: 'json',
            success: function(data) {
                // Update the status
                summaryStatusElement.text(data.status);
                
                // If completed or error, reload the page
                if (data.status === 'completed' || data.status === 'corrected' || data.status === 'error') {
                    window.location.reload();
                } else {
                    // Otherwise, check again in 3 seconds
                    setTimeout(checkStatus, 3000);
                }
            },
            error: function() {
                // If error, try again in 5 seconds
                setTimeout(checkStatus, 5000);
            }
        });
    }
    
    // Start polling if the summary is pending or processing
    const currentStatus = summaryStatusElement.text().trim().toLowerCase();
    if (currentStatus === 'pending' || currentStatus === 'processing') {
        checkStatus();
    }
}

/**
 * Initialize diff viewer for the feedback page
 */
function initializeDiffViewer() {
    const originalText = $('#original-text');
    const correctedText = $('#corrected-text');
    
    if (originalText.length === 0 || correctedText.length === 0) return;
    
    // Function to highlight differences
    function highlightDifferences() {
        const original = originalText.val();
        const corrected = correctedText.val();
        
        // Use diff library if available, otherwise basic diff
        if (typeof Diff !== 'undefined') {
            const diff = Diff.diffWords(original, corrected);
            let result = '';
            
            diff.forEach(part => {
                const spanClass = part.added ? 'diff-added' : part.removed ? 'diff-removed' : '';
                const spanStart = spanClass ? `<span class="${spanClass}">` : '';
                const spanEnd = spanClass ? '</span>' : '';
                
                result += spanStart + part.value + spanEnd;
            });
            
            $('#diff-view').html(result);
        }
    }
    
    // Run highlighting when textarea changes
    correctedText.on('input', highlightDifferences);
    
    // Initial highlighting
    highlightDifferences();
}

/**
 * Animate content on page load
 */
function animateContent() {
    $('.card').each(function(i) {
        $(this).css('opacity', '0');
        
        $(this).delay(i * 100).animate({
            opacity: 1,
            top: 0
        }, 500);
    });
}

/**
 * Format a date string
 * @param {Date} date - The date to format
 * @returns {string} - Formatted date string
 */
function formatDate(date) {
    if (!date) return '';
    
    const options = { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    return new Date(date).toLocaleDateString('en-US', options);
}

/**
 * Format a number as a percentage
 * @param {number} value - The number to format (0-1)
 * @returns {string} - Formatted percentage string
 */
function formatPercentage(value) {
    return (value * 100).toFixed(2) + '%';
}

/**
 * Truncate a string to a maximum length
 * @param {string} str - The string to truncate
 * @param {number} maxLength - Maximum allowed length
 * @returns {string} - Truncated string
 */
function truncateString(str, maxLength = 100) {
    if (!str || str.length <= maxLength) return str;
    return str.substring(0, maxLength) + '...';
}

/**
 * Handle form submission with input validation
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value) {
            isValid = false;
            
            // Add error styling
            field.classList.add('is-invalid');
            
            // Add error message if not already present
            const errorMessageId = `${field.id}-error`;
            if (!document.getElementById(errorMessageId)) {
                const errorMessage = document.createElement('div');
                errorMessage.id = errorMessageId;
                errorMessage.className = 'invalid-feedback';
                errorMessage.textContent = 'This field is required.';
                field.parentNode.appendChild(errorMessage);
            }
        } else {
            // Remove error styling
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}
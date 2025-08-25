// src/static/js/modules/utils.js
/**
 * Utils Module - Shared utility functions
 */

// Function to copy text to clipboard
export function copyToClipboard(text) {
    // Create temporary element
    const tempElement = document.createElement('textarea');
    tempElement.value = text;
    document.body.appendChild(tempElement);
    
    // Select and copy
    tempElement.select();
    document.execCommand('copy');
    
    // Clean up
    document.body.removeChild(tempElement);
}
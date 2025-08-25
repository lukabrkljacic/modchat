// src/static/js/modules/fileUpload.js
/**
 * File Upload Module - Handles file uploads and management
 */

// Uploaded files tracker
let uploadedFiles = [];

// Set up file upload handling
export function setupFileUpload() {
    const uploadButton = document.getElementById('upload-button');
    const fileUpload = document.getElementById('file-upload');
    
    // File upload handling
    if (uploadButton && fileUpload) {
        uploadButton.addEventListener('click', function() {
            fileUpload.click();
        });
        
        fileUpload.addEventListener('change', function() {
            handleFileUpload(this.files);
        });
    }
}

// Handle file uploads
export function handleFileUpload(files) {
    if (!files || files.length === 0) return;
    
    // Create a preview div if it doesn't exist
    let uploadPreview = document.querySelector('.upload-preview');
    
    if (!uploadPreview) {
        uploadPreview = document.createElement('div');
        uploadPreview.className = 'upload-preview';
        document.querySelector('.input-container').appendChild(uploadPreview);
    }
    
    // Process each file
    Array.from(files).forEach(file => {
        // Create FormData
        const formData = new FormData();
        formData.append('file', file);
        formData.append('userToken', `${window.USER_TOKEN}`)
        
        // Upload file to server
        fetch(`${window.BACKEND_URL}/upload`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Add file to our list
                uploadedFiles.push({
                    name: data.filename,
                    path: data.file_path,
                    supported: data.supported
                });
                
                // Update preview
                updateFilePreview();
            } else {
                console.error('Upload failed:', data.error);
                // Show error to user
                const errorMessage = document.createElement('div');
                errorMessage.className = 'error-message';
                errorMessage.textContent = `Upload failed: ${data.error}`;
                uploadPreview.appendChild(errorMessage);
            }
        })
        .catch(error => {
            console.error('Error uploading file:', error);
        });
    });
}

// Update the file preview display
export function updateFilePreview() {
    const uploadPreview = document.querySelector('.upload-preview');
    
    if (!uploadPreview) return;
    
    // Clear existing preview
    uploadPreview.innerHTML = '';
    
    // Add each file
    uploadedFiles.forEach((file, index) => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        // Add icon based on support status
        const icon = document.createElement('i');
        icon.className = file.supported ? 'fas fa-file-alt' : 'fas fa-file-excel';
        fileItem.appendChild(icon);
        
        // Add file name
        const fileName = document.createElement('span');
        fileName.textContent = file.name;
        fileItem.appendChild(fileName);
        
        // Add remove button
        const removeButton = document.createElement('span');
        removeButton.className = 'remove-file';
        removeButton.innerHTML = '&times;';
        removeButton.addEventListener('click', function() {
            uploadedFiles.splice(index, 1);
            updateFilePreview();
        });
        fileItem.appendChild(removeButton);
        
        // Add to preview
        uploadPreview.appendChild(fileItem);
    });
    
    // Hide preview if no files
    if (uploadedFiles.length === 0 && uploadPreview.parentNode) {
        uploadPreview.parentNode.removeChild(uploadPreview);
    }
}

// Get the currently uploaded files
export function getUploadedFiles() {
    return [...uploadedFiles]; // Return a copy of the files array
}

// Clear all uploaded files
export function clearUploadedFiles() {
    uploadedFiles = [];
    updateFilePreview();
}
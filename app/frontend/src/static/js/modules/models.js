// src/static/js/modules/models.js
/**
 * Models Module - Handles model selection and tracking
 */

// Exported model state
export let selectedModel = {
    vendor: '',
    id: '',
    name: 'Select a Model'
};

// Initialize model selector and related UI
export function initializeModelSelector() {
    // DOM Elements
    const modelDropdownButton = document.getElementById('model-dropdown-button');
    const modelDropdown = document.getElementById('model-dropdown');
    const vendorHeaders = document.querySelectorAll('.vendor-header');
    const modelOptions = document.querySelectorAll('.model-option');
    const selectedModelDisplay = document.getElementById('selected-model-display');
    
    // Model selector dropdown
    if (modelDropdownButton && modelDropdown) {
        modelDropdownButton.addEventListener('click', function(e) {
            modelDropdown.classList.toggle('active');
            e.stopPropagation(); // Prevent event from bubbling up
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        // Only close the model dropdown if clicking outside of it and its button
        if (modelDropdown && !modelDropdownButton.contains(e.target) && !modelDropdown.contains(e.target)) {
            modelDropdown.classList.remove('active');
        }
    });
    
    // Vendor headers toggle
    vendorHeaders.forEach(header => {
        header.addEventListener('click', function(e) {
            const vendorId = this.getAttribute('data-vendor-id');
            const modelsContainer = document.getElementById(`vendor-${vendorId}-models`);
            
            // Close all other vendor models
            document.querySelectorAll('.vendor-models').forEach(el => {
                if (el.id !== `vendor-${vendorId}-models`) {
                    el.classList.remove('active');
                }
            });
            
            document.querySelectorAll('.vendor-header').forEach(el => {
                if (el !== this) {
                    el.classList.remove('active');
                }
            });
            
            // Toggle this vendor's models
            this.classList.toggle('active');
            if (modelsContainer) {
                modelsContainer.classList.toggle('active');
            }
            
            // Prevent event bubbling to avoid closing the dropdown
            e.stopPropagation();
        });
    });
    
    // Model options selection
    modelOptions.forEach(option => {
        option.addEventListener('click', function(e) {
            // Remove selected class from all options
            modelOptions.forEach(opt => opt.classList.remove('selected'));
            
            // Add selected class to this option
            this.classList.add('selected');
            
            // Update the selected model
            selectedModel.vendor = this.getAttribute('data-vendor');
            selectedModel.id = this.getAttribute('data-model-id');
            selectedModel.name = this.getAttribute('data-model-name');
            
            if (selectedModelDisplay) {
                selectedModelDisplay.textContent = `${selectedModel.vendor}: ${selectedModel.name}`;
            }
            if (modelDropdown) {
                modelDropdown.classList.remove('active');
            }

            // Remove model selection warning if present
            const chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                chatContainer.querySelectorAll('.system-message').forEach(msg => {
                    if (msg.textContent.includes('Please select a model before sending a message.')) {
                        msg.remove();
                    }
                });
            }

            // Prevent event from bubbling up
            e.stopPropagation();
        });
    });
}

// Get the currently selected model
export function getSelectedModel() {
    return selectedModel;
}
// src/static/js/modules/settings.js
/**
 * Settings Module - Handles app settings and configurations
 */

import { logEvent } from './tracking.js';

// Current settings state
let settings = {
    systemPrompt: 'You are a helpful AI assistant.',
    responseFormat: '{}',
    contextLength: 4000,
    temperature: 0.7,
    topK: 40,
    chunkSize: 1000,
    advancedMode: false,
    decomposeMode: false  // Added decompose toggle state
};

// Initialize settings controls and sliders
export function initializeSettings() {
    // DOM Elements
    const systemPromptEditor = document.getElementById('system-prompt');
    const structuredOutputEditor = document.getElementById('structured-output');
    
    // Sliders
    const contextLengthSlider = document.getElementById('context-length-slider');
    const contextLengthValue = document.getElementById('context-length-value');
    const temperatureSlider = document.getElementById('temperature-slider');
    const temperatureValue = document.getElementById('temperature-value');
    const topKSlider = document.getElementById('top-k-slider');
    const topKValue = document.getElementById('top-k-value');
    const chunkSizeSlider = document.getElementById('chunk-size-slider');
    const chunkSizeValue = document.getElementById('chunk-size-value');
    
    // Toggle switches
    const advancedModeToggle = document.getElementById('advanced-mode-toggle');
    const decomposeToggle = document.getElementById('decompose-toggle');
    
    // Initialize system prompt editor
    if (systemPromptEditor) {
        // Set initial value from settings
        systemPromptEditor.value = settings.systemPrompt;
        
        // Add event listener for changes
        systemPromptEditor.addEventListener('change', function() {
            settings.systemPrompt = this.value;
        });
        
        systemPromptEditor.addEventListener('click', function(e) {
            // Prevent event bubbling when clicking in the editor
            e.stopPropagation();
        });
    }
    
    // Initialize structured output editor
    if (structuredOutputEditor) {
        // Set initial value from settings
        structuredOutputEditor.value = settings.responseFormat;
        
        // Add event listener for changes
        structuredOutputEditor.addEventListener('change', function() {
            settings.responseFormat = this.value;
        });
        
        structuredOutputEditor.addEventListener('click', function(e) {
            // Prevent event bubbling when clicking in the editor
            e.stopPropagation();
        });
    }
    
    // Initialize sliders
    if (contextLengthSlider && contextLengthValue) {
        // Set initial values
        contextLengthSlider.value = settings.contextLength;
        contextLengthValue.textContent = settings.contextLength;
        
        // Add event listener for changes
        contextLengthSlider.addEventListener('input', function() {
            contextLengthValue.textContent = this.value;
            settings.contextLength = parseInt(this.value);
        });
    }
    
    if (temperatureSlider && temperatureValue) {
        // Set initial values
        temperatureSlider.value = settings.temperature;
        temperatureValue.textContent = settings.temperature;
        
        // Add event listener for changes
        temperatureSlider.addEventListener('input', function() {
            temperatureValue.textContent = this.value;
            settings.temperature = parseFloat(this.value);
        });
    }
    
    if (topKSlider && topKValue) {
        // Set initial values
        topKSlider.value = settings.topK;
        topKValue.textContent = settings.topK;
        
        // Add event listener for changes
        topKSlider.addEventListener('input', function() {
            topKValue.textContent = this.value;
            settings.topK = parseInt(this.value);
        });
    }
    
    if (chunkSizeSlider && chunkSizeValue) {
        // Set initial values
        chunkSizeSlider.value = settings.chunkSize;
        chunkSizeValue.textContent = settings.chunkSize;
        
        // Add event listener for changes
        chunkSizeSlider.addEventListener('input', function() {
            chunkSizeValue.textContent = this.value;
            settings.chunkSize = parseInt(this.value);
        });
    }
    
    // Initialize decompose toggle
    if (decomposeToggle) {
        // Set initial value from settings
        decomposeToggle.checked = settings.decomposeMode;

        // Add event listener for changes
        decomposeToggle.addEventListener('change', function() {
            settings.decomposeMode = this.checked;

            logEvent(null, 'decompose_toggled', { enabled: this.checked });
        });
    }
}

// Update a specific setting
export function updateSetting(key, value) {
    if (key in settings) {
        settings[key] = value;
        return true;
    }
    return false;
}

// Get all current settings
export function getSettings() {
    // If we're in advanced mode, make sure to pull the latest values from the editors
    const systemPromptEditor = document.getElementById('system-prompt');
    const structuredOutputEditor = document.getElementById('structured-output');
    const advancedModeToggle = document.getElementById('advanced-mode-toggle');
    const decomposeToggle = document.getElementById('decompose-toggle');
    
    if (advancedModeToggle && advancedModeToggle.checked) {
        if (systemPromptEditor) {
            settings.systemPrompt = systemPromptEditor.value;
        }
        if (structuredOutputEditor) {
            settings.responseFormat = structuredOutputEditor.value;
        }
    }
    
    settings.advancedMode = advancedModeToggle ? advancedModeToggle.checked : false;
    settings.decomposeMode = decomposeToggle ? decomposeToggle.checked : false;
    
    return { ...settings, userToken: `${window.USER_TOKEN}` }; // Return a copy of the settings object
}

// Save settings to backend
export function saveSettings() {
    return fetch(`${window.BACKEND_URL}/save_settings`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(getSettings())
    })
    .then(response => response.json())
    .then(data => {
        return data;
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        throw error;
    });
}
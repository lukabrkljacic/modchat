// src/static/js/main.js

/**
 * Main entry point for the Component-Based LLM Chat Interface.
 * This file loads all the module dependencies and initializes the application.
 */

// Import all required modules
import { setupUIComponents } from './modules/ui.js';
import { initializeModelSelector } from './modules/models.js';
import { initializeSettings, getSettings } from './modules/settings.js';
import { setupMessageHandlers } from './modules/messaging.js';
import { setupFileUpload } from './modules/fileUpload.js';
import { processAIResponse, generateFinalOutput } from './modules/components.js';
import { copyToClipboard } from './modules/utils.js';
import { logEvent, initSession } from './modules/tracking.js';
import { setupFeedback } from './modules/feedback.js';

// Make core functions globally available for event handlers
window.generateFinalOutput = generateFinalOutput;
window.copyToClipboard = copyToClipboard;
window.logEvent = logEvent;

// Main initialization function
document.addEventListener('DOMContentLoaded', function() {
    console.log("Initializing Component-Based LLM Chat Interface");

    // Start a new session for this page load
    initSession();
    
    // Initialize core UI components (sidebar, mobile controls, etc.)
    setupUIComponents();
    
    // Initialize model selector
    initializeModelSelector();
    
    // Initialize settings controls
    initializeSettings();
    
    // Initialize message handling
    setupMessageHandlers();
    
    // Initialize file upload handling
    setupFileUpload();

    // Initialize feedback widget
    setupFeedback();
    
    console.log("Application initialization complete");
});
// src/static/js/modules/messaging.js
/**
 * Messaging Module - Handles sending and receiving messages
 */

import { getSelectedModel } from './models.js';
import { getSettings } from './settings.js';
import { getUploadedFiles, clearUploadedFiles } from './fileUpload.js';
import { processAIResponse } from './components.js';
import { logEvent, getSessionId } from './tracking.js';

// Chat conversation counter for unique IDs
let conversationCounter = parseInt(localStorage.getItem('conversationCounter') || '0', 10);

// Set up message sending and related event handlers
export function setupMessageHandlers() {
    // DOM Elements
    const chatInput = document.getElementById('chat-input');
    const chatContainer = document.getElementById('chat-container');
    const sendButton = document.getElementById('send-button');
    
    // Send message on Enter key
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    }
    
    // Send message on send button click
    if (sendButton) {
        sendButton.addEventListener('click', function() {
            sendMessage();
        });
    }
}

// Send user message to backend
export function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const chatContainer = document.getElementById('chat-container');
    
    const message = chatInput.value.trim();

    if (!message) return;
    
    // Get the current selected model
    const model = getSelectedModel();
    
    // Check if a model is selected
    if (!model.id) {
        appendSystemMessage('Please select a model before sending a message.');
        return;
    }
    
    // Create a new conversation group
    conversationCounter++;
    localStorage.setItem('conversationCounter', conversationCounter);
    const conversationId = `conversation-${conversationCounter}`;

    // Log the user sending a message
    logEvent(conversationId, 'message_sent', { length: message.length });
    
    // Create the message group
    const messageGroup = createMessageGroup(conversationId, message);
    // Store model info for later regenerations
    messageGroup.dataset.modelId = model.id;
    messageGroup.dataset.vendor = model.vendor;
    chatContainer.appendChild(messageGroup);
    
    // Clear input
    chatInput.value = '';
    
    // Get current settings and files
    const currentSettings = getSettings();
    const uploadedFiles = getUploadedFiles();
    
    // Send to backend
    fetch(`${window.BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            model: model.id,
            vendor: model.vendor,
            settings: currentSettings,
            files: uploadedFiles,
            decompose: currentSettings.decomposeMode, // Include decompose flag
            conversation_id: conversationId,
            session_id: getSessionId(),
            userToken: `${window.USER_TOKEN}`
        })
    })
    .then(response => response.json())
    .then(data => {
        // Store conversation id returned from backend
        if (data.conversation_id) {
            messageGroup.dataset.conversationId = data.conversation_id;
        }

        // Process and add AI response components
        processAIResponse(conversationId, data);
        
        // Clear uploaded files after message is sent
        clearUploadedFiles();
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
        appendSystemMessage('An error occurred while processing your request.');
    });
}

// Create a new message group with four columns (no system prompt column)
export function createMessageGroup(id, userMessage) {
    const settings = getSettings();
    const messageGroup = document.createElement('div');
    messageGroup.className = 'message-group';
    messageGroup.id = id;
    
    // Create second column for user prompt
    const userColumn = document.createElement('div');
    userColumn.className = 'user-column';
    
    // User prompt component with header
    const userPrompt = document.createElement('div');
    userPrompt.className = 'user-prompt';
    
    // User prompt header
    const userPromptHeader = document.createElement('div');
    userPromptHeader.className = 'bubble-header';
    userPromptHeader.textContent = 'User Prompt';
    
    // User prompt actions container (no edit button)
    const userPromptActions = document.createElement('div');
    userPromptActions.className = 'bubble-actions';

    userPromptHeader.appendChild(userPromptActions);
    userPrompt.appendChild(userPromptHeader);
    
    // User prompt content
    const userPromptContent = document.createElement('div');
    userPromptContent.className = 'bubble-content';
    userPromptContent.textContent = userMessage;
    userPrompt.appendChild(userPromptContent);
    
    // Add user prompt to second column
    userColumn.appendChild(userPrompt);
    
    // Create third column for main response
    const responseColumn = document.createElement('div');
    responseColumn.className = 'response-column';
    
    // Add loading indicator for response
    const loadingResponse = document.createElement('div');
    loadingResponse.className = 'main-response';
    
    // Response header
    const responseHeader = document.createElement('div');
    responseHeader.className = 'bubble-header';
    responseHeader.textContent = 'Chatbot Response';
    loadingResponse.appendChild(responseHeader);
    
    // Response content with loading indicator
    const responseContent = document.createElement('div');
    responseContent.className = 'bubble-content';
    responseContent.innerHTML = 'Generating response... <i class="fas fa-spinner fa-spin"></i>';
    loadingResponse.appendChild(responseContent);
    
    responseColumn.appendChild(loadingResponse);
    
    // Add action buttons container with Decompose button
    const actionButtonsContainer = document.createElement('div');
    actionButtonsContainer.className = 'action-buttons-container';
    
    // Decompose button
    const decomposeButton = document.createElement('button');
    decomposeButton.className = 'decompose-button';
    decomposeButton.id = `decompose-response-${id}`;
    decomposeButton.innerHTML = '<i class="fas fa-sitemap"></i> Decompose';
    
    actionButtonsContainer.appendChild(decomposeButton);
    responseColumn.appendChild(actionButtonsContainer);
    
    // Create fourth column for components
    const componentsColumn = document.createElement('div');
    componentsColumn.className = 'components-column';

    // Components header with toggle
    const componentsHeader = document.createElement('div');
    componentsHeader.className = 'components-header';
    componentsHeader.textContent = 'Components';

    const componentsHeaderActions = document.createElement('div');
    const componentsToggle = document.createElement('i');
    componentsToggle.className = 'fas fa-chevron-up components-toggle';
    componentsToggle.title = 'Collapse';
    componentsHeaderActions.appendChild(componentsToggle);
    componentsHeader.appendChild(componentsHeaderActions);
    componentsColumn.appendChild(componentsHeader);

    const componentsList = document.createElement('div');
    componentsList.className = 'components-list';
    componentsColumn.appendChild(componentsList);

    // Create fifth column for final output
    const finalOutputColumn = document.createElement('div');
    finalOutputColumn.className = 'final-output-column';
    
    // Create final output container
    const finalOutput = document.createElement('div');
    finalOutput.className = 'final-output';
    
    // Final output header
    const finalOutputHeader = document.createElement('div');
    finalOutputHeader.className = 'bubble-header';
    finalOutputHeader.textContent = 'Final Output';
    
    // Final output actions
    const finalOutputActions = document.createElement('div');
    finalOutputActions.className = 'bubble-actions';
    
    const finalOutputEdit = document.createElement('i');
    finalOutputEdit.className = 'fas fa-edit bubble-action';
    finalOutputEdit.title = 'Edit';
    finalOutputActions.appendChild(finalOutputEdit);
    
    const finalOutputCopy = document.createElement('i');
    finalOutputCopy.className = 'fas fa-copy bubble-action';
    finalOutputCopy.title = 'Copy to clipboard';
    finalOutputActions.appendChild(finalOutputCopy);
    
    finalOutputHeader.appendChild(finalOutputActions);
    finalOutput.appendChild(finalOutputHeader);
    
    // Final output content
    const finalOutputContent = document.createElement('div');
    finalOutputContent.className = 'bubble-content';
    finalOutputContent.textContent = '';
    finalOutput.appendChild(finalOutputContent);
    
    finalOutputColumn.appendChild(finalOutput);
    
    // Create column resizers
    const resizer1 = document.createElement('div');
    resizer1.className = 'column-resizer';
    resizer1.dataset.index = '1';

    const resizer2 = document.createElement('div');
    resizer2.className = 'column-resizer';
    resizer2.dataset.index = '2';

    const resizer3 = document.createElement('div');
    resizer3.className = 'column-resizer';
    resizer3.dataset.index = '3';

    // Add all columns and resizers to message group (no system column)
    messageGroup.appendChild(userColumn);
    messageGroup.appendChild(resizer1);
    messageGroup.appendChild(responseColumn);
    messageGroup.appendChild(resizer2);
    messageGroup.appendChild(componentsColumn);
    messageGroup.appendChild(resizer3);
    messageGroup.appendChild(finalOutputColumn);
    
    return messageGroup;
}

// Append a system message for errors and notifications
export function appendSystemMessage(message) {
    const chatContainer = document.getElementById('chat-container');
    
    if (!chatContainer) return;
    
    const systemMessage = document.createElement('div');
    systemMessage.className = 'system-message';
    systemMessage.textContent = message;
    
    chatContainer.appendChild(systemMessage);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
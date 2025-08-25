// src/static/js/modules/decompose.js
/**
 * Decompose Module - Handles decomposition of AI responses into components
 */

import { processAIResponse } from './components.js';

// Decompose state
let decomposeEnabled = true;

// Initialize decompose toggle and related functionality
export function initializeDecompose() {
    const decomposeToggle = document.getElementById('decompose-output-toggle');
    
    if (decomposeToggle) {
        // Set initial state
        decomposeToggle.checked = decomposeEnabled;
        
        // Add event listener
        decomposeToggle.addEventListener('change', function() {
            decomposeEnabled = this.checked;
            console.log('Decompose output setting changed to:', decomposeEnabled);
        });
    }
}

// Get decompose setting
export function isDecomposeEnabled() {
    return decomposeEnabled;
}

// Set decompose setting
export function setDecomposeEnabled(enabled) {
    decomposeEnabled = enabled;
    const decomposeToggle = document.getElementById('decompose-output-toggle');
    if (decomposeToggle) {
        decomposeToggle.checked = enabled;
    }
}

// Add decompose button to response column
export function addDecomposeButton(responseColumn, conversationId) {
    // Check if button container already exists
    let buttonContainer = responseColumn.querySelector('.action-buttons-container');
    
    if (!buttonContainer) {
        buttonContainer = document.createElement('div');
        buttonContainer.className = 'action-buttons-container';
        responseColumn.appendChild(buttonContainer);
    }
    
    // Check if decompose button already exists
    if (buttonContainer.querySelector('.decompose-button')) {
        return; // Button already exists
    }
    
    // Create decompose button
    const decomposeBtn = document.createElement('button');
    decomposeBtn.className = 'decompose-button';
    decomposeBtn.innerHTML = '<i class="fas fa-project-diagram"></i> Decompose';
    
    // Add event listener
    decomposeBtn.addEventListener('click', async () => {
        await decomposeResponse(conversationId);
    });
    
    // Add button to container
    buttonContainer.appendChild(decomposeBtn);
}

// Decompose an existing AI response
export async function decomposeResponse(conversationId) {
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) {
        console.error('Message group not found:', conversationId);
        return;
    }
    
    // Get the main response content
    const responseContent = messageGroup.querySelector('.main-response .bubble-content');
    if (!responseContent) {
        console.error('Response content not found');
        return;
    }
    
    const rawText = responseContent.textContent.trim();
    if (!rawText) {
        console.error('No content to decompose');
        return;
    }
    
    // Show loading state on decompose button
    const decomposeBtn = messageGroup.querySelector('.decompose-button');
    if (decomposeBtn) {
        const originalText = decomposeBtn.innerHTML;
        decomposeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Decomposing...';
        decomposeBtn.disabled = true;
        
        try {
            // Send decompose request to backend
            const conversationId = `conversation-${localStorage.getItem("conversationCounter")}`
            const response = await fetch(`${window.MOD_AGENT_URL}/${window.DECOMPOSE_ENDPOINT}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ response: rawText, userToken: `${window.USER_TOKEN}`, conversation_id: conversationId})
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Decomposition failed:', data.error);
                alert('Failed to decompose response: ' + data.error);
            } else {
                // Process the decomposed response
                processAIResponse(conversationId, data);
                
                // Hide the decompose button since we now have components
                decomposeBtn.style.display = 'none';
            }
        } catch (error) {
            console.error('Error during decomposition:', error);
            alert('An error occurred during decomposition');
        } finally {
            // Restore button state
            decomposeBtn.innerHTML = originalText;
            decomposeBtn.disabled = false;
        }
    }
}

// Render simple response without decomposition
export function renderSimpleResponse(conversationId, aiMessage) {
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) return;
    
    const responseColumn = messageGroup.querySelector('.response-column');
    if (!responseColumn) return;
    
    const mainResponse = responseColumn.querySelector('.main-response');
    if (!mainResponse) return;
    
    const bubbleHeader = mainResponse.querySelector('.bubble-header');
    const bubbleContent = mainResponse.querySelector('.bubble-content');
    
    if (!bubbleHeader || !bubbleContent) return;
    
    // Update response content
    bubbleHeader.textContent = 'Chatbot Response';
    bubbleContent.innerHTML = marked.parse(aiMessage);
    
    // Add response actions to header if not already present
    if (!bubbleHeader.querySelector('.bubble-actions')) {
        const responseActions = document.createElement('div');
        responseActions.className = 'bubble-actions';
        
        const responseEdit = document.createElement('i');
        responseEdit.className = 'fas fa-edit bubble-action';
        responseEdit.title = 'Edit';
        responseActions.appendChild(responseEdit);
        
        const responseExpand = document.createElement('i');
        responseExpand.className = 'fas fa-chevron-up bubble-action';
        responseExpand.title = 'Collapse';
        responseActions.appendChild(responseExpand);
        
        bubbleHeader.appendChild(responseActions);
    }
    
    // Clean up any existing button containers
    const oldButtonContainer = responseColumn.querySelector('.action-buttons-container');
    if (oldButtonContainer) {
        oldButtonContainer.remove();
    }
    
    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'action-buttons-container';

    // Add Decompose button
    const decomposeBtn = document.createElement('button');
    decomposeBtn.className = 'decompose-button';
    decomposeBtn.innerHTML = '<i class="fas fa-project-diagram"></i> Decompose';
    decomposeBtn.addEventListener('click', async () => {
        await decomposeResponse(conversationId);
    });
    
    // Add button to container
    buttonContainer.appendChild(generateBtn);
    buttonContainer.appendChild(decomposeBtn);
    responseColumn.appendChild(buttonContainer);
}
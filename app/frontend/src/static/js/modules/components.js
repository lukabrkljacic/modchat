// src/static/js/modules/components.js
/**
 * Components Module - Handles AI component rendering and management
 */

import { copyToClipboard } from './utils.js';
import { logEvent } from './tracking.js';

// Convert AI response into component structures
export function processAIResponse(conversationId, data) {
    console.log("Processing AI response:", data);
    
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) {
        console.error("Message group not found:", conversationId);
        return;
    }

    // Store model info and conversation id for future actions
    if (data.model) {
        messageGroup.dataset.modelId = data.model;
    }
    if (data.vendor) {
        messageGroup.dataset.vendor = data.vendor;
    }
    if (data.conversation_id) {
        messageGroup.dataset.conversationId = data.conversation_id;
    }
    
    // Update main response in the middle column
    const responseColumn = messageGroup.querySelector('.response-column');
    if (!responseColumn) {
        console.error("Response column not found");
        return;
    }
    
    const loadingResponse = responseColumn.querySelector('.main-response');
    if (!loadingResponse) {
        console.error("Main response element not found");
        return;
    }
    
    // Update the response content
    const responseContent = loadingResponse.querySelector('.bubble-content');
    if (!responseContent) {
        console.error("Response content element not found");
        return;
    }
    
    responseContent.innerHTML = '';
    
    // Set the main response text
    if (data.text && typeof data.text === 'string') {
        responseContent.innerHTML = marked.parse(data.text);
        console.log("Main response set successfully");
    }
    
    // Get the components column and list
    const componentsColumn = messageGroup.querySelector('.components-column');
    if (!componentsColumn) {
        console.error("Components column not found");
        return;
    }

    const componentsList = componentsColumn.querySelector('.components-list');
    if (!componentsList) {
        console.error("Components list not found");
        return;
    }

    // Clear any existing components or loading indicators
    componentsList.innerHTML = '';
    console.log("Cleared existing components");
    
    // Handle the components - keep them as an array
    let componentsArr = [];
    
    // Handle the new array format
    if (data.components && Array.isArray(data.components)) {
        console.log("Processing array components format");
        componentsArr = data.components;
    }
    // Handle the old object format for backward compatibility
    else if (data.components && typeof data.components === 'object') {
        console.log("Processing object components format");
        componentsArr = Object.keys(data.components).map(key => ({[key]: data.components[key]}));
    }
    
    console.log("Extracted components array:", componentsArr);
    
    // Store output type and structure
    if (data.outputType) {
        messageGroup.dataset.outputType = data.outputType;
    }
    
    let outputStructure = [];
    if (data.outputStructure && Array.isArray(data.outputStructure)) {
        outputStructure = data.outputStructure;
        messageGroup.dataset.outputStructure = JSON.stringify(outputStructure);
    } else {
        outputStructure = componentsArr.map(obj => Object.keys(obj)[0]);
    }
    
    // Now add each component to the UI preserving order
    if (componentsArr.length > 0) {
        console.log("Building component elements");

        componentsArr.forEach(componentObj => {
            const key = Object.keys(componentObj)[0];
            const value = componentObj[key];
            addComponentToUI(componentsColumn, key, value);
        });

        console.log(`Total of ${componentsList.children.length} components rendered`);
    } else {
        // No components found - add a placeholder
        console.log("No components found - adding placeholder");
        addPlaceholderComponent(componentsList);
    }
    
    // Add response actions to header
    const responseHeader = loadingResponse.querySelector('.bubble-header');
    if (responseHeader) {
        // Create actions
        const responseActions = document.createElement('div');
        responseActions.className = 'bubble-actions';

        const responseEdit = document.createElement('i');
        responseEdit.className = 'fas fa-edit bubble-action';
        responseEdit.title = 'Edit';
        responseActions.appendChild(responseEdit);

        const responseRegenerate = document.createElement('i');
        responseRegenerate.className = 'fas fa-sync-alt bubble-action';
        responseRegenerate.title = 'Regenerate';
        responseActions.appendChild(responseRegenerate);

        const responseExpand = document.createElement('i');
        responseExpand.className = 'fas fa-chevron-up bubble-action';
        responseExpand.title = 'Collapse';
        responseActions.appendChild(responseExpand);
        
        // Clear existing actions if any
        const headerText = responseHeader.childNodes[0];
        responseHeader.innerHTML = '';
        responseHeader.appendChild(headerText);
        responseHeader.appendChild(responseActions);
    }
    
    // Update decompose button click handler
    const decomposeButton = responseColumn.querySelector('.decompose-button');
    if (decomposeButton) {
        decomposeButton.addEventListener('click', function() {
            decomposeResponse(conversationId);
        });
    }
}

// Add a single component to the UI
function addComponentToUI(container, key, value) {
    console.log(`Adding component: "${key}"`);
    
    // Create component element
    const component = document.createElement('div');
    component.className = 'component';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'component-header';
    
    // Format the display name
    const displayName = key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
    
    header.textContent = displayName;
    
    // Create actions container
    const actions = document.createElement('div');
    actions.className = 'component-actions';

    // Add checkmark button
    const checkBtn = document.createElement('i');
    checkBtn.className = 'fas fa-check-circle component-action component-check';
    checkBtn.title = 'Accept Component';
    actions.appendChild(checkBtn);

    // Add delete button
    const deleteBtn = document.createElement('i');
    deleteBtn.className = 'fas fa-trash component-action component-delete';
    deleteBtn.title = 'Delete Component';
    actions.appendChild(deleteBtn);

    // Add edit button
    const editBtn = document.createElement('i');
    editBtn.className = 'fas fa-edit component-action component-edit';
    editBtn.title = 'Edit';
    actions.appendChild(editBtn);

    // Add regenerate button
    const regenBtn = document.createElement('i');
    regenBtn.className = 'fas fa-sync-alt component-action component-regenerate';
    regenBtn.title = 'Regenerate';
    actions.appendChild(regenBtn);

    // Add expand button
    const expandBtn = document.createElement('i');
    expandBtn.className = 'fas fa-chevron-up component-action component-expand';
    expandBtn.title = 'Collapse';
    actions.appendChild(expandBtn);
    
    header.appendChild(actions);
    component.appendChild(header);
    
    // Create content element
    const contentElement = document.createElement('div');
    contentElement.className = 'component-content';
    contentElement.innerHTML = marked.parse(value);
    component.appendChild(contentElement);
    
    // Add the component to the column
    container.appendChild(component);
    console.log(`Component "${key}" added to UI`);
}

// Check how many valid components exist in the message group
function getValidComponents(messageGroup) {
    const components = Array.from(messageGroup.querySelectorAll('.components-column .component'));
    return components.filter(comp => {
        const headerText = comp.querySelector('.component-header')?.textContent.trim();
        return headerText && !['Decomposing Response', 'Decomposition Error', 'No Components Found'].includes(headerText);
    });
}

// Determine if all valid components have been checked
function areAllComponentsChecked(messageGroup) {
    const valid = getValidComponents(messageGroup);
    if (valid.length === 0) return false;
    return valid.every(comp => comp.querySelector('.component-check')?.classList.contains('checked'));
}

// Called when components are modified (checked/unchecked or deleted)
export function onComponentStateChange(conversationId) {
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) return;
    generateFinalOutput(conversationId);
}

// Add a placeholder component when no components are found
function addPlaceholderComponent(container) {
    // Create component element
    const component = document.createElement('div');
    component.className = 'component';
    
    // Create header
    const header = document.createElement('div');
    header.className = 'component-header';
    header.textContent = "No Components Found";
    
    // Create actions container
    const actions = document.createElement('div');
    actions.className = 'component-actions';
    
    // Add edit button
    const editBtn = document.createElement('i');
    editBtn.className = 'fas fa-edit component-action component-edit';
    editBtn.title = 'Edit';
    actions.appendChild(editBtn);

    // Add regenerate button
    const regenBtn = document.createElement('i');
    regenBtn.className = 'fas fa-sync-alt component-action component-regenerate';
    regenBtn.title = 'Regenerate';
    actions.appendChild(regenBtn);

    // Add expand button
    const expandBtn = document.createElement('i');
    expandBtn.className = 'fas fa-chevron-up component-action component-expand';
    expandBtn.title = 'Collapse';
    actions.appendChild(expandBtn);
    
    header.appendChild(actions);
    component.appendChild(header);
    
    // Create content element
    const contentElement = document.createElement('div');
    contentElement.className = 'component-content';
    contentElement.innerHTML = marked.parse("The model response did not include structured components.");
    component.appendChild(contentElement);
    
    // Add the placeholder to the column
    container.appendChild(component);
}

// Add loading indicator for decomposition
function showDecompositionLoading(container) {
    container.innerHTML = '';
    
    const loadingComponent = document.createElement('div');
    loadingComponent.className = 'component decomposition-loading';
    
    const header = document.createElement('div');
    header.className = 'component-header';
    header.textContent = 'Decomposing Response';
    loadingComponent.appendChild(header);
    
    const content = document.createElement('div');
    content.className = 'component-content';
    content.innerHTML = 'Breaking down response into components... <i class="fas fa-spinner fa-spin"></i>';
    loadingComponent.appendChild(content);
    
    container.appendChild(loadingComponent);
}

// Add error message for failed decomposition
function showDecompositionError(container, errorMessage) {
    // Only add error if there are no existing components
    if (container.children.length === 0) {
        const errorComponent = document.createElement('div');
        errorComponent.className = 'component decomposition-error';
        
        const header = document.createElement('div');
        header.className = 'component-header';
        header.textContent = 'Decomposition Error';
        errorComponent.appendChild(header);
        
        const content = document.createElement('div');
        content.className = 'component-content';
        content.textContent = `Failed to decompose response: ${errorMessage}`;
        errorComponent.appendChild(content);
        
        container.appendChild(errorComponent);
    }
}

// Decompose response function (called by button click)
export function decomposeResponse(conversationId) {
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) {
        console.error("Message group not found:", conversationId);
        return;
    }

    // Record the button click
    logEvent(conversationId, 'decompose_clicked');
    
    // Get the main response text
    const responseContent = messageGroup.querySelector('.main-response .bubble-content');
    if (!responseContent) {
        console.error("Response content not found");
        return;
    }
    
    const responseText = responseContent.textContent;
    if (!responseText) {
        console.error("No response text to decompose");
        return;
    }   
    
    // Get components column
    const componentsColumn = messageGroup.querySelector('.components-column');
    if (!componentsColumn) {
        console.error("Components column not found");
        return;
    }

    const componentsList = componentsColumn.querySelector('.components-list');
    if (!componentsList) {
        console.error("Components list not found");
        return;
    }

    // Show loading indicator
    showDecompositionLoading(componentsList);
    
    // Create A2A format payload
    const taskId = generateUUID();
    // const conversationId = `conversation-${localStorage.getItem("conversationCounter")}`;
    const userToken = `${window.USER_TOKEN}`;
    const payload = {
        id: taskId,
        conversation_id: conversationId,
        userToken: userToken,
        message: {
            role: "user",
            parts: [
                { text: responseText }
            ]
        }
    };
    
    // Send decomposition request to backend
    fetch(`${window.MOD_AGENT_URL}/${window.DECOMPOSE_ENDPOINT}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(taskResponse => {
        // Process A2A response format
        const processedData = processA2AResponse(taskResponse);
        
        if (processedData.error) {
            throw new Error(processedData.error);
        }
        
        // Clear loading indicator
        componentsList.innerHTML = '';
        
        // Process decomposed components and keep as an array
        let componentsArr = [];
        
        if (processedData.components && Array.isArray(processedData.components)) {
            componentsArr = processedData.components;
        }
        
        // Store data for final output generation
        if (processedData.outputType) {
            messageGroup.dataset.outputType = processedData.outputType;
        }
        
        if (processedData.outputStructure) {
            messageGroup.dataset.outputStructure = JSON.stringify(processedData.outputStructure);
        }
        
        // Render components
        if (componentsArr.length > 0) {
            componentsArr.forEach(componentObj => {
                const key = Object.keys(componentObj)[0];
                const value = componentObj[key];
                addComponentToUI(componentsColumn, key, value);
            });
        } else {
            addPlaceholderComponent(componentsList);
        }
        
    })
    .catch(error => {
        console.error('Decomposition failed:', error);
        showDecompositionError(componentsList, error.message);
    });
}

function processA2AResponse(taskResponse) {
    try {
        // Validate basic structure
        if (!taskResponse || typeof taskResponse !== 'object') {
            return { error: 'Invalid task response format' };
        }
        
        const responseData = {};
        
        // Check if artifacts exist
        if (taskResponse.artifacts && Array.isArray(taskResponse.artifacts)) {
            // Process each artifact
            for (const artifact of taskResponse.artifacts) {
                if (artifact.parts && Array.isArray(artifact.parts)) {
                    // Process each part
                    for (const part of artifact.parts) {
                        // Check if this part has data with kind "data"
                        if (part.kind === 'data' && part.data) {
                            const data = part.data;
                            
                            // Extract components
                            const components = data.components || [];
                            if (components.length > 0) {
                                responseData.components = components;
                                responseData.outputType = data.outputType || '';
                                
                                // Use outputStructure if provided, otherwise generate from components
                                if (data.outputStructure && Array.isArray(data.outputStructure)) {
                                    responseData.outputStructure = data.outputStructure;
                                } else {
                                    responseData.outputStructure = components.map(component => {
                                        const keys = Object.keys(component);
                                        return keys.length > 0 ? keys[0] : '';
                                    }).filter(key => key !== '');
                                }
                                
                                // Return early on first successful extraction
                                return responseData;
                            }
                        }
                    }
                }
            }
        }
        
        // If no components found, return empty structure
        if (!responseData.components) {
            responseData.components = [];
            responseData.outputType = '';
            responseData.outputStructure = [];
        }
        
        return responseData;
    } catch (error) {
        console.error('Error processing A2A response:', error);
        return { error: `Failed to process A2A response: ${error.message}` };
    }
}


// Generate a UUID for task ID using modern browser API
function generateUUID() {
    // Use native crypto.randomUUID if available (modern browsers)
    if (crypto && crypto.randomUUID) {
        return crypto.randomUUID();
    }
    
    // Fallback for older browsers
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Generate final output based on components
export function generateFinalOutput(conversationId) {
    const messageGroup = document.getElementById(conversationId);
    if (!messageGroup) return;

    // Log button click with type
    logEvent(conversationId, 'generate_output_clicked', { button_type: 'structured' });
    
    // Get output type and structure if available
    const outputType = messageGroup.dataset.outputType || 'document';
    let outputStructure = [];
    try {
        if (messageGroup.dataset.outputStructure) {
            outputStructure = JSON.parse(messageGroup.dataset.outputStructure);
        }
    } catch (e) {
        console.error('Error parsing output structure:', e);
    }
    
    // Object to store all component contents by key. Values may be strings or arrays
    const componentContents = {};
    
    // Get all components and store their content
    const components = messageGroup.querySelectorAll('.components-column .component');
    components.forEach(component => {
        const headerText = component.querySelector('.component-header').textContent.trim();
        const contentText = component.querySelector('.component-content').textContent.trim();
        
        // Skip loading and error components
        if (headerText === 'Decomposing Response' ||
            headerText === 'Decomposition Error' ||
            headerText === 'No Components Found') {
            return;
        }
        
        // Only include components that have been checked
        const checkIcon = component.querySelector('.component-check');
        if (!checkIcon || !checkIcon.classList.contains('checked')) {
            return;
        }

        // Convert header to key format (lowercase, underscores)
        const key = headerText.toLowerCase().replace(/\s+/g, '_');
        if (componentContents[key]) {
            // Support duplicate components by storing an array of values
            if (Array.isArray(componentContents[key])) {
                componentContents[key].push(contentText);
            } else {
                componentContents[key] = [componentContents[key], contentText];
            }
        } else {
            componentContents[key] = contentText;
        }
    });
    
    // Generate final output based on type and structure
    let finalOutput = '';
    
    if (outputType === 'email') {
        finalOutput = formatEmailOutput(componentContents);
    } else if (outputType === 'report') {
        finalOutput = formatReportOutput(componentContents);
    } else {
        finalOutput = formatDocumentOutput(componentContents, outputStructure);
    }
    
    // Find the final output container and update its content
    const finalOutputContent = messageGroup.querySelector('.final-output .bubble-content');
    if (finalOutputContent) {
        finalOutputContent.innerHTML = marked.parse(finalOutput);
    }

    // Reveal the final output column if hidden
    const finalOutputColumn = messageGroup.querySelector('.final-output-column');
    if (finalOutputColumn) {
        finalOutputColumn.style.display = 'flex';
    }
    
    // Highlight the final output briefly to show it's been updated
    const finalOutputBubble = messageGroup.querySelector('.final-output');
    if (finalOutputBubble) {
        finalOutputBubble.classList.add('highlight-pulse');
        setTimeout(() => {
            finalOutputBubble.classList.remove('highlight-pulse');
        }, 1000);
    }
}

function normalizeValue(val) {
    if (Array.isArray(val)) {
        return val;
    }
    return val ? [val] : [];
}

// Format components as an email
function formatEmailOutput(componentContents) {
    let output = '';
    
    // Email subject
    if (componentContents.subject) {
        output = `${normalizeValue(componentContents.subject)[0]}\n\n`;
    }
    
    // Greeting
    if (componentContents.greeting) {
        output += `${normalizeValue(componentContents.greeting)[0]}\n\n`;
    }
    
    // Main body paragraphs - dynamically find all relevant keys
    const excludedKeys = ['subject', 'greeting', 'sign_off'];
    Object.keys(componentContents).forEach(key => {
        if (!excludedKeys.includes(key)) {
            const parts = normalizeValue(componentContents[key]);
            parts.forEach(part => {
                output += `${part}\n\n`;
            });
        }
    });
    
    // Sign off
    if (componentContents.sign_off) {
        output += normalizeValue(componentContents.sign_off)[0];
    }
    
    return output.trim();
}

// Format components as a report
function formatReportOutput(componentContents) {
    let output = '';

    // Report title
    if (componentContents.title) {
        output = `${normalizeValue(componentContents.title)[0]}\n\n`;
    }

    // Executive summary
    if (componentContents.executive_summary) {
        output += `${normalizeValue(componentContents.executive_summary)[0]}\n\n`;
    }

    // Other report sections - use all remaining components
    const excludedKeys = ['title', 'executive_summary'];
    Object.keys(componentContents).forEach(key => {
        if (!excludedKeys.includes(key)) {
            const parts = normalizeValue(componentContents[key]);
            parts.forEach(part => {
                output += `${part}\n\n`;
            });
        }
    });

    return output.trim();
}

// Format components as a generic document
function formatDocumentOutput(componentContents, outputStructure) {
    let output = '';
    
    const appendContent = val => {
        const parts = normalizeValue(val);
        parts.forEach(part => {
            output += `${part}\n\n`;
        });
    };

    if (outputStructure && outputStructure.length > 0) {
        // Use the provided structure to order components
        outputStructure.forEach(heading => {
            // Try to find the matching key in componentContents
            // First convert the heading to a consistent format
            const normalizedHeading = heading.toLowerCase().replace(/\s+/g, '_');
            let content = null;
            
            // Check direct match
            if (componentContents[normalizedHeading]) {
                content = componentContents[normalizedHeading];
            } else {
                // Try to match by direct key (might be capitalized differently)
                const keys = Object.keys(componentContents);
                for (const key of keys) {
                    if (key.toLowerCase() === normalizedHeading) {
                        content = componentContents[key];
                        break;
                    }
                }
            }
            
            if (content) {
                appendContent(content);
            }
        });

        // Include any remaining components not specified in the structure
        Object.keys(componentContents).forEach(key => {
            if (!outputStructure.map(h => h.toLowerCase().replace(/\s+/g, '_')).includes(key)) {
                appendContent(componentContents[key]);
            }
        });
    } else {
        // Fallback to the order of components as provided
        Object.keys(componentContents).forEach(key => {
            appendContent(componentContents[key]);
        });
    }

    return output.trim();
}
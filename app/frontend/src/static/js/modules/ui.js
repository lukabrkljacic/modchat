// src/static/js/modules/ui.js
/**
 * UI Module - Handles core UI functionality like sidebar, mobile controls, etc.
 */

// Import helpers
import { getSelectedModel } from './models.js';
import { getSettings } from './settings.js';
import { onComponentStateChange } from './components.js';
import { logEvent, getSessionId } from './tracking.js';

// Function to check if we're on a mobile device
export function isMobileDevice() {
    return window.innerWidth <= 768;
}

// Set up all UI controls and event listeners
export function setupUIComponents() {
    // DOM Elements
    const sidebar = document.getElementById('settings-sidebar');
    const advancedModeToggle = document.getElementById('advanced-mode-toggle');
    const backArrow = document.querySelector('.back-arrow');
    const settingItems = document.querySelectorAll('.setting-item');
    
    // Mobile elements
    const sidebarOverlay = document.getElementById('sidebar-overlay');
    const mobileSettingsToggle = document.getElementById('mobile-settings-toggle');
    const closeSidebarBtn = document.getElementById('close-sidebar');
    
    // Toggle advanced mode
    if (advancedModeToggle) {
        advancedModeToggle.addEventListener('change', function() {
            const isAdvancedMode = this.checked;
            document.body.classList.toggle('advanced-mode', isAdvancedMode);
            
            // Show/hide sidebar based on advanced mode
            if (isAdvancedMode && sidebar) {
                // Always show sidebar in advanced mode, regardless of device
                sidebar.classList.add('active');
            } else if (sidebar) {
                // When turning off advanced mode, hide the sidebar
                sidebar.classList.remove('active');
            }

            // Log toggle event with current settings
            logEvent(null, 'advanced_mode_toggled', {
                enabled: isAdvancedMode,
                settings: getSettings()
            });
        });
    }
    
    // Mobile settings toggle button
    if (mobileSettingsToggle && sidebar) {
        mobileSettingsToggle.addEventListener('click', function(e) {
            sidebar.classList.add('active');
            e.stopPropagation();
        });
    }
    
    // Close sidebar button (mobile)
    if (closeSidebarBtn && sidebar) {
        closeSidebarBtn.addEventListener('click', function(e) {
            // On mobile, just hide the sidebar but KEEP advanced mode on
            sidebar.classList.remove('active');
            e.stopPropagation();
        });
    }
    
    // Sidebar overlay click handler (only for mobile)
    if (sidebarOverlay && sidebar) {
        sidebarOverlay.addEventListener('click', function(e) {
            // Only on mobile should clicks on overlay close the sidebar
            if (isMobileDevice()) {
                sidebar.classList.remove('active');
            }
            // Don't propagate the click
            e.stopPropagation();
        });
    }
    
    // Back button in sidebar (desktop)
    if (backArrow && sidebar && advancedModeToggle) {
        backArrow.addEventListener('click', function(e) {
            // Turn off advanced mode when clicking back arrow
            advancedModeToggle.checked = false;
            document.body.classList.remove('advanced-mode');
            
            // Hide the sidebar
            sidebar.classList.remove('active');
            
            // Prevent event propagation
            e.stopPropagation();
        });
    }
    
    // Expandable settings sections
    settingItems.forEach(item => {
        item.addEventListener('click', function(e) {
            // Don't toggle if clicking inside the expanded content
            if (e.target.closest('.setting-content') && e.target.closest('.setting-content').parentNode === this) {
                return;
            }
            
            // Close any other open settings
            settingItems.forEach(otherItem => {
                if (otherItem !== this) {
                    otherItem.classList.remove('active');
                }
            });
            
            // Toggle this setting
            this.classList.toggle('active');
            
            // Prevent event bubbling
            e.stopPropagation();
        });
    });
    
    // Adjust behavior when window is resized
    window.addEventListener('resize', function() {
        if (advancedModeToggle && advancedModeToggle.checked && sidebar) {
            // In advanced mode, sidebar should always be visible
            sidebar.classList.add('active');
        } else if (sidebar) {
            // When not in advanced mode, sidebar should be hidden
            sidebar.classList.remove('active');
        }
    });
    
    // Add global event handlers for component and bubble actions
    setupComponentActions();
}

// Helper function to set up component actions (edit, expand, etc.)
function setupComponentActions() {
    document.addEventListener('click', function(e) {
        // Handle edit button clicks on components
        if (e.target.classList.contains('fas') && (e.target.classList.contains('component-edit') || 
            (e.target.classList.contains('bubble-action') && e.target.classList.contains('fa-edit')))) {
            let contentElement;
            
            if (e.target.classList.contains('component-edit')) {
                contentElement = e.target.closest('.component').querySelector('.component-content');
            } else {
                // For bubble actions
                const parentElement = e.target.closest('.user-prompt, .system-prompt, .main-response, .final-output');
                if (parentElement) {
                    contentElement = parentElement.querySelector('.bubble-content');
                }
            }
            
            // If we found a content element to edit
            if (contentElement) {
                // Make content editable if it's not already
                if (!contentElement.getAttribute('contenteditable')) {
                    contentElement.setAttribute('contenteditable', 'true');
                    contentElement.focus();
                    
                    // Add a save button
                    const actionsContainer = e.target.closest('.component-actions, .bubble-actions');
                    if (actionsContainer) {
                        const saveBtn = document.createElement('i');
                        saveBtn.className = e.target.classList.contains('component-edit') ?
                            'fas fa-check component-action component-save' :
                            'fas fa-check bubble-action bubble-save';
                        saveBtn.title = 'Accept Edits';
                        actionsContainer.appendChild(saveBtn);
                        
                        // Hide the edit button
                        e.target.style.display = 'none';
                    }
                }
            }
        }
        
        // Handle save button clicks
        if (e.target.classList.contains('fas') && (e.target.classList.contains('component-save') || 
            e.target.classList.contains('bubble-save'))) {
            let contentElement, editBtn;
            let isComponent = e.target.classList.contains('component-save');
            
            if (isComponent) {
                const component = e.target.closest('.component');
                contentElement = component.querySelector('.component-content');
                editBtn = component.querySelector('.component-edit');
            } else {
                // For bubble save
                const parentElement = e.target.closest('.user-prompt, .system-prompt, .main-response, .final-output');
                if (parentElement) {
                    contentElement = parentElement.querySelector('.bubble-content');
                    editBtn = parentElement.querySelector('.bubble-action.fa-edit');
                }
            }
            
            // If we found content and edit button
            if (contentElement && editBtn) {
                // Make content non-editable
                contentElement.removeAttribute('contenteditable');
                
                // Show the edit button again
                editBtn.style.display = 'inline';
                
                // Remove the save button
                e.target.remove();
            }
        }

        // Handle component expand/collapse for both components and main response
        if (e.target.classList.contains('fas') && (e.target.classList.contains('component-expand') ||
            (e.target.classList.contains('bubble-action') && (e.target.classList.contains('fa-chevron-up') ||
            e.target.classList.contains('fa-chevron-down'))))) {
            let contentElement;
            
            if (e.target.classList.contains('component-expand')) {
                contentElement = e.target.closest('.component').querySelector('.component-content');
            } else {
                // For bubble actions
                const parentElement = e.target.closest('.main-response, .final-output');
                if (parentElement) {
                    contentElement = parentElement.querySelector('.bubble-content');
                }
            }
            
            // Toggle content visibility
            if (contentElement) {
                if (contentElement.style.display === 'none') {
                    contentElement.style.display = 'block';
                    e.target.classList.remove('fa-chevron-down');
                    e.target.classList.add('fa-chevron-up');
                } else {
                    contentElement.style.display = 'none';
                    e.target.classList.remove('fa-chevron-up');
                    e.target.classList.add('fa-chevron-down');
                }
            }
        }

        // Handle regenerate button clicks
        if (e.target.classList.contains('fas') && (e.target.classList.contains('component-regenerate') ||
            (e.target.classList.contains('bubble-action') && e.target.classList.contains('fa-sync-alt')))) {
            const isComponent = e.target.classList.contains('component-regenerate');
            const messageGroup = e.target.closest('.message-group');
            let contentElement;
            let containerElement;
            let componentTitle = '';

            if (isComponent) {
                const comp = e.target.closest('.component');
                containerElement = comp;
                contentElement = comp ? comp.querySelector('.component-content') : null;
                const header = comp ? comp.querySelector('.component-header') : null;
                componentTitle = header ? header.textContent.trim() : '';
            } else {
                const parentElement = e.target.closest('.main-response');
                containerElement = parentElement;
                if (parentElement) {
                    contentElement = parentElement.querySelector('.bubble-content');
                    const header = parentElement.querySelector('.bubble-header');
                    componentTitle = header ? header.textContent.trim() : '';
                }
            }

            if (containerElement) {
                containerElement.classList.add('highlight-pulse');
                setTimeout(() => containerElement.classList.remove('highlight-pulse'), 1000);
            }

            if (contentElement && messageGroup) {
                const originalText = contentElement.textContent.trim();
                const promptMessage = componentTitle ? `Enter a prompt to regenerate "${componentTitle}":` :
                    'Enter a prompt to regenerate the text:';
                const userPrompt = prompt(promptMessage, '');
                if (!userPrompt) return;

                // Show loading animation
                contentElement.innerHTML = 'Regenerating... <i class="fas fa-spinner fa-spin"></i>';

                const modelId = messageGroup.dataset.modelId || getSelectedModel().id;
                const vendor = messageGroup.dataset.vendor || getSelectedModel().vendor;
                const settings = getSettings();
                const conversationId = messageGroup.dataset.conversationId;

                const responseBubble = messageGroup.querySelector('.main-response .bubble-content');
                const userBubble = messageGroup.querySelector('.user-prompt .bubble-content');
                const originalResponse = responseBubble ? responseBubble.textContent.trim() : '';
                const originalPrompt = userBubble ? userBubble.textContent.trim() : '';

                fetch(`${window.BACKEND_URL}/regenerate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        text: originalText,
                        prompt: userPrompt,
                        model: modelId,
                        vendor: vendor,
                        settings: settings,
                        conversation_id: conversationId,
                        session_id: getSessionId(),
                        component_title: componentTitle,
                        original_response: originalResponse,
                        original_prompt: originalPrompt,
                        userToken: `${window.USER_TOKEN}`

                    })
                })
                .then(resp => resp.json())
                .then(data => {
                    if (data.text) {
                        contentElement.innerHTML = marked.parse(data.text);
                        if (data.conversation_id) {
                            messageGroup.dataset.conversationId = data.conversation_id;
                        }
                    } else if (data.error) {
                        contentElement.innerHTML = `Regeneration failed: ${data.error}`;
                    }
                })
                .catch(err => {
                    console.error('Regeneration error:', err);
                    contentElement.innerHTML = 'An error occurred while regenerating the text.';
                });
            }
        }
        
        // Handle components container collapse/expand
        if (e.target.classList.contains('components-toggle')) {
            const column = e.target.closest('.components-column');
            if (column) {
                const list = column.querySelector('.components-list');
                if (list) {
                    if (list.style.display === 'none') {
                        list.style.display = 'flex';
                        e.target.classList.remove('fa-chevron-down');
                        e.target.classList.add('fa-chevron-up');
                    } else {
                        list.style.display = 'none';
                        e.target.classList.remove('fa-chevron-up');
                        e.target.classList.add('fa-chevron-down');
                    }
                }
            }
        }

        // Handle checkmark clicks
        if (e.target.classList.contains('component-check')) {
            e.target.classList.toggle('checked');
            const group = e.target.closest('.message-group');
            if (group) {
                onComponentStateChange(group.id);
            }
        }

        // Handle delete button clicks
        if (e.target.classList.contains('component-delete')) {
            const comp = e.target.closest('.component');
            const group = e.target.closest('.message-group');
            if (comp) comp.remove();
            if (group) {
                onComponentStateChange(group.id);
            }
        }

        // Handle copy button clicks
        if (e.target.classList.contains('fas') && e.target.classList.contains('fa-copy')) {
            const parentElement = e.target.closest('.final-output');
            if (parentElement) {
                const contentElement = parentElement.querySelector('.bubble-content');
                const headerElement = parentElement.querySelector('.bubble-header');
                
                if (contentElement) {
                    // Copy to clipboard
                    copyToClipboard(contentElement.textContent);
                    
                    // Show feedback
                    if (headerElement) {
                        const originalText = headerElement.childNodes[0].textContent;
                        headerElement.childNodes[0].textContent = 'Copied to clipboard!';
                        setTimeout(() => {
                            headerElement.childNodes[0].textContent = originalText;
                        }, 1500);
                    }
                }
            }
        }
    });

    setupColumnResizeHandlers();
}

function setupColumnResizeHandlers() {
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;

    let startX = 0;
    let startWidths = [];
    let activeIndex = 0;
    let totalFractions = 0;

    chatContainer.addEventListener('mousedown', (e) => {
        if (!e.target.classList.contains('column-resizer')) return;
        activeIndex = parseInt(e.target.dataset.index, 10);
        startX = e.clientX;
        const styles = getComputedStyle(document.documentElement);
        startWidths = [
            parseFloat(styles.getPropertyValue('--user-col-width')),
            parseFloat(styles.getPropertyValue('--response-col-width')),
            parseFloat(styles.getPropertyValue('--components-col-width')),
            parseFloat(styles.getPropertyValue('--final-output-col-width'))
        ];
        totalFractions = startWidths[0] + startWidths[1] + startWidths[2] + startWidths[3];
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', stopResize);
    });

    function handleMouseMove(e) {
        const containerWidth = chatContainer.getBoundingClientRect().width;
        const deltaFraction = ((e.clientX - startX) / containerWidth) * totalFractions;
        const minFraction = totalFractions * 0.05;
        let [w1, w2, w3, w4] = startWidths;
        if (activeIndex === 1) {
            w1 = Math.max(minFraction, startWidths[0] + deltaFraction);
            w2 = Math.max(minFraction, startWidths[1] - deltaFraction);
            document.documentElement.style.setProperty('--user-col-width', `${w1}fr`);
            document.documentElement.style.setProperty('--response-col-width', `${w2}fr`);
        } else if (activeIndex === 2) {
            w2 = Math.max(minFraction, startWidths[1] + deltaFraction);
            w3 = Math.max(minFraction, startWidths[2] - deltaFraction);
            document.documentElement.style.setProperty('--response-col-width', `${w2}fr`);
            document.documentElement.style.setProperty('--components-col-width', `${w3}fr`);
        } else if (activeIndex === 3) {
            w3 = Math.max(minFraction, startWidths[2] + deltaFraction);
            w4 = Math.max(minFraction, startWidths[3] - deltaFraction);
            document.documentElement.style.setProperty('--components-col-width', `${w3}fr`);
            document.documentElement.style.setProperty('--final-output-col-width', `${w4}fr`);
        }
    }

    function stopResize() {
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', stopResize);
    }
}

// Utility function to copy text to clipboard
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
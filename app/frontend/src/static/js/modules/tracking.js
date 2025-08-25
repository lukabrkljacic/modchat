// src/static/js/modules/tracking.js
/**
 * Tracking Module - Sends user interaction events to the backend
 */

let sessionId = null;

export function initSession() {
    sessionId = crypto.randomUUID();
    try {
        sessionStorage.setItem('sessionId', sessionId);
    } catch (e) {
        console.warn('Unable to store sessionId:', e);
    }
}

export function getSessionId() {
    return sessionId;
}

export function logEvent(conversationId, eventType, data = {}) {
    const payload = {
        session_id: sessionId,
        conversation_id: conversationId || 'global',
        event_type: eventType,
        data: data,
        userToken: `${window.USER_TOKEN}`
    };

    fetch(`${window.BACKEND_URL}/log_event`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).catch(err => {
        console.error('Event logging failed:', err);
    });
}

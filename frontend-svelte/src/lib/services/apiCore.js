import { mapError } from './toast.svelte.js';

// PROXY CONFIGURATION:
// requests to /api/... will be forwarded to http://localhost:8000/... by Vite
export const API_URL = '/api';

/**
 * Get stored JWT token
 */
export function getToken() {
    return localStorage.getItem('token');
}

/**
 * Create headers with auth token
 */
export function authHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

/**
 * Parse API error from response and map to Indonesian messages.
 */
export async function parseError(response) {
    const errText = await response.text();
    let message = errText;
    try {
        const json = JSON.parse(errText);
        const detail = json.detail;
        if (typeof detail === 'string') {
            message = detail;
        } else if (detail && typeof detail === 'object') {
            const detailMessage = typeof detail.message === 'string'
                ? detail.message
                : JSON.stringify(detail);
            if (detail.code === 'bypass_quota_exceeded' && detail.quota) {
                const remaining = detail.quota.remaining_files ?? '-';
                const limit = detail.quota.limit_files ?? '-';
                message = `${detailMessage} Remaining ${remaining}/${limit} files in 1h window.`;
            } else {
                message = detailMessage;
            }
        }
    } catch (e) { /* ignore */ }
    return mapError(message || 'Request failed');
}

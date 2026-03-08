import { mapError } from './toast.svelte.js';

// PROXY CONFIGURATION:
// requests to /api/... will be forwarded to http://localhost:8000/... by Vite
export const API_URL = '/api';

/**
 * Create request headers.
 * Auth is carried by HttpOnly cookie session.
 */
export function authHeaders(extra = {}) {
    return { ...extra };
}

/**
 * Cookie-aware fetch for API requests.
 */
export function apiFetch(url, options = {}) {
    return fetch(url, {
        credentials: 'include',
        ...options,
    });
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
                const suggestedMode = detail.suggested_mode ? ` Try ${detail.suggested_mode} mode.` : '';
                message = `${detailMessage} Remaining ${remaining}/${limit} files in 1h window.${suggestedMode}`;
            } else {
                message = detailMessage;
            }
        }
    } catch (e) { /* ignore */ }
    return mapError(message || 'Request failed');
}

// Super Admin API Service
// Provides API methods for the super admin dashboard

import { API_URL, authHeaders, parseError } from './apiCore.js';

export const SuperAdminApi = {
    // ========================================================================
    // STATS
    // ========================================================================

    async getStats() {
        const response = await fetch(`${API_URL}/super-admin/stats`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // ========================================================================
    // AI CACHE OPS
    // ========================================================================

    async getAICacheStats() {
        const response = await fetch(`${API_URL}/super-admin/ai-cache/stats`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getAICacheRecent({ limit = 20, offset = 0, expiredOnly = false } = {}) {
        const params = new URLSearchParams({
            limit: String(limit),
            offset: String(offset),
        });
        if (expiredOnly) params.append('expired_only', 'true');

        const response = await fetch(`${API_URL}/super-admin/ai-cache/recent?${params}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async purgeExpiredAICache() {
        const response = await fetch(`${API_URL}/super-admin/ai-cache/purge-expired`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async exportAICacheRecentCsv({ expiredOnly = false, limit = 5000 } = {}) {
        const params = new URLSearchParams({ limit: String(limit) });
        if (expiredOnly) params.append('expired_only', 'true');

        const response = await fetch(`${API_URL}/super-admin/ai-cache/recent/export?${params}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.blob();
    },

    async deleteAICacheKey(cacheKey) {
        const response = await fetch(`${API_URL}/super-admin/ai-cache/${cacheKey}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // ========================================================================
    // TICKETS
    // ========================================================================

    async listTickets(filters = {}) {
        const { skip = 0, limit = 50, status, priority } = filters;
        const params = new URLSearchParams({ skip, limit });
        if (status) params.append('status', status);
        if (priority) params.append('priority', priority);

        const response = await fetch(`${API_URL}/super-admin/tickets?${params}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getUnreadTicketCount() {
        const response = await fetch(`${API_URL}/super-admin/tickets/unread-count`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getTicketDetail(ticketId) {
        const response = await fetch(`${API_URL}/super-admin/tickets/${ticketId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async replyToTicket(ticketId, content) {
        const response = await fetch(`${API_URL}/super-admin/tickets/${ticketId}/reply`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ content }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async updateTicketStatus(ticketId, status) {
        const response = await fetch(`${API_URL}/super-admin/tickets/${ticketId}/status`, {
            method: 'PATCH',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ status }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteTicket(ticketId) {
        const response = await fetch(`${API_URL}/super-admin/tickets/${ticketId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },
};

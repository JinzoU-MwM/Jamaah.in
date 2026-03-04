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

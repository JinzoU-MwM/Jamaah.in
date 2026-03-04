import { API_URL, authHeaders, parseError } from '../apiCore.js';

export const supportTicketApi = {
    async createTicket(subject, message, priority = 'medium') {
        const response = await fetch(`${API_URL}/tickets`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ subject, message, priority }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async listMyTickets(filters = {}) {
        const { skip = 0, limit = 20, status } = filters;
        const params = new URLSearchParams({
            skip: String(skip),
            limit: String(limit),
        });
        if (status) params.append('status', status);

        const response = await fetch(`${API_URL}/tickets?${params}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getMyTicketDetail(ticketId) {
        const response = await fetch(`${API_URL}/tickets/${ticketId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async replyToTicket(ticketId, content) {
        const response = await fetch(`${API_URL}/tickets/${ticketId}/reply`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ content }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },
};

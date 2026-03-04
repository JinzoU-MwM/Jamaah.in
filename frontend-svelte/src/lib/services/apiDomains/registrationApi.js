import { API_URL, authHeaders, parseError } from '../apiCore.js';

export const registrationApi = {
    async getRegistrationInfo(token) {
        const response = await fetch(`${API_URL}/registration/public/${token}`);
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async submitRegistration(token, formData) {
        const response = await fetch(`${API_URL}/registration/public/${token}`, {
            method: 'POST',
            body: formData,
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getRegistrationLink(groupId) {
        const response = await fetch(`${API_URL}/registration/link/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async generateRegistrationLink(groupId, expiresInDays = 30) {
        const response = await fetch(`${API_URL}/registration/generate`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ group_id: groupId, expires_in_days: expiresInDays }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async revokeRegistrationLink(groupId) {
        const response = await fetch(`${API_URL}/registration/link/${groupId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getPendingMembers(groupId) {
        const response = await fetch(`${API_URL}/registration/pending/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async approvePendingMember(pendingId) {
        const response = await fetch(`${API_URL}/registration/pending/${pendingId}/approve`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async rejectPendingMember(pendingId) {
        const response = await fetch(`${API_URL}/registration/pending/${pendingId}/reject`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },
};

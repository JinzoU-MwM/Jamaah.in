import { API_URL, authHeaders, parseError, apiFetch } from '../apiCore.js';

export function createContentApi({ cacheGet, cacheSet }) {
    return {
        async getDashboardStats() {
            const cached = cacheGet('analytics:dashboard');
            if (cached) return cached;
            const response = await apiFetch(`${API_URL}/analytics/dashboard`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet('analytics:dashboard', data, 30000); // 30s TTL
            return data;
        },

        async getItinerary(groupId) {
            const response = await apiFetch(`${API_URL}/itineraries/${groupId}`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async createItinerary(groupId, data) {
            const response = await apiFetch(`${API_URL}/itineraries/${groupId}`, {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async updateItinerary(groupId, itemId, data) {
            const response = await apiFetch(`${API_URL}/itineraries/${groupId}/${itemId}`, {
                method: 'PUT',
                headers: authHeaders(),
                body: JSON.stringify(data),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async deleteItinerary(groupId, itemId) {
            const response = await apiFetch(`${API_URL}/itineraries/${groupId}/${itemId}`, {
                method: 'DELETE',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        getDocumentUrl(groupId, type) {
            return `${API_URL}/documents/${groupId}/${type}`;
        },

        async getNotifications() {
            const response = await apiFetch(`${API_URL}/notifications`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },
    };
}

// PROXY CONFIGURATION:
// requests to /api/... will be forwarded to http://localhost:8000/... by Vite
export const API_URL = '/api';

/**
 * Get stored JWT token
 */
function getToken() {
    return localStorage.getItem('token');
}

/**
 * Create headers with auth token
 */
function authHeaders(extra = {}) {
    const token = getToken();
    const headers = { ...extra };
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
}

import { mapError } from './toast.svelte.js';

/**
 * Parse API error from response — maps to Indonesian messages
 */
async function parseError(response) {
    const errText = await response.text();
    let message = errText;
    try {
        const json = JSON.parse(errText);
        if (json.detail) message = json.detail;
    } catch (e) { /* ignore */ }
    return mapError(message || 'Request failed');
}

// ==========================================================================
// LIGHTWEIGHT IN-MEMORY CACHE
// ==========================================================================

const _cache = new Map();

function cacheGet(key) {
    const entry = _cache.get(key);
    if (!entry) return null;
    if (Date.now() > entry.expiresAt) {
        _cache.delete(key);
        return null;
    }
    return entry.data;
}

function cacheSet(key, data, ttlMs) {
    _cache.set(key, { data, expiresAt: Date.now() + ttlMs });
}

function cacheInvalidate(prefix) {
    for (const key of _cache.keys()) {
        if (key.startsWith(prefix)) _cache.delete(key);
    }
}

function cacheClear() {
    _cache.clear();
}

export const ApiService = {

    // =========================================================================
    // AUTH
    // =========================================================================

    async register(email, password, name) {
        const response = await fetch(`${API_URL}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password, name }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async login(email, password) {
        const response = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getMe() {
        const cached = cacheGet('auth:me');
        if (cached) return cached;
        const response = await fetch(`${API_URL}/auth/me`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet('auth:me', data, 120000); // 120s TTL
        return data;
    },

    // =========================================================================
    // SUBSCRIPTION
    // =========================================================================

    async getSubscriptionStatus() {
        const cached = cacheGet('sub:status');
        if (cached) return cached;
        const response = await fetch(`${API_URL}/subscription/status`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet('sub:status', data, 60000); // 60s TTL
        return data;
    },

    async upgradeToPro(paymentRef = null) {
        const response = await fetch(`${API_URL}/subscription/upgrade`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ payment_ref: paymentRef }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async updateProfile(updates) {
        // updates can be: { name, avatar_color, notify_usage_limit, notify_expiry }
        const response = await fetch(`${API_URL}/auth/profile`, {
            method: 'PATCH',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(updates),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async changePassword(currentPassword, newPassword) {
        const response = await fetch(`${API_URL}/auth/change-password`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getActivity() {
        const response = await fetch(`${API_URL}/auth/activity`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteAccount(password) {
        const response = await fetch(`${API_URL}/auth/account`, {
            method: 'DELETE',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ password }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async verifyEmail(email, otp) {
        const response = await fetch(`${API_URL}/auth/verify-email`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, otp }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async resendOtp(email) {
        const response = await fetch(`${API_URL}/auth/resend-otp`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async forgotPassword(email) {
        const response = await fetch(`${API_URL}/auth/forgot-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async resetPassword(email, code, newPassword) {
        const response = await fetch(`${API_URL}/auth/reset-password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, code, new_password: newPassword }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // PAYMENT (Pakasir)
    // =========================================================================

    async createPaymentOrder(planType = "monthly") {
        const response = await fetch(`${API_URL}/payment/create-order?plan_type=${planType}`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async checkPaymentStatus(orderId) {
        const response = await fetch(`${API_URL}/payment/status/${orderId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // DOCUMENT PROCESSING
    // =========================================================================

    /**
     * Upload documents for OCR processing (auth required)
     */
    async uploadDocuments(files, sessionId = null) {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });

        const url = sessionId
            ? `${API_URL}/process-documents/?session_id=${sessionId}`
            : `${API_URL}/process-documents/`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: authHeaders(),  // JWT auth
                body: formData,
            });

            if (!response.ok) {
                throw new Error(await parseError(response));
            }

            return await response.json();
        } catch (error) {
            if (error.message.includes('fetch')) {
                throw new Error(`Connection failed: ${error.message}. Is the backend running?`);
            }
            throw error;
        }
    },

    /**
     * Stream progress updates via SSE
     */
    streamProgress(sessionId, onProgress) {
        const eventSource = new EventSource(`${API_URL}/progress/${sessionId}`);

        eventSource.addEventListener('progress', (e) => {
            try {
                const data = JSON.parse(e.data);
                onProgress(data);
            } catch (err) {
                console.error('Progress parse error:', err);
            }
        });

        eventSource.addEventListener('done', () => {
            eventSource.close();
        });

        eventSource.addEventListener('error', (e) => {
            console.error('SSE error:', e);
            eventSource.close();
        });

        return eventSource;
    },

    // =========================================================================
    // EXCEL
    // =========================================================================

    async generateExcel(data) {
        try {
            const response = await fetch(`${API_URL}/generate-excel/`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ data }),
            });

            if (!response.ok) {
                throw new Error(await parseError(response));
            }

            const blob = await response.blob();
            if (blob.size < 100) {
                throw new Error('Downloaded file appears to be corrupted (too small)');
            }
            return blob;
        } catch (error) {
            if (error.message.includes('fetch')) {
                throw new Error(`Excel generation failed: ${error.message}`);
            }
            throw error;
        }
    },

    // =========================================================================
    // GROUPS
    // =========================================================================

    async listGroups() {
        const cached = cacheGet('groups:list');
        if (cached) return cached;
        const response = await fetch(`${API_URL}/groups/`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet('groups:list', data, 30000); // 30s TTL
        return data;
    },

    async createGroup(name, description = '') {
        const response = await fetch(`${API_URL}/groups/`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ name, description }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        cacheInvalidate('groups:');
        return await response.json();
    },

    async getGroup(groupId) {
        const cached = cacheGet(`groups:${groupId}`);
        if (cached) return cached;
        const response = await fetch(`${API_URL}/groups/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet(`groups:${groupId}`, data, 30000); // 30s TTL
        return data;
    },

    async updateGroup(groupId, data) {
        const response = await fetch(`${API_URL}/groups/${groupId}`, {
            method: 'PUT',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteGroup(groupId) {
        const response = await fetch(`${API_URL}/groups/${groupId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        cacheInvalidate('groups:');
        return await response.json();
    },

    async addGroupMembers(groupId, members) {
        const response = await fetch(`${API_URL}/groups/${groupId}/members`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ members }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        cacheInvalidate('groups:');
        return await response.json();
    },

    async updateGroupMember(groupId, memberId, data) {
        const response = await fetch(`${API_URL}/groups/${groupId}/members/${memberId}`, {
            method: 'PUT',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteGroupMember(groupId, memberId) {
        const response = await fetch(`${API_URL}/groups/${groupId}/members/${memberId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        cacheInvalidate('groups:');
        return await response.json();
    },
};


// Extend ApiService with Inventory and Rooming methods (Pro only)
Object.assign(ApiService, {
    // =========================================================================
    // INVENTORY (Pro only)
    // =========================================================================

    async getInventoryForecast(groupId) {
        const response = await fetch(`${API_URL}/inventory/forecast/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getFulfillmentStatus(groupId) {
        const response = await fetch(`${API_URL}/inventory/fulfillment/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async markMembersReceived(groupId, memberIds) {
        const response = await fetch(`${API_URL}/inventory/fulfillment/${groupId}/mark-received`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ member_ids: memberIds, items_received: ['koper', 'baju'] }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async updateMemberOperational(memberId, bajuSize, familyId) {
        const response = await fetch(`${API_URL}/inventory/members/${memberId}/operational`, {
            method: 'PUT',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ baju_size: bajuSize, family_id: familyId }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // ROOMING (Pro only)
    // =========================================================================

    async getRoomingSummary(groupId) {
        const response = await fetch(`${API_URL}/rooming/summary/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getGroupRooms(groupId) {
        const response = await fetch(`${API_URL}/rooming/group/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async createRoom(groupId, roomNumber, genderType = 'male', roomType = 'quad', capacity = 4) {
        const response = await fetch(`${API_URL}/rooming/group/${groupId}`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ room_number: roomNumber, gender_type: genderType, room_type: roomType, capacity }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteRoom(roomId) {
        const response = await fetch(`${API_URL}/rooming/${roomId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async autoRooming(groupId, roomCapacity = 4) {
        const response = await fetch(`${API_URL}/rooming/auto/${groupId}`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ room_capacity: roomCapacity }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async clearAutoRooming(groupId) {
        const response = await fetch(`${API_URL}/rooming/auto/${groupId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async assignMemberToRoom(memberId, roomId) {
        const response = await fetch(`${API_URL}/rooming/assign`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ member_id: memberId, room_id: roomId }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async unassignMember(memberId) {
        const response = await fetch(`${API_URL}/rooming/unassign/${memberId}`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // SHARED MANIFEST (Mutawwif)
    // =========================================================================

    async shareGroup(groupId, pin, expiresInDays = 30) {
        const response = await fetch(`${API_URL}/groups/${groupId}/share`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ pin, expires_in_days: expiresInDays }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async revokeShare(groupId) {
        const response = await fetch(`${API_URL}/groups/${groupId}/share`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getSharedManifest(sharedToken, pin) {
        const response = await fetch(`${API_URL}/shared/manifest/${sharedToken}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pin }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // TEAM / ORGANIZATION (Pro only)
    // =========================================================================

    async getTeam() {
        const response = await fetch(`${API_URL}/team/`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async createOrganization(name) {
        const response = await fetch(`${API_URL}/team/create`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ name }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async inviteTeamMember(email, role = 'viewer') {
        const response = await fetch(`${API_URL}/team/invite`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ email, role }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async joinTeam(token) {
        const response = await fetch(`${API_URL}/team/join/${token}`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async updateTeamMemberRole(memberId, role) {
        const response = await fetch(`${API_URL}/team/members/${memberId}`, {
            method: 'PATCH',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ role }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async removeTeamMember(memberId) {
        const response = await fetch(`${API_URL}/team/members/${memberId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async cancelTeamInvite(inviteId) {
        const response = await fetch(`${API_URL}/team/invites/${inviteId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // ANALYTICS
    // =========================================================================

    async getDashboardStats() {
        const cached = cacheGet('analytics:dashboard');
        if (cached) return cached;
        const response = await fetch(`${API_URL}/analytics/dashboard`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet('analytics:dashboard', data, 30000); // 30s TTL
        return data;
    },

    // =========================================================================
    // ITINERARY
    // =========================================================================

    async getItinerary(groupId) {
        const response = await fetch(`${API_URL}/itineraries/${groupId}`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async createItinerary(groupId, data) {
        const response = await fetch(`${API_URL}/itineraries/${groupId}`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async updateItinerary(groupId, itemId, data) {
        const response = await fetch(`${API_URL}/itineraries/${groupId}/${itemId}`, {
            method: 'PUT',
            headers: authHeaders(),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async deleteItinerary(groupId, itemId) {
        const response = await fetch(`${API_URL}/itineraries/${groupId}/${itemId}`, {
            method: 'DELETE',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // DOCUMENT TEMPLATES
    // =========================================================================

    getDocumentUrl(groupId, type) {
        const token = localStorage.getItem('token');
        return `${API_URL}/documents/${groupId}/${type}?token=${token}`;
    },

    // =========================================================================
    // NOTIFICATIONS
    // =========================================================================

    async getNotifications() {
        const response = await fetch(`${API_URL}/notifications`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    // =========================================================================
    // PHONE VERIFICATION & PRO TRIAL
    // =========================================================================

    async sendPhoneOtp(phoneNumber) {
        const response = await fetch(`${API_URL}/auth/send-phone-otp`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ phone_number: phoneNumber }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async verifyPhone(phoneNumber, otp) {
        const response = await fetch(`${API_URL}/auth/verify-phone`, {
            method: 'POST',
            headers: authHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({ phone_number: phoneNumber, otp }),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getTrialStatus() {
        const cached = cacheGet('sub:trial');
        if (cached) return cached;
        const response = await fetch(`${API_URL}/subscription/trial-status`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        const data = await response.json();
        cacheSet('sub:trial', data, 300000); // 5min TTL
        return data;
    },

    async activateProTrial() {
        const response = await fetch(`${API_URL}/subscription/activate-trial`, {
            method: 'POST',
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },

    async getPricing() {
        const response = await fetch(`${API_URL}/subscription/pricing`, {
            headers: authHeaders(),
        });
        if (!response.ok) throw new Error(await parseError(response));
        return await response.json();
    },
});

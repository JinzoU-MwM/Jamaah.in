import { API_URL, authHeaders, parseError, apiFetch } from '../apiCore.js';

export function createAuthSubscriptionApi({ cacheGet, cacheSet }) {
    return {
        async register(email, password, name) {
            const response = await apiFetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, name }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async login(email, password) {
            const response = await apiFetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async logout() {
            const response = await apiFetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getMe() {
            const cached = cacheGet('auth:me');
            if (cached) return cached;
            const response = await apiFetch(`${API_URL}/auth/me`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet('auth:me', data, 30000); // 30s TTL
            return data;
        },

        async getSubscriptionStatus() {
            const cached = cacheGet('sub:status');
            if (cached) return cached;
            const response = await apiFetch(`${API_URL}/subscription/status`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet('sub:status', data, 20000); // 20s TTL
            return data;
        },

        async upgradeToPro(paymentRef = null) {
            const response = await apiFetch(`${API_URL}/subscription/upgrade`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ payment_ref: paymentRef }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async updateProfile(updates) {
            const response = await apiFetch(`${API_URL}/auth/profile`, {
                method: 'PATCH',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify(updates),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async changePassword(currentPassword, newPassword) {
            const response = await apiFetch(`${API_URL}/auth/change-password`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getActivity() {
            const response = await apiFetch(`${API_URL}/auth/activity`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async deleteAccount(password) {
            const response = await apiFetch(`${API_URL}/auth/account`, {
                method: 'DELETE',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ password }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async verifyEmail(email, otp) {
            const response = await apiFetch(`${API_URL}/auth/verify-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, otp }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async resendOtp(email) {
            const response = await apiFetch(`${API_URL}/auth/resend-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async forgotPassword(email) {
            const response = await apiFetch(`${API_URL}/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async resetPassword(email, code, newPassword) {
            const response = await apiFetch(`${API_URL}/auth/reset-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, code, new_password: newPassword }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async sendPhoneOtp(phoneNumber) {
            const response = await apiFetch(`${API_URL}/auth/send-phone-otp`, {
                method: 'POST',
                headers: authHeaders({ 'Content-Type': 'application/json' }),
                body: JSON.stringify({ phone_number: phoneNumber }),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async verifyPhone(phoneNumber, otp) {
            const response = await apiFetch(`${API_URL}/auth/verify-phone`, {
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
            const response = await apiFetch(`${API_URL}/subscription/trial-status`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            const data = await response.json();
            cacheSet('sub:trial', data, 30000); // 30s TTL
            return data;
        },

        async activateProTrial() {
            const response = await apiFetch(`${API_URL}/subscription/activate-trial`, {
                method: 'POST',
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },

        async getPricing() {
            const response = await apiFetch(`${API_URL}/subscription/pricing`, {
                headers: authHeaders(),
            });
            if (!response.ok) throw new Error(await parseError(response));
            return await response.json();
        },
    };
}

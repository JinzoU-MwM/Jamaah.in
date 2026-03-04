import { API_URL, authHeaders, parseError } from '../apiCore.js';

export const paymentApi = {
    async createPaymentOrder(planType = 'monthly') {
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
};

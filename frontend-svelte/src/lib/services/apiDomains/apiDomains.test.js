import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createAuthSubscriptionApi } from './authSubscriptionApi.js';
import { createContentApi } from './contentApi.js';
import { documentExcelApi } from './documentExcelApi.js';
import { createGroupOpsApi } from './groupOpsApi.js';
import { paymentApi } from './paymentApi.js';
import { registrationApi } from './registrationApi.js';

function createStorageMock() {
    const store = new Map();
    return {
        getItem: vi.fn((key) => store.get(key) ?? null),
        setItem: vi.fn((key, value) => store.set(key, String(value))),
        removeItem: vi.fn((key) => store.delete(key)),
        clear: vi.fn(() => store.clear()),
    };
}

describe('API domain modules', () => {
    let fetchMock;

    beforeEach(() => {
        vi.restoreAllMocks();
        vi.stubGlobal('localStorage', createStorageMock());
        localStorage.setItem('token', 'test-token');
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
    });

    it('createAuthSubscriptionApi.getMe caches response', async () => {
        const cache = new Map();
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ id: 1, email: 'a@b.com' }),
        });

        const api = createAuthSubscriptionApi({
            cacheGet: (key) => cache.get(key) ?? null,
            cacheSet: (key, value) => cache.set(key, value),
        });

        const a = await api.getMe();
        const b = await api.getMe();

        expect(a.id).toBe(1);
        expect(b.id).toBe(1);
        expect(fetchMock).toHaveBeenCalledTimes(1);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/auth/me',
            expect.objectContaining({
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
            })
        );
    });

    it('paymentApi.createPaymentOrder sends expected request', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ order_id: 'ord-1' }),
        });

        const res = await paymentApi.createPaymentOrder('yearly');

        expect(res.order_id).toBe('ord-1');
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/payment/create-order?plan_type=yearly',
            expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
            })
        );
    });

    it('registrationApi.submitRegistration posts form data', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ success: true }),
        });
        const formData = new FormData();
        formData.append('nama', 'Ahmad');

        const res = await registrationApi.submitRegistration('token123', formData);

        expect(res.success).toBe(true);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/registration/public/token123',
            expect.objectContaining({
                method: 'POST',
                body: formData,
            })
        );
    });

    it('createContentApi.getDocumentUrl builds document endpoint', () => {
        const api = createContentApi({
            cacheGet: () => null,
            cacheSet: () => {},
        });
        expect(api.getDocumentUrl(7, 'group-manifest')).toBe('/api/documents/7/group-manifest');
    });

    it('documentExcelApi.uploadDocuments uses session and cache mode query when provided', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ processed: 1 }),
        });

        const blob = new Blob(['abc'], { type: 'text/plain' });
        const res = await documentExcelApi.uploadDocuments([blob], 'sess-1');

        expect(res.processed).toBe(1);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/process-documents/?session_id=sess-1&cache_mode=default',
            expect.objectContaining({
                method: 'POST',
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
            })
        );
    });

    it('documentExcelApi.uploadDocuments accepts explicit cache mode', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ processed: 1 }),
        });

        const blob = new Blob(['abc'], { type: 'text/plain' });
        await documentExcelApi.uploadDocuments([blob], null, { cacheMode: 'bypass' });

        expect(fetchMock).toHaveBeenCalledWith(
            '/api/process-documents/?cache_mode=bypass',
            expect.objectContaining({ method: 'POST' })
        );
    });

    it('documentExcelApi.uploadDocuments rejects invalid cache mode', async () => {
        const blob = new Blob(['abc'], { type: 'text/plain' });
        await expect(
            documentExcelApi.uploadDocuments([blob], null, { cacheMode: 'unknown-mode' })
        ).rejects.toThrow('Invalid cache mode');
    });

    it('createGroupOpsApi.listGroups uses cache on second call', async () => {
        const cache = new Map();
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => [{ id: 1, name: 'Grup A' }],
        });
        const api = createGroupOpsApi({
            cacheGet: (key) => cache.get(key) ?? null,
            cacheSet: (key, value) => cache.set(key, value),
            cacheInvalidate: () => {},
        });

        const a = await api.listGroups();
        const b = await api.listGroups();

        expect(a).toHaveLength(1);
        expect(b).toHaveLength(1);
        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it('createContentApi.getDashboardStats uses cache on second call', async () => {
        const cache = new Map();
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ total_users: 10 }),
        });
        const api = createContentApi({
            cacheGet: (key) => cache.get(key) ?? null,
            cacheSet: (key, value) => cache.set(key, value),
        });

        const a = await api.getDashboardStats();
        const b = await api.getDashboardStats();

        expect(a.total_users).toBe(10);
        expect(b.total_users).toBe(10);
        expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it('createGroupOpsApi.createGroup invalidates groups cache prefix', async () => {
        const invalidateMock = vi.fn();
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ id: 2, name: 'Baru' }),
        });
        const api = createGroupOpsApi({
            cacheGet: () => null,
            cacheSet: () => {},
            cacheInvalidate: invalidateMock,
        });

        await api.createGroup('Baru', 'desc');

        expect(invalidateMock).toHaveBeenCalledWith('groups:');
    });

    it('paymentApi.checkPaymentStatus maps error message from backend detail', async () => {
        fetchMock.mockResolvedValue({
            ok: false,
            text: async () => JSON.stringify({ detail: 'Unauthorized' }),
        });

        await expect(paymentApi.checkPaymentStatus('ord-err')).rejects.toThrow(
            'Sesi Anda telah habis. Silakan login kembali.'
        );
    });
});

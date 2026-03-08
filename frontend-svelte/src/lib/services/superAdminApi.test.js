import { beforeEach, describe, expect, it, vi } from 'vitest';
import { SuperAdminApi } from './superAdminApi.js';

function createStorageMock() {
    const store = new Map();
    return {
        getItem: vi.fn((key) => store.get(key) ?? null),
        setItem: vi.fn((key, value) => store.set(key, String(value))),
        removeItem: vi.fn((key) => store.delete(key)),
        clear: vi.fn(() => store.clear()),
    };
}

describe('SuperAdminApi', () => {
    let fetchMock;

    beforeEach(() => {
        vi.restoreAllMocks();
        vi.stubGlobal('localStorage', createStorageMock());
        fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
    });

    it('getAICacheStats fetches super-admin ai cache stats', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ total: 10, active: 7, expired: 3 }),
        });

        const data = await SuperAdminApi.getAICacheStats();

        expect(data.total).toBe(10);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/ai-cache/stats',
            expect.objectContaining({
                credentials: 'include',
            })
        );
    });

    it('getCharts fetches chart series for dashboard', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ user_activity: [], revenue_monthly: [] }),
        });

        const data = await SuperAdminApi.getCharts();

        expect(Array.isArray(data.user_activity)).toBe(true);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/charts',
            expect.objectContaining({
                credentials: 'include',
            })
        );
    });

    it('getAICacheRecent sends limit/offset/expired_only params', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ total: 1, limit: 5, offset: 0, items: [] }),
        });

        await SuperAdminApi.getAICacheRecent({ limit: 5, offset: 0, expiredOnly: true });

        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/ai-cache/recent?limit=5&offset=0&expired_only=true',
            expect.objectContaining({
                credentials: 'include',
            })
        );
    });

    it('purgeExpiredAICache posts to purge endpoint', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ deleted: 3 }),
        });

        const data = await SuperAdminApi.purgeExpiredAICache();

        expect(data.deleted).toBe(3);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/ai-cache/purge-expired',
            expect.objectContaining({
                method: 'POST',
                credentials: 'include',
            })
        );
    });

    it('exportAICacheRecentCsv fetches csv blob from export endpoint', async () => {
        const blob = new Blob(['csv,data']);
        fetchMock.mockResolvedValue({
            ok: true,
            blob: async () => blob,
        });

        const res = await SuperAdminApi.exportAICacheRecentCsv({ expiredOnly: true, limit: 100 });

        expect(res).toBe(blob);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/ai-cache/recent/export?limit=100&expired_only=true',
            expect.objectContaining({
                credentials: 'include',
            })
        );
    });

    it('deleteAICacheKey sends delete request to per-key endpoint', async () => {
        fetchMock.mockResolvedValue({
            ok: true,
            json: async () => ({ cache_key: 'abc', deleted: true }),
        });

        const res = await SuperAdminApi.deleteAICacheKey('abc');

        expect(res.deleted).toBe(true);
        expect(fetchMock).toHaveBeenCalledWith(
            '/api/super-admin/ai-cache/abc',
            expect.objectContaining({
                method: 'DELETE',
                credentials: 'include',
            })
        );
    });
});

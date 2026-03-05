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
        localStorage.setItem('token', 'test-token');
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
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
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
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
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
                headers: expect.objectContaining({
                    Authorization: 'Bearer test-token',
                }),
            })
        );
    });
});

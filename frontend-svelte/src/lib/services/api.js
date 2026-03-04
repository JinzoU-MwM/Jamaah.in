import { API_URL, authHeaders } from './apiCore.js';
import { createAuthSubscriptionApi } from './apiDomains/authSubscriptionApi.js';
import { createGroupOpsApi } from './apiDomains/groupOpsApi.js';
import { createContentApi } from './apiDomains/contentApi.js';
import { paymentApi } from './apiDomains/paymentApi.js';
import { documentExcelApi } from './apiDomains/documentExcelApi.js';
import { supportTicketApi } from './apiDomains/supportTicketApi.js';
import { registrationApi } from './apiDomains/registrationApi.js';

export { API_URL, authHeaders };

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
    cacheClear,
};

Object.assign(
    ApiService,
    createAuthSubscriptionApi({ cacheGet, cacheSet }),
    createGroupOpsApi({ cacheGet, cacheSet, cacheInvalidate }),
    createContentApi({ cacheGet, cacheSet }),
    paymentApi,
    documentExcelApi,
    supportTicketApi,
    registrationApi
);

import { API_URL, authHeaders, parseError } from '../apiCore.js';

export const documentExcelApi = {
    /**
     * Get OCR runtime/provider/cache status (auth required)
     */
    async getOcrStatus() {
        try {
            const response = await fetch(`${API_URL}/ocr/status`, {
                headers: authHeaders(),
            });

            if (!response.ok) {
                throw new Error(await parseError(response));
            }

            return await response.json();
        } catch (error) {
            if (error.message.includes('fetch')) {
                throw new Error(`Failed to get OCR status: ${error.message}`);
            }
            throw error;
        }
    },

    /**
     * Upload documents for OCR processing (auth required)
     */
    async uploadDocuments(files, sessionId = null, options = {}) {
        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });

        const normalizedCacheMode = String(options.cacheMode || 'default').trim().toLowerCase();
        if (!['default', 'refresh', 'bypass'].includes(normalizedCacheMode)) {
            throw new Error(`Invalid cache mode: ${normalizedCacheMode}`);
        }
        const params = new URLSearchParams();
        if (sessionId) params.set('session_id', sessionId);
        params.set('cache_mode', normalizedCacheMode);
        const query = params.toString();
        const url = query
            ? `${API_URL}/process-documents/?${query}`
            : `${API_URL}/process-documents/`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: authHeaders(),
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
};

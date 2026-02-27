/**
 * Toast notification store — Svelte 5 reactive
 * Usage: import { showToast } from './toast'; showToast('message', 'success');
 */

let toasts = $state([]);
let nextId = 0;

// Indonesian error message mapping
const ERROR_MAP = {
    'Failed to fetch': 'Gagal koneksi ke server. Periksa koneksi internet Anda.',
    'Network Error': 'Koneksi jaringan bermasalah. Coba lagi nanti.',
    'fetch failed': 'Gagal koneksi ke server. Pastikan backend berjalan.',
    'Connection failed': 'Gagal koneksi ke server.',
    'Internal Server Error': 'Terjadi kesalahan di server. Coba lagi nanti.',
    'Not Found': 'Data tidak ditemukan.',
    'Unauthorized': 'Sesi Anda telah habis. Silakan login kembali.',
    'Forbidden': 'Anda tidak memiliki akses ke fitur ini.',
    'Token expired': 'Sesi Anda telah habis. Silakan login kembali.',
    'Invalid token': 'Sesi tidak valid. Silakan login kembali.',
    'limit reached': 'Batas penggunaan gratis telah tercapai.',
    'usage limit': 'Batas penggunaan gratis telah tercapai.',
    'Email already registered': 'Email sudah terdaftar. Silakan login.',
    'Invalid credentials': 'Email atau password salah.',
    'too many requests': 'Terlalu banyak percobaan. Tunggu beberapa saat.',
    'Rate limit': 'Terlalu banyak percobaan. Tunggu beberapa saat.',
    'file too large': 'Ukuran file terlalu besar. Maksimal 10MB.',
    'Excel generation failed': 'Gagal membuat file Excel. Coba lagi.',
    'corrupted': 'File yang diunduh tampaknya rusak. Coba lagi.',
};

/**
 * Map an English error message to Indonesian
 */
export function mapError(message) {
    if (!message) return 'Terjadi kesalahan. Coba lagi.';

    const lower = message.toLowerCase();
    for (const [key, value] of Object.entries(ERROR_MAP)) {
        if (lower.includes(key.toLowerCase())) {
            return value;
        }
    }

    return message;
}

/**
 * Show a toast notification
 * @param {string} message
 * @param {'success'|'error'|'warning'|'info'} type
 * @param {number} duration - ms before auto-dismiss (0 = no auto-dismiss)
 */
export function showToast(message, type = 'info', duration = 5000) {
    const id = nextId++;
    const toast = { id, message, type, duration, visible: true };

    // Max 3 toasts — remove oldest if needed
    if (toasts.length >= 3) {
        toasts = toasts.slice(-2);
    }

    toasts = [...toasts, toast];

    if (duration > 0) {
        setTimeout(() => dismissToast(id), duration);
    }

    return id;
}

/**
 * Dismiss a specific toast
 */
export function dismissToast(id) {
    toasts = toasts.filter(t => t.id !== id);
}

/**
 * Get current toasts (reactive)
 */
export function getToasts() {
    return toasts;
}

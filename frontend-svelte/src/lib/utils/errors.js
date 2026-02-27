/**
 * Indonesian error messages for user-facing error display.
 */
export const errorMessages = {
  // OCR errors
  OCR_FAILED: 'Gagal memproses dokumen. Pastikan foto terang dan jelas.',
  OCR_BLURRY: 'Foto kurang jelas. Coba foto ulang dengan pencahayaan lebih baik.',
  OCR_TOO_DARK: 'Foto terlalu gelap. Coba foto dengan pencahayaan yang cukup.',
  OCR_CORNER_CUT: 'Sudut dokumen terpotong. Pastikan seluruh dokumen terfoto.',
  
  // API errors
  NETWORK_ERROR: 'Koneksi internet terputus. Silakan coba lagi.',
  SERVER_ERROR: 'Terjadi kesalahan pada server. Silakan coba lagi nanti.',
  UNAUTHORIZED: 'Sesi Anda telah berakhir. Silakan login kembali.',
  
  // Validation errors
  INVALID_NIK: 'NIK harus 16 digit angka.',
  INVALID_PASSPORT: 'Nomor paspor tidak valid (huruf + 6-7 digit angka).',
  INVALID_DATE: 'Format tanggal tidak valid.',
  
  // Payment errors
  PAYMENT_FAILED: 'Pembayaran gagal. Silakan coba lagi.',
  QRIS_EXPIRED: 'QRIS telah expired. Silakan buat pembayaran baru.',
  
  // Generic
  UNKNOWN_ERROR: 'Terjadi kesalahan. Silakan coba lagi atau hubungi support.',
};

export function getErrorMessage(error) {
  const code = error?.code || error?.response?.data?.error?.code;
  return errorMessages[code] || errorMessages.UNKNOWN_ERROR;
}

export function getErrorDetail(error) {
  return error?.response?.data?.error?.details || null;
}

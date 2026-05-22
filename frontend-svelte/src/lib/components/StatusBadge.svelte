<script>
  /**
   * StatusBadge — colored pill badge for any status string.
   *
   * statusMap can be passed in, or defaults handle the common cases
   * for packages, jamaah pipeline, invoices, and documents.
   */
  let { status = '', size = 'sm' } = $props();

  const CONFIG = {
    // Package statuses
    draft:     { label: 'Draft',     bg: '#f1f5f9', color: '#64748b' },
    open:      { label: 'Open',      bg: '#eff6ff', color: '#2563eb' },
    full:      { label: 'Penuh',     bg: '#fef3c7', color: '#d97706' },
    closed:    { label: 'Ditutup',   bg: '#fee2e2', color: '#dc2626' },
    done:      { label: 'Selesai',   bg: '#f0fdf4', color: '#16a34a' },
    // Jamaah pipeline
    prospek:   { label: 'Prospek',   bg: '#f1f5f9', color: '#64748b' },
    survey:    { label: 'Survey',    bg: '#eff6ff', color: '#2563eb' },
    booking:   { label: 'Booking',   bg: '#faf5ff', color: '#7c3aed' },
    dp:        { label: 'DP',        bg: '#fff7ed', color: '#ea580c' },
    cicilan:   { label: 'Cicilan',   bg: '#fefce8', color: '#ca8a04' },
    lunas:     { label: 'Lunas',     bg: '#f0fdf4', color: '#16a34a' },
    berangkat: { label: 'Berangkat', bg: '#ecfdf5', color: '#059669' },
    batal:     { label: 'Batal',     bg: '#fef2f2', color: '#dc2626' },
    // Invoice
    'belum bayar': { label: 'Belum Bayar', bg: '#fef2f2', color: '#dc2626' },
    sebagian:  { label: 'Sebagian',  bg: '#fff7ed', color: '#ea580c' },
    // Documents
    'belum diterima': { label: 'Belum', bg: '#f1f5f9', color: '#64748b' },
    diterima:  { label: 'Diterima',  bg: '#f0fdf4', color: '#16a34a' },
    diproses:  { label: 'Diproses',  bg: '#eff6ff', color: '#2563eb' },
  };

  let cfg = $derived(CONFIG[status?.toLowerCase()] || { label: status, bg: '#f1f5f9', color: '#64748b' });
  let padding = $derived(size === 'xs' ? '2px 8px' : '3px 10px');
  let fontSize = $derived(size === 'xs' ? '10px' : '11px');
</script>

<span
  style="background:{cfg.bg}; color:{cfg.color}; padding:{padding}; font-size:{fontSize}; font-weight:700; border-radius:6px; white-space:nowrap; display:inline-block; letter-spacing:0.02em; text-transform:uppercase;"
>
  {cfg.label}
</span>

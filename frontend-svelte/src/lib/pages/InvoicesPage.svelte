<script>
  import { onMount } from 'svelte';
  import {
    Plus, Search, Receipt, AlertCircle, CheckCircle,
    Clock, ChevronRight, Upload, Download,
  } from 'lucide-svelte';
  import StatusBadge from '../components/StatusBadge.svelte';
  import SlideDrawer from '../components/SlideDrawer.svelte';
  import IDRInput from '../components/IDRInput.svelte';
  import { showToast } from '../services/toast.svelte.js';

  let { onNavigate, user = null } = $props();

  // ── State ──────────────────────────────────────────────
  let invoices = $state([]);
  let isLoading = $state(true);
  let searchQuery = $state('');
  let filterStatus = $state('all');
  let drawerOpen = $state(false);
  let selectedInvoice = $state(null);
  let showPaymentModal = $state(false);

  // New payment form
  let payAmount = $state(0);
  let payMethod = $state('transfer');
  let payDate = $state(new Date().toISOString().slice(0, 10));
  let payRef = $state('');
  let payNote = $state('');

  const INVOICE_STATUSES = [
    { id: 'all',          label: 'Semua' },
    { id: 'belum bayar',  label: 'Belum Bayar' },
    { id: 'sebagian',     label: 'Sebagian' },
    { id: 'lunas',        label: 'Lunas' },
  ];

  const PAY_METHODS = [
    { id: 'transfer', label: 'Transfer Bank' },
    { id: 'qris',     label: 'QRIS' },
    { id: 'tunai',    label: 'Tunai' },
    { id: 'cek',      label: 'Cek/Giro' },
  ];

  let filtered = $derived(
    invoices.filter(inv => {
      const matchStatus = filterStatus === 'all' || inv.status === filterStatus;
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || inv.jamaah_name.toLowerCase().includes(q) || inv.invoice_no.toLowerCase().includes(q);
      return matchStatus && matchSearch;
    })
  );

  // Summary stats
  let summaryStats = $derived({
    totalActive: invoices.filter(i => i.status !== 'lunas').reduce((s, i) => s + i.remaining, 0),
    overdueCount: invoices.filter(i => i.is_overdue).length,
    cashToday: invoices.reduce((s, i) => s + i.payments.filter(p => p.date === new Date().toISOString().slice(0,10)).reduce((a, p) => a + p.amount, 0), 0),
  });

  onMount(loadInvoices);

  async function loadInvoices() {
    isLoading = true;
    try {
      await new Promise(r => setTimeout(r, 500));
      invoices = MOCK_INVOICES;
    } catch {
      showToast('Gagal memuat invoice', 'error');
    } finally {
      isLoading = false;
    }
  }

  function openDetail(inv) {
    selectedInvoice = inv;
    drawerOpen = true;
    showPaymentModal = false;
  }

  function formatIDR(num) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  }

  function formatDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  async function submitPayment() {
    if (!payAmount || payAmount <= 0) {
      showToast('Masukkan nominal pembayaran', 'warning');
      return;
    }
    try {
      // TODO: ApiService.recordPayment(selectedInvoice.id, { amount: payAmount, method: payMethod, date: payDate, ref: payRef, note: payNote })
      showToast('Pembayaran berhasil dicatat', 'success');
      showPaymentModal = false;
      drawerOpen = false;
      await loadInvoices();
    } catch (e) {
      showToast('Gagal mencatat pembayaran', 'error');
    }
  }

  const MOCK_INVOICES = [
    {
      id: 1, invoice_no: 'INV/2026/0310/0001', jamaah_name: 'Ahmad Fauzi',
      package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Quad',
      total: 22500000, paid: 22500000, remaining: 0,
      status: 'lunas', is_overdue: false,
      due_date: '2026-02-01',
      payments: [
        { id: 1, date: '2026-01-10', amount: 10000000, method: 'Transfer Bank', ref: 'TRF001' },
        { id: 2, date: '2026-01-25', amount: 12500000, method: 'Transfer Bank', ref: 'TRF002' },
      ],
    },
    {
      id: 2, invoice_no: 'INV/2026/0310/0002', jamaah_name: 'Siti Rahayu',
      package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Double',
      total: 29000000, paid: 10000000, remaining: 19000000,
      status: 'sebagian', is_overdue: true,
      due_date: '2026-02-15',
      payments: [
        { id: 3, date: '2026-01-20', amount: 10000000, method: 'Transfer Bank', ref: 'TRF003' },
      ],
    },
    {
      id: 3, invoice_no: 'INV/2026/0415/0001', jamaah_name: 'Budi Santoso',
      package_name: 'Umroh Plus VIP April 2026', room_type: 'Triple',
      total: 40000000, paid: 0, remaining: 40000000,
      status: 'belum bayar', is_overdue: false,
      due_date: '2026-03-01',
      payments: [],
    },
    {
      id: 4, invoice_no: 'INV/2026/0310/0004', jamaah_name: 'Fatimah Zahra',
      package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Quad',
      total: 22500000, paid: 15000000, remaining: 7500000,
      status: 'sebagian', is_overdue: false,
      due_date: '2026-03-01',
      payments: [
        { id: 4, date: '2026-02-01', amount: 8000000, method: 'QRIS', ref: '' },
        { id: 5, date: '2026-02-20', amount: 7000000, method: 'Tunai', ref: '' },
      ],
    },
  ];
</script>

<div class="flex h-screen flex-col">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Invoice & Pembayaran</h1>
        <p class="mt-0.5 text-sm text-slate-500">{filtered.length} invoice</p>
      </div>
      <button
        type="button"
        class="flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary-600/30 transition-all hover:bg-primary-700"
      >
        <Plus class="h-4 w-4" />
        Buat Invoice
      </button>
    </div>

    <!-- Summary cards -->
    <div class="mt-4 grid grid-cols-3 gap-3">
      <div class="rounded-xl bg-red-50 p-3">
        <p class="text-[11px] font-semibold text-red-400">Total Piutang Aktif</p>
        <p class="mt-0.5 text-base font-bold text-red-700">{formatIDR(summaryStats.totalActive)}</p>
      </div>
      <div class="rounded-xl bg-amber-50 p-3">
        <p class="text-[11px] font-semibold text-amber-400">Overdue</p>
        <p class="mt-0.5 text-base font-bold text-amber-700">{summaryStats.overdueCount} jamaah</p>
      </div>
      <div class="rounded-xl bg-emerald-50 p-3">
        <p class="text-[11px] font-semibold text-emerald-400">Kas Hari Ini</p>
        <p class="mt-0.5 text-base font-bold text-emerald-700">{formatIDR(summaryStats.cashToday)}</p>
      </div>
    </div>

    <!-- Search + filter -->
    <div class="mt-4 flex gap-3">
      <div class="relative flex-1 min-w-0">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          bind:value={searchQuery}
          placeholder="Cari nama atau nomor invoice..."
          class="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div class="flex gap-1">
        {#each INVOICE_STATUSES as s}
          <button
            type="button"
            onclick={() => (filterStatus = s.id)}
            class="flex-shrink-0 rounded-lg px-3 py-2 text-xs font-semibold transition-all
              {filterStatus === s.id ? 'bg-primary-600 text-white' : 'text-slate-500 hover:bg-slate-100'}"
          >
            {s.label}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- Invoice table -->
  <div class="flex-1 overflow-auto">
    {#if isLoading}
      <div class="space-y-3 p-6">
        {#each [1,2,3,4] as _}
          <div class="h-16 animate-pulse rounded-xl bg-slate-100"></div>
        {/each}
      </div>
    {:else if filtered.length === 0}
      <div class="flex flex-col items-center justify-center py-24 text-slate-400">
        <Receipt class="mb-3 h-12 w-12 opacity-30" />
        <p class="font-medium">Belum ada invoice</p>
      </div>
    {:else}
      <table class="w-full min-w-[750px]">
        <thead class="sticky top-0 bg-slate-50">
          <tr class="text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
            <th class="px-6 py-3">No. Invoice</th>
            <th class="px-4 py-3">Jamaah</th>
            <th class="px-4 py-3 text-right">Total</th>
            <th class="px-4 py-3 text-right">Terbayar</th>
            <th class="px-4 py-3 text-right">Sisa</th>
            <th class="px-4 py-3">Status</th>
            <th class="px-4 py-3">Jatuh Tempo</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-50">
          {#each filtered as inv}
            <tr class="group bg-white transition-colors hover:bg-primary-50/30 {inv.is_overdue ? 'bg-red-50/30' : ''}">
              <td class="px-6 py-3.5">
                <div class="flex items-center gap-2">
                  {#if inv.is_overdue}
                    <AlertCircle class="h-4 w-4 flex-shrink-0 text-red-500" />
                  {/if}
                  <span class="text-sm font-mono font-semibold text-slate-700">{inv.invoice_no}</span>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <p class="text-sm font-semibold text-slate-800">{inv.jamaah_name}</p>
                <p class="text-xs text-slate-400">{inv.package_name} · {inv.room_type}</p>
              </td>
              <td class="px-4 py-3.5 text-right text-sm font-medium text-slate-600">{formatIDR(inv.total)}</td>
              <td class="px-4 py-3.5 text-right text-sm font-medium text-emerald-600">{formatIDR(inv.paid)}</td>
              <td class="px-4 py-3.5 text-right text-sm font-bold {inv.remaining > 0 ? 'text-red-600' : 'text-emerald-600'}">
                {inv.remaining > 0 ? formatIDR(inv.remaining) : 'Lunas'}
              </td>
              <td class="px-4 py-3.5">
                <StatusBadge status={inv.status} size="xs" />
              </td>
              <td class="px-4 py-3.5">
                <span class="text-xs {inv.is_overdue ? 'font-semibold text-red-600' : 'text-slate-500'}">
                  {formatDate(inv.due_date)}
                </span>
              </td>
              <td class="px-4 py-3.5">
                <button
                  type="button"
                  onclick={() => openDetail(inv)}
                  class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold text-primary-600 transition-colors hover:bg-primary-50"
                >
                  Detail <ChevronRight class="h-3 w-3" />
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>

<!-- Invoice Detail Drawer -->
<SlideDrawer
  open={drawerOpen}
  title="Invoice {selectedInvoice?.invoice_no || ''}"
  width="580px"
  onClose={() => (drawerOpen = false)}
>
  {#if selectedInvoice}
    <div class="p-6 space-y-5">
      <!-- Header info -->
      <div class="rounded-xl bg-slate-50 p-4 space-y-2">
        <div class="flex items-center justify-between">
          <StatusBadge status={selectedInvoice.status} />
          {#if selectedInvoice.is_overdue}
            <span class="flex items-center gap-1 text-xs font-semibold text-red-600">
              <AlertCircle class="h-3.5 w-3.5" /> Overdue
            </span>
          {/if}
        </div>
        <p class="text-base font-bold text-slate-800">{selectedInvoice.jamaah_name}</p>
        <p class="text-sm text-slate-500">{selectedInvoice.package_name} · {selectedInvoice.room_type}</p>
      </div>

      <!-- Billing summary -->
      <div class="rounded-xl border border-slate-100 p-4 space-y-3">
        <h4 class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Ringkasan Tagihan</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-slate-500">Total Tagihan</span>
            <span class="font-semibold text-slate-800">{formatIDR(selectedInvoice.total)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-slate-500">Sudah Dibayar</span>
            <span class="font-semibold text-emerald-600">{formatIDR(selectedInvoice.paid)}</span>
          </div>
          <div class="border-t border-slate-100 pt-2 flex justify-between">
            <span class="font-semibold text-slate-700">Sisa Tagihan</span>
            <span class="font-bold {selectedInvoice.remaining > 0 ? 'text-red-600' : 'text-emerald-600'}">
              {selectedInvoice.remaining > 0 ? formatIDR(selectedInvoice.remaining) : 'LUNAS'}
            </span>
          </div>
        </div>
        <!-- Progress bar -->
        <div class="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full bg-emerald-400"
            style="width: {Math.round((selectedInvoice.paid / selectedInvoice.total) * 100)}%"
          ></div>
        </div>
        <p class="text-center text-[11px] text-slate-400">
          {Math.round((selectedInvoice.paid / selectedInvoice.total) * 100)}% lunas
        </p>
      </div>

      <!-- Payment history -->
      <div class="rounded-xl border border-slate-100 p-4">
        <h4 class="mb-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">Riwayat Pembayaran</h4>
        {#if selectedInvoice.payments.length === 0}
          <p class="text-sm text-slate-400">Belum ada pembayaran.</p>
        {:else}
          <div class="space-y-2">
            {#each selectedInvoice.payments as pay}
              <div class="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2.5">
                <div>
                  <p class="text-xs font-semibold text-slate-700">{formatDate(pay.date)}</p>
                  <p class="text-[11px] text-slate-400">{pay.method} {pay.ref ? '· ' + pay.ref : ''}</p>
                </div>
                <span class="text-sm font-bold text-emerald-600">{formatIDR(pay.amount)}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Actions -->
      {#if !showPaymentModal}
        <div class="flex gap-3">
          <button
            type="button"
            class="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
          >
            <Download class="h-4 w-4" />
            PDF Invoice
          </button>
          {#if selectedInvoice.remaining > 0}
            <button
              type="button"
              onclick={() => (showPaymentModal = true)}
              class="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary-600 py-2.5 text-sm font-semibold text-white hover:bg-primary-700"
            >
              <Plus class="h-4 w-4" />
              Rekam Pembayaran
            </button>
          {/if}
        </div>

      <!-- Record payment form -->
      {:else}
        <div class="rounded-xl border border-primary-200 bg-primary-50 p-4 space-y-3">
          <h4 class="text-sm font-bold text-primary-800">Rekam Pembayaran Baru</h4>

          <IDRInput label="Nominal" bind:value={payAmount} required />

          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-slate-700">Metode</label>
            <select
              bind:value={payMethod}
              class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            >
              {#each PAY_METHODS as m}
                <option value={m.id}>{m.label}</option>
              {/each}
            </select>
          </div>

          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-slate-700">Tanggal</label>
            <input
              type="date"
              bind:value={payDate}
              class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
          </div>

          <div class="flex flex-col gap-1">
            <label class="text-sm font-medium text-slate-700">No. Referensi (opsional)</label>
            <input
              type="text"
              bind:value={payRef}
              placeholder="Nomor bukti transfer..."
              class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-primary-400"
            />
          </div>

          <div class="flex gap-2">
            <button
              type="button"
              onclick={() => (showPaymentModal = false)}
              class="flex-1 rounded-xl border border-slate-200 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            >
              Batal
            </button>
            <button
              type="button"
              onclick={submitPayment}
              class="flex-1 rounded-xl bg-primary-600 py-2 text-sm font-semibold text-white hover:bg-primary-700"
            >
              Simpan
            </button>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</SlideDrawer>

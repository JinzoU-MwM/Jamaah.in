<script>
  import { onMount } from 'svelte';
  import { TrendingUp, TrendingDown, DollarSign, AlertCircle, Download } from 'lucide-svelte';
  import { showToast } from '../services/toast.svelte.js';

  let { onNavigate, user = null } = $props();

  let activeTab = $state('pl');
  let selectedPeriod = $state('this_month');
  let isLoading = $state(true);
  let stats = $state(null);
  let plData = $state(null);
  let agingData = $state([]);
  let cashFlowData = $state([]);
  let selectedTripId = $state(null);

  const TABS = [
    { id: 'pl',       label: 'P&L per Trip' },
    { id: 'aging',    label: 'Piutang Aging' },
    { id: 'cashflow', label: 'Arus Kas' },
    { id: 'daily',    label: 'Kas Harian' },
  ];

  const PERIODS = [
    { id: 'this_month', label: 'Bulan Ini' },
    { id: 'last_month', label: 'Bulan Lalu' },
    { id: 'this_year',  label: 'Tahun Ini' },
  ];

  onMount(loadData);

  async function loadData() {
    isLoading = true;
    try {
      await new Promise(r => setTimeout(r, 600));
      stats = MOCK_STATS;
      plData = MOCK_PL;
      agingData = MOCK_AGING;
      cashFlowData = MOCK_CASHFLOW;
      if (MOCK_PL.trips.length) selectedTripId = MOCK_PL.trips[0].id;
    } catch {
      showToast('Gagal memuat laporan keuangan', 'error');
    } finally {
      isLoading = false;
    }
  }

  function formatIDR(num) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  }

  function pct(a, b) {
    return b > 0 ? Math.round((a / b) * 100) : 0;
  }

  let selectedTrip = $derived(plData?.trips?.find(t => t.id === selectedTripId));

  // ── Mock data ───────────────────────────────────────────
  const MOCK_STATS = {
    pemasukan: 287500000,
    pengeluaran: 195000000,
    gross_profit: 92500000,
    piutang: 66500000,
    pemasukan_change: 12,
    profit_change: 8,
  };

  const MOCK_PL = {
    trips: [
      {
        id: 1, name: 'Umroh Reguler Ramadan 2026',
        pendapatan: 630000000, diskon: 5000000, pendapatan_bersih: 625000000,
        pengeluaran: { tiket: 200000000, hotel_makkah: 150000000, hotel_madinah: 80000000, visa: 75000000, bus: 30000000, muthawwif: 20000000, perlengkapan: 40000000, lainnya: 10000000 },
        total_pengeluaran: 605000000,
        laba_kotor: 20000000,
        proyeksi_profit: 22000000,
      },
    ],
  };

  const MOCK_AGING = [
    { jamaah: 'Siti Rahayu', paket: 'Umroh Reguler Ramadan 2026', total: 29000000, paid: 10000000, remaining: 19000000, days_overdue: 15, bucket: '1-30' },
    { jamaah: 'Budi Santoso', paket: 'Umroh Plus VIP April 2026', total: 40000000, paid: 0, remaining: 40000000, days_overdue: 0, bucket: '0' },
    { jamaah: 'Fatimah Zahra', paket: 'Umroh Reguler Ramadan 2026', total: 22500000, paid: 15000000, remaining: 7500000, days_overdue: 0, bucket: '0' },
  ];

  const MOCK_CASHFLOW = [
    { month: 'Jan 2026', pemasukan: 45000000, pengeluaran: 30000000 },
    { month: 'Feb 2026', pemasukan: 72000000, pengeluaran: 55000000 },
    { month: 'Mar 2026', pemasukan: 95000000, pengeluaran: 70000000 },
    { month: 'Apr 2026', pemasukan: 38000000, pengeluaran: 22000000 },
    { month: 'Mei 2026', pemasukan: 20000000, pengeluaran: 10000000 },
    { month: 'Jun 2026', pemasukan: 17500000, pengeluaran: 8000000 },
  ];

  let maxCashFlow = $derived(Math.max(...MOCK_CASHFLOW.map(d => Math.max(d.pemasukan, d.pengeluaran)), 1));
</script>

<div class="flex h-screen flex-col">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Laporan Keuangan</h1>
        <p class="mt-0.5 text-sm text-slate-500">Pantau P&L, piutang, dan arus kas bisnis Anda</p>
      </div>
      <div class="flex items-center gap-3">
        <select
          bind:value={selectedPeriod}
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 outline-none focus:border-primary-400"
        >
          {#each PERIODS as p}
            <option value={p.id}>{p.label}</option>
          {/each}
        </select>
        <button
          type="button"
          class="flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
        >
          <Download class="h-4 w-4" />
          Export Excel
        </button>
      </div>
    </div>

    <!-- Summary cards -->
    {#if isLoading}
      <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        {#each [1,2,3,4] as _}
          <div class="h-20 animate-pulse rounded-xl bg-slate-100"></div>
        {/each}
      </div>
    {:else if stats}
      <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryCard
          label="Total Pemasukan"
          value={formatIDR(stats.pemasukan)}
          change={stats.pemasukan_change}
          color="blue"
        />
        <SummaryCard
          label="Total Pengeluaran"
          value={formatIDR(stats.pengeluaran)}
          color="slate"
        />
        <SummaryCard
          label="Gross Profit"
          value={formatIDR(stats.gross_profit)}
          change={stats.profit_change}
          color="emerald"
        />
        <SummaryCard
          label="Total Piutang"
          value={formatIDR(stats.piutang)}
          color="red"
        />
      </div>
    {/if}

    <!-- Tabs -->
    <div class="mt-4 flex gap-1">
      {#each TABS as tab}
        <button
          type="button"
          onclick={() => (activeTab = tab.id)}
          class="rounded-lg px-4 py-1.5 text-xs font-semibold transition-all
            {activeTab === tab.id
              ? 'bg-primary-600 text-white'
              : 'text-slate-500 hover:bg-slate-100'}"
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Tab Content -->
  <div class="flex-1 overflow-y-auto bg-slate-50 p-6">

    {#if activeTab === 'pl'}
      <!-- P&L per Trip -->
      {#if plData}
        <div class="mb-4">
          <label class="block mb-1 text-sm font-medium text-slate-600">Pilih Trip</label>
          <select
            bind:value={selectedTripId}
            class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-primary-400"
          >
            {#each plData.trips as t}
              <option value={t.id}>{t.name}</option>
            {/each}
          </select>
        </div>

        {#if selectedTrip}
          <div class="grid gap-4 lg:grid-cols-2">
            <!-- Pendapatan -->
            <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200/60">
              <h3 class="mb-4 text-sm font-bold text-slate-700">Pendapatan</h3>
              <div class="space-y-2 text-sm">
                <PLRow label="Tagihan Jamaah (total invoice)" value={selectedTrip.pendapatan} />
                <PLRow label="Diskon yang diberikan" value={-selectedTrip.diskon} isNegative />
                <div class="border-t border-slate-100 pt-2">
                  <PLRow label="Total Pendapatan Bersih" value={selectedTrip.pendapatan_bersih} bold />
                </div>
              </div>
            </div>

            <!-- Pengeluaran -->
            <div class="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200/60">
              <h3 class="mb-4 text-sm font-bold text-slate-700">Pengeluaran</h3>
              <div class="space-y-2 text-sm">
                {#each Object.entries(selectedTrip.pengeluaran) as [key, val]}
                  <PLRow label={key.replace(/_/g, ' ')} value={val} isNegative />
                {/each}
                <div class="border-t border-slate-100 pt-2">
                  <PLRow label="Total Pengeluaran" value={selectedTrip.total_pengeluaran} isNegative bold />
                </div>
              </div>
            </div>

            <!-- Bottom result -->
            <div class="lg:col-span-2 rounded-2xl p-5 shadow-sm ring-1 {selectedTrip.laba_kotor >= 0 ? 'bg-emerald-50 ring-emerald-200' : 'bg-red-50 ring-red-200'}">
              <div class="flex items-center justify-between">
                <div>
                  <p class="text-sm font-semibold {selectedTrip.laba_kotor >= 0 ? 'text-emerald-600' : 'text-red-600'}">
                    Laba Kotor
                  </p>
                  <p class="text-3xl font-bold {selectedTrip.laba_kotor >= 0 ? 'text-emerald-700' : 'text-red-700'}">
                    {formatIDR(selectedTrip.laba_kotor)}
                  </p>
                </div>
                <div class="text-right">
                  <p class="text-sm text-slate-500">Margin</p>
                  <p class="text-2xl font-bold text-slate-700">
                    {pct(selectedTrip.laba_kotor, selectedTrip.pendapatan_bersih)}%
                  </p>
                  <p class="text-xs text-slate-400 mt-1">
                    Proyeksi: {formatIDR(selectedTrip.proyeksi_profit)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        {/if}
      {/if}

    {:else if activeTab === 'aging'}
      <!-- Piutang Aging -->
      <div class="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200/60 overflow-hidden">
        <table class="w-full min-w-[600px]">
          <thead class="bg-slate-50">
            <tr class="text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
              <th class="px-5 py-3">Jamaah</th>
              <th class="px-4 py-3">Paket</th>
              <th class="px-4 py-3 text-right">Total</th>
              <th class="px-4 py-3 text-right">Sisa</th>
              <th class="px-4 py-3">Overdue</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-50">
            {#each agingData as row}
              <tr class="hover:bg-slate-50">
                <td class="px-5 py-3 text-sm font-semibold text-slate-800">{row.jamaah}</td>
                <td class="px-4 py-3 text-sm text-slate-500">{row.paket}</td>
                <td class="px-4 py-3 text-right text-sm text-slate-600">{formatIDR(row.total)}</td>
                <td class="px-4 py-3 text-right text-sm font-bold text-red-600">{formatIDR(row.remaining)}</td>
                <td class="px-4 py-3 text-sm">
                  {#if row.days_overdue > 0}
                    <span class="text-red-600 font-semibold">{row.days_overdue} hari</span>
                  {:else}
                    <span class="text-slate-400">Belum jatuh tempo</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

    {:else if activeTab === 'cashflow'}
      <!-- Cash Flow Chart (simple bar chart via CSS) -->
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200/60">
        <h3 class="mb-6 text-sm font-bold text-slate-700">Pemasukan vs Pengeluaran (6 Bulan)</h3>
        <div class="space-y-4">
          {#each cashFlowData as d}
            <div>
              <div class="mb-1 flex items-center justify-between text-xs text-slate-500">
                <span class="font-medium">{d.month}</span>
                <span>{formatIDR(d.pemasukan - d.pengeluaran)}</span>
              </div>
              <div class="flex gap-1 h-6">
                <div
                  class="rounded bg-primary-400"
                  style="width: {pct(d.pemasukan, maxCashFlow)}%"
                  title="Pemasukan: {formatIDR(d.pemasukan)}"
                ></div>
                <div
                  class="rounded bg-red-300"
                  style="width: {pct(d.pengeluaran, maxCashFlow)}%"
                  title="Pengeluaran: {formatIDR(d.pengeluaran)}"
                ></div>
              </div>
              <div class="mt-0.5 flex gap-4 text-[11px] text-slate-400">
                <span class="flex items-center gap-1"><span class="inline-block h-2 w-2 rounded bg-primary-400"></span>Masuk: {formatIDR(d.pemasukan)}</span>
                <span class="flex items-center gap-1"><span class="inline-block h-2 w-2 rounded bg-red-300"></span>Keluar: {formatIDR(d.pengeluaran)}</span>
              </div>
            </div>
          {/each}
        </div>
      </div>

    {:else if activeTab === 'daily'}
      <div class="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200/60">
        <p class="text-slate-400 text-sm">Laporan kas harian akan tersedia setelah data pembayaran diinput.</p>
      </div>
    {/if}
  </div>
</div>

{#snippet SummaryCard(label, value, change, color)}
  {@const colors = {
    blue: 'bg-blue-50 text-blue-700',
    emerald: 'bg-emerald-50 text-emerald-700',
    red: 'bg-red-50 text-red-600',
    slate: 'bg-slate-100 text-slate-700',
  }}
  <div class="rounded-xl {colors[color] || colors.slate} p-4">
    <p class="text-[11px] font-semibold opacity-70">{label}</p>
    <p class="mt-1 text-base font-bold">{value}</p>
    {#if change !== undefined}
      <p class="mt-0.5 text-[11px] font-medium {change >= 0 ? 'text-emerald-600' : 'text-red-500'}">
        {change >= 0 ? '▲' : '▼'} {Math.abs(change)}% vs bulan lalu
      </p>
    {/if}
  </div>
{/snippet}

{#snippet PLRow(label, value, isNegative, bold)}
  <div class="flex items-center justify-between">
    <span class="capitalize text-slate-500 {bold ? 'font-semibold text-slate-700' : ''}">{label}</span>
    <span class="{isNegative ? 'text-red-600' : 'text-slate-800'} {bold ? 'font-bold text-base' : 'font-medium'}">
      {isNegative ? '− ' : ''}{formatIDR(Math.abs(value))}
    </span>
  </div>
{/snippet}

<script>
  import { onMount } from 'svelte';
  import {
    Plus, Package, CalendarDays, Users, ChevronRight,
    Plane, Hotel, MoreVertical, Eye, Edit, Trash2, Globe, Lock,
  } from 'lucide-svelte';
  import StatusBadge from '../components/StatusBadge.svelte';
  import SlideDrawer from '../components/SlideDrawer.svelte';
  import IDRInput from '../components/IDRInput.svelte';
  import { showToast } from '../services/toast.svelte.js';

  let { onNavigate, user = null } = $props();

  // ── State ──────────────────────────────────────────────
  let packages = $state([]);
  let isLoading = $state(true);
  let filterStatus = $state('all');
  let drawerOpen = $state(false);
  let selectedPackage = $state(null);
  let showCreateForm = $state(false);

  // ── Static filter tabs ──────────────────────────────────
  const STATUS_TABS = [
    { id: 'all',    label: 'Semua' },
    { id: 'open',   label: 'Open' },
    { id: 'draft',  label: 'Draft' },
    { id: 'full',   label: 'Penuh' },
    { id: 'closed', label: 'Ditutup' },
    { id: 'done',   label: 'Selesai' },
  ];

  // ── Derived ────────────────────────────────────────────
  let filtered = $derived(
    filterStatus === 'all'
      ? packages
      : packages.filter(p => p.status === filterStatus)
  );

  // ── Data loading ───────────────────────────────────────
  onMount(loadPackages);

  async function loadPackages() {
    isLoading = true;
    try {
      // TODO: replace with ApiService.listPackages() when endpoint ready
      await new Promise(r => setTimeout(r, 600)); // simulate
      packages = MOCK_PACKAGES;
    } catch (e) {
      showToast('Gagal memuat data paket', 'error');
    } finally {
      isLoading = false;
    }
  }

  function openDetail(pkg) {
    selectedPackage = pkg;
    drawerOpen = true;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function formatIDR(num) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  }

  // ── Mock data (replace with API) ────────────────────────
  const MOCK_PACKAGES = [
    {
      id: 1, name: 'Umroh Reguler Ramadan 2026', type: 'umroh_reguler',
      departure_date: '2026-03-10', return_date: '2026-03-24',
      status: 'open', total_seats: 40, filled_seats: 28,
      airline: 'Saudi Airlines', flight_no_dep: 'SV812',
      hotel_makkah: 'Hilton Makkah', hotel_madinah: 'Le Meridien Madinah',
      prices: { quad: 22500000, triple: 25000000, double: 29000000, single: 38000000 },
      is_public: true,
    },
    {
      id: 2, name: 'Umroh Plus VIP April 2026', type: 'umroh_plus',
      departure_date: '2026-04-15', return_date: '2026-04-29',
      status: 'open', total_seats: 25, filled_seats: 10,
      airline: 'Garuda Indonesia', flight_no_dep: 'GA980',
      hotel_makkah: 'Conrad Makkah', hotel_madinah: 'Anwar Al Madinah Mövenpick',
      prices: { quad: 35000000, triple: 40000000, double: 47000000, single: 62000000 },
      is_public: false,
    },
    {
      id: 3, name: 'Haji Khusus 2026', type: 'haji_khusus',
      departure_date: '2026-05-20', return_date: '2026-06-30',
      status: 'full', total_seats: 50, filled_seats: 50,
      airline: 'Saudi Airlines', flight_no_dep: 'SV818',
      hotel_makkah: 'Zam Zam Pullman', hotel_madinah: 'Dallah Taibah',
      prices: { quad: 90000000, triple: 100000000, double: 115000000, single: 145000000 },
      is_public: true,
    },
    {
      id: 4, name: 'Umroh Reguler Juli 2026', type: 'umroh_reguler',
      departure_date: '2026-07-05', return_date: '2026-07-19',
      status: 'draft', total_seats: 40, filled_seats: 0,
      airline: 'Saudi Airlines', flight_no_dep: 'SV810',
      hotel_makkah: 'Hilton Makkah', hotel_madinah: 'Le Meridien Madinah',
      prices: { quad: 23000000, triple: 26000000, double: 30000000, single: 39000000 },
      is_public: false,
    },
  ];
</script>

<div class="flex h-screen flex-col">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Paket & Harga</h1>
        <p class="mt-0.5 text-sm text-slate-500">{packages.length} paket tersedia</p>
      </div>
      <button
        type="button"
        onclick={() => (showCreateForm = true)}
        class="flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary-600/30 transition-all hover:bg-primary-700 hover:shadow-md"
      >
        <Plus class="h-4 w-4" />
        Buat Paket
      </button>
    </div>

    <!-- Filter tabs -->
    <div class="mt-4 flex gap-1 overflow-x-auto pb-0.5">
      {#each STATUS_TABS as tab}
        <button
          type="button"
          onclick={() => (filterStatus = tab.id)}
          class="flex-shrink-0 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all
            {filterStatus === tab.id
              ? 'bg-primary-600 text-white shadow-sm'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'}"
        >
          {tab.label}
        </button>
      {/each}
    </div>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto bg-slate-50 p-6">
    {#if isLoading}
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each [1, 2, 3] as _}
          <div class="h-52 animate-pulse rounded-2xl bg-white"></div>
        {/each}
      </div>
    {:else if filtered.length === 0}
      <div class="flex flex-col items-center justify-center py-24 text-slate-400">
        <Package class="mb-3 h-12 w-12 opacity-30" />
        <p class="font-medium">Belum ada paket</p>
        <p class="mt-1 text-sm">Buat paket pertama untuk mulai menerima pendaftaran jamaah.</p>
      </div>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each filtered as pkg}
          <!-- Package Card -->
          <button
            type="button"
            onclick={() => openDetail(pkg)}
            class="group relative rounded-2xl bg-white p-5 text-left shadow-sm ring-1 ring-slate-200/60 transition-all hover:shadow-md hover:ring-primary-200"
          >
            <!-- Status + visibility row -->
            <div class="mb-3 flex items-center justify-between">
              <StatusBadge status={pkg.status} size="xs" />
              <span class="flex items-center gap-1 text-[11px] font-medium text-slate-400">
                {#if pkg.is_public}
                  <Globe class="h-3 w-3" /> Publik
                {:else}
                  <Lock class="h-3 w-3" /> Private
                {/if}
              </span>
            </div>

            <h3 class="mb-1 text-[15px] font-bold leading-snug text-slate-800 group-hover:text-primary-700">
              {pkg.name}
            </h3>

            <div class="mt-3 space-y-1.5 text-[12px] text-slate-500">
              <div class="flex items-center gap-1.5">
                <CalendarDays class="h-3.5 w-3.5 flex-shrink-0" />
                {formatDate(pkg.departure_date)} — {formatDate(pkg.return_date)}
              </div>
              <div class="flex items-center gap-1.5">
                <Plane class="h-3.5 w-3.5 flex-shrink-0" />
                {pkg.airline} · {pkg.flight_no_dep}
              </div>
              <div class="flex items-center gap-1.5">
                <Hotel class="h-3.5 w-3.5 flex-shrink-0" />
                {pkg.hotel_makkah}
              </div>
            </div>

            <!-- Quota bar -->
            <div class="mt-4">
              <div class="mb-1 flex items-center justify-between text-[11px]">
                <span class="text-slate-400">Kuota terisi</span>
                <span class="font-semibold text-slate-600">{pkg.filled_seats}/{pkg.total_seats}</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  class="h-full rounded-full {pkg.filled_seats >= pkg.total_seats ? 'bg-red-400' : 'bg-emerald-400'}"
                  style="width: {Math.min(100, Math.round((pkg.filled_seats / pkg.total_seats) * 100))}%"
                ></div>
              </div>
            </div>

            <!-- Starting price -->
            <div class="mt-4 border-t border-slate-100 pt-3">
              <p class="text-[11px] text-slate-400">Mulai dari</p>
              <p class="text-sm font-bold text-primary-700">{formatIDR(Math.min(...Object.values(pkg.prices)))}</p>
            </div>

            <ChevronRight class="absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-300 group-hover:text-primary-400" />
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<!-- Package Detail Drawer -->
<SlideDrawer
  open={drawerOpen}
  title={selectedPackage?.name || ''}
  width="600px"
  onClose={() => (drawerOpen = false)}
>
  {#if selectedPackage}
    <div class="p-6 space-y-6">
      <!-- Status row -->
      <div class="flex items-center gap-3">
        <StatusBadge status={selectedPackage.status} />
        <span class="text-sm text-slate-500">
          {selectedPackage.is_public ? '🌐 Paket Publik' : '🔒 Paket Private'}
        </span>
      </div>

      <!-- Basic info -->
      <div class="rounded-xl border border-slate-100 p-4 space-y-3">
        <h3 class="text-xs font-bold uppercase tracking-wider text-slate-400">Info Keberangkatan</h3>
        <InfoRow label="Tanggal Berangkat" value={formatDate(selectedPackage.departure_date)} />
        <InfoRow label="Tanggal Pulang" value={formatDate(selectedPackage.return_date)} />
        <InfoRow label="Maskapai" value="{selectedPackage.airline} — {selectedPackage.flight_no_dep}" />
        <InfoRow label="Hotel Makkah" value={selectedPackage.hotel_makkah} />
        <InfoRow label="Hotel Madinah" value={selectedPackage.hotel_madinah} />
      </div>

      <!-- Pricing tiers -->
      <div class="rounded-xl border border-slate-100 p-4">
        <h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400">Harga per Tipe Kamar</h3>
        <table class="w-full text-sm">
          <thead>
            <tr class="text-left text-xs text-slate-400">
              <th class="pb-2 font-semibold">Tipe</th>
              <th class="pb-2 text-right font-semibold">Harga</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-50">
            {#each [['Quad (4 orang)', selectedPackage.prices.quad], ['Triple (3 orang)', selectedPackage.prices.triple], ['Double (2 orang)', selectedPackage.prices.double], ['Single (1 orang)', selectedPackage.prices.single]] as [label, price]}
              <tr>
                <td class="py-2 text-slate-700">{label}</td>
                <td class="py-2 text-right font-semibold text-slate-800">{formatIDR(price)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      <!-- Quota -->
      <div class="rounded-xl border border-slate-100 p-4">
        <h3 class="mb-3 text-xs font-bold uppercase tracking-wider text-slate-400">Kuota</h3>
        <div class="flex items-end justify-between mb-2">
          <span class="text-3xl font-bold text-slate-800">{selectedPackage.filled_seats}</span>
          <span class="text-slate-400">/ {selectedPackage.total_seats} kursi</span>
        </div>
        <div class="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full {selectedPackage.filled_seats >= selectedPackage.total_seats ? 'bg-red-400' : 'bg-emerald-400'}"
            style="width: {Math.min(100, Math.round((selectedPackage.filled_seats / selectedPackage.total_seats) * 100))}%"
          ></div>
        </div>
        <p class="mt-1.5 text-xs text-slate-400">{selectedPackage.total_seats - selectedPackage.filled_seats} kursi tersisa</p>
      </div>

      <!-- Actions -->
      <div class="flex gap-3">
        <button
          type="button"
          class="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
        >
          <Edit class="h-4 w-4" />
          Edit Paket
        </button>
        <button
          type="button"
          onclick={() => { onNavigate?.('crm'); drawerOpen = false; }}
          class="flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
        >
          <Users class="h-4 w-4" />
          Lihat Jamaah
        </button>
      </div>
    </div>
  {/if}
</SlideDrawer>

<!-- InfoRow snippet -->
{#snippet InfoRow(label, value)}
  <div class="flex items-start justify-between gap-4 text-sm">
    <span class="flex-shrink-0 text-slate-400">{label}</span>
    <span class="text-right font-medium text-slate-700">{value}</span>
  </div>
{/snippet}

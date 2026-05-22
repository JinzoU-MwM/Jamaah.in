<script>
  import { onMount } from 'svelte';
  import {
    Plus, Search, SlidersHorizontal, LayoutGrid, List,
    Phone, Mail, ChevronRight, UserCircle, AlertTriangle,
  } from 'lucide-svelte';
  import StatusBadge from '../components/StatusBadge.svelte';
  import SlideDrawer from '../components/SlideDrawer.svelte';
  import { showToast } from '../services/toast.svelte.js';

  let { onNavigate, user = null } = $props();

  // ── State ──────────────────────────────────────────────
  let jamaah = $state([]);
  let isLoading = $state(true);
  let searchQuery = $state('');
  let filterStatus = $state('all');
  let viewMode = $state('table'); // 'table' | 'kanban'
  let drawerOpen = $state(false);
  let selectedJamaah = $state(null);
  let activeTab = $state('profil');

  const PIPELINE_STATUSES = [
    { id: 'all',       label: 'Semua' },
    { id: 'prospek',   label: 'Prospek' },
    { id: 'survey',    label: 'Survey' },
    { id: 'booking',   label: 'Booking' },
    { id: 'dp',        label: 'DP' },
    { id: 'cicilan',   label: 'Cicilan' },
    { id: 'lunas',     label: 'Lunas' },
    { id: 'berangkat', label: 'Berangkat' },
    { id: 'batal',     label: 'Batal' },
  ];

  const DRAWER_TABS = [
    { id: 'profil',   label: 'Profil' },
    { id: 'dokumen',  label: 'Dokumen' },
    { id: 'invoice',  label: 'Invoice' },
    { id: 'catatan',  label: 'Catatan' },
  ];

  // ── Derived ────────────────────────────────────────────
  let filtered = $derived(
    jamaah.filter(j => {
      const matchStatus = filterStatus === 'all' || j.pipeline_status === filterStatus;
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || j.name.toLowerCase().includes(q) || j.phone.includes(q);
      return matchStatus && matchSearch;
    })
  );

  onMount(loadJamaah);

  async function loadJamaah() {
    isLoading = true;
    try {
      await new Promise(r => setTimeout(r, 500)); // simulate API
      jamaah = MOCK_JAMAAH;
    } catch {
      showToast('Gagal memuat data jamaah', 'error');
    } finally {
      isLoading = false;
    }
  }

  function openDetail(j) {
    selectedJamaah = j;
    activeTab = 'profil';
    drawerOpen = true;
  }

  function openWhatsApp(phone) {
    const clean = phone.replace(/\D/g, '');
    const number = clean.startsWith('0') ? '62' + clean.slice(1) : clean;
    window.open(`https://wa.me/${number}`, '_blank');
  }

  function formatDate(d) {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('id-ID', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function formatIDR(num) {
    return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(num || 0);
  }

  // ── Mock data ───────────────────────────────────────────
  const MOCK_JAMAAH = [
    { id: 1, name: 'Ahmad Fauzi', nik: '3271234567890001', passport_no: 'A1234567', phone: '081234567890', email: 'ahmad@email.com', gender: 'L', package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Quad', pipeline_status: 'lunas', total_invoice: 22500000, paid: 22500000, passport_expiry: '2028-06-15', sisa_tagihan: 0 },
    { id: 2, name: 'Siti Rahayu', nik: '3271234567890002', passport_no: 'B2345678', phone: '087654321098', email: 'siti@email.com', gender: 'P', package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Double', pipeline_status: 'dp', total_invoice: 29000000, paid: 10000000, passport_expiry: '2026-02-10', sisa_tagihan: 19000000 },
    { id: 3, name: 'Budi Santoso', nik: '3271234567890003', passport_no: 'C3456789', phone: '081298765432', email: 'budi@email.com', gender: 'L', package_name: 'Umroh Plus VIP April 2026', room_type: 'Triple', pipeline_status: 'booking', total_invoice: 40000000, paid: 0, passport_expiry: '2027-08-20', sisa_tagihan: 40000000 },
    { id: 4, name: 'Fatimah Zahra', nik: '3271234567890004', passport_no: 'D4567890', phone: '089876543210', email: 'fatimah@email.com', gender: 'P', package_name: 'Umroh Reguler Ramadan 2026', room_type: 'Quad', pipeline_status: 'cicilan', total_invoice: 22500000, paid: 15000000, passport_expiry: '2029-03-05', sisa_tagihan: 7500000 },
    { id: 5, name: 'Rizky Pratama', nik: '3271234567890005', passport_no: null, phone: '082112345678', email: 'rizky@email.com', gender: 'L', package_name: null, room_type: null, pipeline_status: 'prospek', total_invoice: 0, paid: 0, passport_expiry: null, sisa_tagihan: 0 },
  ];

  // ── Passport expiry warning ─────────────────────────────
  function passportWarning(expiry, departureDate) {
    if (!expiry) return null;
    const exp = new Date(expiry);
    const dep = departureDate ? new Date(departureDate) : new Date();
    const daysLeft = Math.round((exp.getTime() - dep.getTime()) / (1000 * 60 * 60 * 24));
    if (daysLeft < 30) return 'red';
    if (daysLeft < 90) return 'yellow';
    return null;
  }
</script>

<div class="flex h-screen flex-col">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">CRM & Jamaah</h1>
        <p class="mt-0.5 text-sm text-slate-500">{filtered.length} jamaah</p>
      </div>
      <div class="flex items-center gap-2">
        <!-- View toggle -->
        <div class="flex rounded-xl border border-slate-200 p-0.5">
          <button
            type="button"
            onclick={() => (viewMode = 'table')}
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-colors {viewMode === 'table' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-600'}"
            title="Tampilan tabel"
          >
            <List class="h-4 w-4" />
          </button>
          <button
            type="button"
            onclick={() => (viewMode = 'kanban')}
            class="flex h-8 w-8 items-center justify-center rounded-lg transition-colors {viewMode === 'kanban' ? 'bg-primary-600 text-white' : 'text-slate-400 hover:text-slate-600'}"
            title="Tampilan kanban"
          >
            <LayoutGrid class="h-4 w-4" />
          </button>
        </div>
        <button
          type="button"
          class="flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary-600/30 transition-all hover:bg-primary-700"
        >
          <Plus class="h-4 w-4" />
          Tambah Jamaah
        </button>
      </div>
    </div>

    <!-- Search + filter -->
    <div class="mt-4 flex gap-3">
      <div class="relative flex-1">
        <Search class="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          bind:value={searchQuery}
          placeholder="Cari nama atau nomor HP..."
          class="w-full rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div class="flex gap-1 overflow-x-auto">
        {#each PIPELINE_STATUSES as s}
          <button
            type="button"
            onclick={() => (filterStatus = s.id)}
            class="flex-shrink-0 rounded-lg px-3 py-2 text-xs font-semibold transition-all
              {filterStatus === s.id
                ? 'bg-primary-600 text-white'
                : 'text-slate-500 hover:bg-slate-100'}"
          >
            {s.label}
          </button>
        {/each}
      </div>
    </div>
  </div>

  <!-- Table view -->
  {#if viewMode === 'table'}
    <div class="flex-1 overflow-auto">
      {#if isLoading}
        <div class="space-y-3 p-6">
          {#each [1,2,3,4] as _}
            <div class="h-14 animate-pulse rounded-xl bg-slate-100"></div>
          {/each}
        </div>
      {:else if filtered.length === 0}
        <div class="flex flex-col items-center justify-center py-24 text-slate-400">
          <UserCircle class="mb-3 h-12 w-12 opacity-30" />
          <p class="font-medium">Belum ada jamaah</p>
        </div>
      {:else}
        <table class="w-full min-w-[700px]">
          <thead class="sticky top-0 bg-slate-50">
            <tr class="text-left text-xs font-semibold uppercase tracking-wider text-slate-400">
              <th class="px-6 py-3">Nama</th>
              <th class="px-4 py-3">Paket</th>
              <th class="px-4 py-3">Status</th>
              <th class="px-4 py-3 text-right">Sisa Tagihan</th>
              <th class="px-4 py-3">Paspor</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-50">
            {#each filtered as j}
              {@const warn = passportWarning(j.passport_expiry, null)}
              <tr class="group bg-white transition-colors hover:bg-primary-50/30">
                <td class="px-6 py-3.5">
                  <div class="flex items-center gap-3">
                    <div class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl {j.gender === 'P' ? 'bg-pink-100' : 'bg-blue-100'} text-sm font-bold {j.gender === 'P' ? 'text-pink-600' : 'text-blue-600'}">
                      {j.name.charAt(0)}
                    </div>
                    <div>
                      <p class="text-sm font-semibold text-slate-800">{j.name}</p>
                      <p class="text-xs text-slate-400">{j.phone}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3.5">
                  <p class="text-sm text-slate-600">{j.package_name || '—'}</p>
                  {#if j.room_type}<p class="text-xs text-slate-400">{j.room_type}</p>{/if}
                </td>
                <td class="px-4 py-3.5">
                  <StatusBadge status={j.pipeline_status} size="xs" />
                </td>
                <td class="px-4 py-3.5 text-right">
                  {#if j.sisa_tagihan > 0}
                    <span class="text-sm font-semibold text-red-600">{formatIDR(j.sisa_tagihan)}</span>
                  {:else}
                    <span class="text-sm font-semibold text-emerald-600">Lunas</span>
                  {/if}
                </td>
                <td class="px-4 py-3.5">
                  {#if !j.passport_no}
                    <span class="text-xs text-slate-400">Belum ada</span>
                  {:else if warn === 'red'}
                    <span class="flex items-center gap-1 text-xs font-semibold text-red-600">
                      <AlertTriangle class="h-3 w-3" /> Segera expired
                    </span>
                  {:else if warn === 'yellow'}
                    <span class="flex items-center gap-1 text-xs font-semibold text-amber-500">
                      <AlertTriangle class="h-3 w-3" /> Exp: {formatDate(j.passport_expiry)}
                    </span>
                  {:else}
                    <span class="text-xs text-slate-500">{formatDate(j.passport_expiry)}</span>
                  {/if}
                </td>
                <td class="px-4 py-3.5">
                  <button
                    type="button"
                    onclick={() => openDetail(j)}
                    class="flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-semibold text-primary-600 transition-colors hover:bg-primary-50"
                  >
                    Detail
                    <ChevronRight class="h-3 w-3" />
                  </button>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      {/if}
    </div>

  <!-- Kanban view -->
  {:else}
    <div class="flex-1 overflow-x-auto">
      <div class="flex h-full gap-3 p-4">
        {#each PIPELINE_STATUSES.filter(s => s.id !== 'all') as col}
          {@const colItems = jamaah.filter(j => j.pipeline_status === col.id)}
          <div class="flex h-full w-64 flex-shrink-0 flex-col rounded-2xl bg-slate-100 p-3">
            <div class="mb-3 flex items-center justify-between">
              <span class="text-xs font-bold uppercase tracking-wider text-slate-500">{col.label}</span>
              <span class="rounded-full bg-white px-2 py-0.5 text-[10px] font-bold text-slate-500">{colItems.length}</span>
            </div>
            <div class="flex-1 space-y-2 overflow-y-auto">
              {#each colItems as j}
                <button
                  type="button"
                  onclick={() => openDetail(j)}
                  class="w-full rounded-xl bg-white p-3 text-left shadow-sm transition-all hover:shadow-md"
                >
                  <p class="text-sm font-semibold text-slate-800">{j.name}</p>
                  {#if j.package_name}
                    <p class="mt-0.5 text-[11px] text-slate-500">{j.package_name}</p>
                  {/if}
                  {#if j.sisa_tagihan > 0}
                    <p class="mt-2 text-[11px] font-semibold text-red-500">Sisa {formatIDR(j.sisa_tagihan)}</p>
                  {/if}
                </button>
              {/each}
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<!-- Jamaah Detail Drawer -->
<SlideDrawer
  open={drawerOpen}
  title={selectedJamaah?.name || ''}
  width="560px"
  onClose={() => (drawerOpen = false)}
>
  {#if selectedJamaah}
    <div class="flex flex-col h-full">
      <!-- Status row -->
      <div class="flex items-center justify-between border-b border-slate-100 px-6 py-3">
        <StatusBadge status={selectedJamaah.pipeline_status} />
        <div class="flex gap-2">
          <button
            type="button"
            onclick={() => openWhatsApp(selectedJamaah.phone)}
            class="flex items-center gap-1.5 rounded-lg bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition-colors hover:bg-emerald-100"
          >
            <Phone class="h-3.5 w-3.5" />
            WhatsApp
          </button>
          <button
            type="button"
            onclick={() => { onNavigate?.('invoices'); drawerOpen = false; }}
            class="flex items-center gap-1.5 rounded-lg bg-primary-50 px-3 py-1.5 text-xs font-semibold text-primary-700 transition-colors hover:bg-primary-100"
          >
            Invoice
          </button>
        </div>
      </div>

      <!-- Tabs -->
      <div class="flex border-b border-slate-100">
        {#each DRAWER_TABS as tab}
          <button
            type="button"
            onclick={() => (activeTab = tab.id)}
            class="flex-1 py-3 text-xs font-semibold transition-colors
              {activeTab === tab.id
                ? 'border-b-2 border-primary-600 text-primary-700'
                : 'text-slate-400 hover:text-slate-600'}"
          >
            {tab.label}
          </button>
        {/each}
      </div>

      <!-- Tab content -->
      <div class="flex-1 overflow-y-auto p-6">
        {#if activeTab === 'profil'}
          <div class="space-y-4">
            <div class="rounded-xl border border-slate-100 p-4 space-y-2.5">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Identitas</h4>
              {@render InfoRow("Nama Lengkap", selectedJamaah.name)}
              {@render InfoRow("NIK", selectedJamaah.nik || '—')}
              {@render InfoRow("No. Paspor", selectedJamaah.passport_no || '—')}
              {@render InfoRow("Jenis Kelamin", selectedJamaah.gender === 'L' ? 'Laki-laki' : 'Perempuan')}
            </div>
            <div class="rounded-xl border border-slate-100 p-4 space-y-2.5">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Kontak</h4>
              {@render InfoRow("HP / WhatsApp", selectedJamaah.phone)}
              {@render InfoRow("Email", selectedJamaah.email || '—')}
            </div>
            <div class="rounded-xl border border-slate-100 p-4 space-y-2.5">
              <h4 class="text-[10px] font-bold uppercase tracking-wider text-slate-400">Paket</h4>
              {@render InfoRow("Paket", selectedJamaah.package_name || 'Belum dipilih')}
              {@render InfoRow("Tipe Kamar", selectedJamaah.room_type || '—')}
            </div>
          </div>
        {:else if activeTab === 'dokumen'}
          <div class="space-y-2">
            {#each ['KTP', 'Kartu Keluarga', 'Paspor', 'Pas Foto 4×6', 'Suntik Meningitis'] as doc}
              <div class="flex items-center justify-between rounded-xl border border-slate-100 p-3">
                <span class="text-sm text-slate-700">{doc}</span>
                <span class="rounded-full bg-slate-100 px-2 py-1 text-[10px] font-bold text-slate-500">BELUM</span>
              </div>
            {/each}
          </div>
        {:else if activeTab === 'invoice'}
          <div class="space-y-3">
            <div class="rounded-xl bg-slate-50 p-4">
              <p class="text-xs text-slate-400">Total Tagihan</p>
              <p class="text-xl font-bold text-slate-800">{formatIDR(selectedJamaah.total_invoice)}</p>
            </div>
            <div class="rounded-xl bg-emerald-50 p-4">
              <p class="text-xs text-emerald-600">Sudah Dibayar</p>
              <p class="text-xl font-bold text-emerald-700">{formatIDR(selectedJamaah.paid)}</p>
            </div>
            {#if selectedJamaah.sisa_tagihan > 0}
              <div class="rounded-xl bg-red-50 p-4">
                <p class="text-xs text-red-500">Sisa Tagihan</p>
                <p class="text-xl font-bold text-red-600">{formatIDR(selectedJamaah.sisa_tagihan)}</p>
              </div>
            {/if}
            <button
              type="button"
              onclick={() => { onNavigate?.('invoices'); drawerOpen = false; }}
              class="w-full rounded-xl bg-primary-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
            >
              Lihat Invoice Lengkap
            </button>
          </div>
        {:else if activeTab === 'catatan'}
          <div class="space-y-3">
            <textarea
              class="w-full rounded-xl border border-slate-200 p-3 text-sm text-slate-700 outline-none focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
              placeholder="Tambahkan catatan internal tentang jamaah ini..."
              rows="4"
            ></textarea>
            <button
              type="button"
              class="w-full rounded-xl bg-primary-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
            >
              Simpan Catatan
            </button>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</SlideDrawer>

{#snippet InfoRow(label, value)}
  <div class="flex items-start justify-between gap-4 text-sm">
    <span class="flex-shrink-0 text-slate-400">{label}</span>
    <span class="text-right font-medium text-slate-700">{value}</span>
  </div>
{/snippet}

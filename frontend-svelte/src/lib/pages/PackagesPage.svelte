<script>
  import { onMount } from 'svelte';
  import {
    CalendarDays,
    ChevronRight,
    Copy,
    Edit,
    ExternalLink,
    Globe,
    Hotel,
    Link2,
    Loader2,
    Lock,
    Package,
    Plane,
    Plus,
    Trash2,
    Users,
  } from 'lucide-svelte';
  import StatusBadge from '../components/StatusBadge.svelte';
  import SlideDrawer from '../components/SlideDrawer.svelte';
  import IDRInput from '../components/IDRInput.svelte';
  import { ApiService } from '../services/api';
  import { showToast } from '../services/toast.svelte.js';

  let { onNavigate, user = null } = $props();

  const STATUS_TABS = [
    { id: 'all', label: 'Semua' },
    { id: 'open', label: 'Open' },
    { id: 'draft', label: 'Draft' },
    { id: 'full', label: 'Penuh' },
    { id: 'closed', label: 'Ditutup' },
    { id: 'done', label: 'Selesai' },
  ];

  const PACKAGE_TYPES = [
    { value: 'umroh_reguler', label: 'Umroh Reguler' },
    { value: 'umroh_plus', label: 'Umroh Plus' },
    { value: 'haji_khusus', label: 'Haji Khusus' },
    { value: 'haji_onh_plus', label: 'Haji ONH Plus' },
  ];

  const STATUS_OPTIONS = [
    { value: 'draft', label: 'Draft' },
    { value: 'open', label: 'Open' },
    { value: 'full', label: 'Penuh' },
    { value: 'closed', label: 'Ditutup' },
    { value: 'done', label: 'Selesai' },
  ];

  const ROOM_FIELDS = [
    { room_type: 'quad', label: 'Quad (4 orang)' },
    { room_type: 'triple', label: 'Triple (3 orang)' },
    { room_type: 'double', label: 'Double (2 orang)' },
    { room_type: 'single', label: 'Single (1 orang)' },
  ];

  let packages = $state([]);
  let isLoading = $state(true);
  let filterStatus = $state('all');
  let drawerOpen = $state(false);
  let detailLoading = $state(false);
  let selectedPackage = $state(null);
  let formDrawerOpen = $state(false);
  let formMode = $state('create');
  let savingForm = $state(false);
  let changingStatus = $state(false);
  let publishingId = $state('');
  let deletingId = $state('');
  let formError = $state('');
  let formState = $state(createEmptyForm());

  let currentRole = $derived(user?.is_super_admin ? 'owner' : (user?.role ?? 'viewer'));
  let canEditPackages = $derived(currentRole === 'owner' || currentRole === 'admin');
  let canPublishPackages = $derived(currentRole === 'owner');
  let canDeletePackages = $derived(currentRole === 'owner');

  let filtered = $derived(
    filterStatus === 'all'
      ? packages
      : packages.filter((pkg) => pkg.status === filterStatus)
  );

  onMount(loadPackages);

  function createEmptyForm() {
    return {
      id: '',
      name: '',
      packageType: 'umroh_reguler',
      departureDate: '',
      returnDate: '',
      totalSeats: 40,
      status: 'draft',
      description: '',
      airline: '',
      flightNumberGo: '',
      flightNumberReturn: '',
      hotelMakkahName: '',
      hotelMadinahName: '',
      prices: {
        quad: 0,
        triple: 0,
        double: 0,
        single: 0,
      },
      existingPricingTiers: [],
    };
  }

  function normalizePackage(pkg) {
    const pricingTiers = [...(pkg?.pricing_tiers || [])].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    const reservedSeats = Number(pkg?.reserved_seats || 0);
    const totalSeats = Number(pkg?.total_seats || 0);
    return {
      ...pkg,
      pricing_tiers: pricingTiers,
      reserved_seats: reservedSeats,
      total_seats: totalSeats,
      available_seats: Math.max(0, totalSeats - reservedSeats),
    };
  }

  function getPackagesFromResponse(response) {
    if (Array.isArray(response?.data)) return response.data;
    if (Array.isArray(response)) return response;
    return [];
  }

  async function loadPackages() {
    isLoading = true;
    try {
      const response = await ApiService.listPackages({ pageSize: 100 });
      packages = getPackagesFromResponse(response).map(normalizePackage);
    } catch (error) {
      packages = [];
      showToast(error.message || 'Gagal memuat data paket', 'error');
    } finally {
      isLoading = false;
    }
  }

  async function openDetail(pkg) {
    drawerOpen = true;
    detailLoading = true;
    selectedPackage = normalizePackage(pkg);
    try {
      const response = await ApiService.getPackage(pkg.id);
      selectedPackage = normalizePackage(response.data ?? response);
      mergePackage(selectedPackage);
    } catch (error) {
      showToast(error.message || 'Gagal memuat detail paket', 'error');
    } finally {
      detailLoading = false;
    }
  }

  function mergePackage(pkg) {
    packages = packages.map((item) => (item.id === pkg.id ? normalizePackage(pkg) : item));
  }

  function removePackage(packageId) {
    packages = packages.filter((pkg) => pkg.id !== packageId);
    if (selectedPackage?.id === packageId) {
      selectedPackage = null;
      drawerOpen = false;
    }
  }

  function formatDate(dateStr) {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('id-ID', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  function toDateInput(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (Number.isNaN(date.getTime())) return '';
    return date.toISOString().slice(0, 10);
  }

  function formatIDR(num) {
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(num || 0);
  }

  function getLowestPrice(pkg) {
    const prices = (pkg.pricing_tiers || [])
      .map((tier) => Number(tier.price || 0))
      .filter((price) => price > 0);
    return prices.length > 0 ? Math.min(...prices) : null;
  }

  function getPublicLink(slug) {
    if (typeof window === 'undefined') {
      return `/#/paket/${slug}`;
    }
    return `${window.location.origin}/#/paket/${slug}`;
  }

  async function copyPublicLink(pkg) {
    const link = getPublicLink(pkg.slug);
    try {
      await navigator.clipboard.writeText(link);
      showToast('Link paket berhasil disalin', 'success');
    } catch {
      const textArea = document.createElement('textarea');
      textArea.value = link;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showToast('Link paket berhasil disalin', 'success');
    }
  }

  function openPublicLink(pkg) {
    if (!pkg.is_published) {
      showToast('Paket masih private. Publikasikan dulu untuk membuka halaman publik.', 'error');
      return;
    }
    window.open(getPublicLink(pkg.slug), '_blank', 'noopener,noreferrer');
  }

  async function togglePublish(pkg) {
    if (!canPublishPackages) return;
    publishingId = pkg.id;
    try {
      const response = await ApiService.updatePackage(pkg.id, {
        is_published: !pkg.is_published,
      });
      const updated = normalizePackage(response.data ?? response);
      mergePackage(updated);
      if (selectedPackage?.id === updated.id) {
        selectedPackage = updated;
      }
      showToast(
        updated.is_published ? 'Paket berhasil dipublikasikan' : 'Paket dikembalikan ke mode internal',
        'success'
      );
    } catch (error) {
      showToast(error.message || 'Gagal mengubah publikasi paket', 'error');
    } finally {
      publishingId = '';
    }
  }

  async function updatePackageStatus(pkg, status) {
    if (!canEditPackages || status === pkg.status) return;
    changingStatus = true;
    try {
      const response = await ApiService.updatePackageStatus(pkg.id, status);
      const updated = normalizePackage(response.data ?? response);
      mergePackage(updated);
      if (selectedPackage?.id === updated.id) {
        selectedPackage = updated;
      }
      showToast('Status paket diperbarui', 'success');
    } catch (error) {
      showToast(error.message || 'Gagal memperbarui status paket', 'error');
    } finally {
      changingStatus = false;
    }
  }

  async function deletePackage(pkg) {
    if (!canDeletePackages) return;
    if (!confirm(`Hapus paket "${pkg.name}"? Tindakan ini tidak dapat dibatalkan.`)) {
      return;
    }
    deletingId = pkg.id;
    try {
      await ApiService.deletePackage(pkg.id);
      removePackage(pkg.id);
      showToast('Paket berhasil dihapus', 'success');
    } catch (error) {
      showToast(error.message || 'Gagal menghapus paket', 'error');
    } finally {
      deletingId = '';
    }
  }

  function openCreateForm() {
    if (!canEditPackages) return;
    formMode = 'create';
    formError = '';
    formState = createEmptyForm();
    formDrawerOpen = true;
  }

  function packageToForm(pkg) {
    const prices = { quad: 0, triple: 0, double: 0, single: 0 };
    for (const tier of pkg.pricing_tiers || []) {
      prices[tier.room_type] = Number(tier.price || 0);
    }

    return {
      id: pkg.id,
      name: pkg.name || '',
      packageType: pkg.package_type || 'umroh_reguler',
      departureDate: toDateInput(pkg.departure_date),
      returnDate: toDateInput(pkg.return_date),
      totalSeats: Number(pkg.total_seats || 0),
      status: pkg.status || 'draft',
      description: pkg.description || '',
      airline: pkg.airline || '',
      flightNumberGo: pkg.flight_number_go || '',
      flightNumberReturn: pkg.flight_number_return || '',
      hotelMakkahName: pkg.hotel_makkah_name || '',
      hotelMadinahName: pkg.hotel_madinah_name || '',
      prices,
      existingPricingTiers: pkg.pricing_tiers || [],
    };
  }

  function openEditForm() {
    if (!canEditPackages || !selectedPackage) return;
    formMode = 'edit';
    formError = '';
    formState = packageToForm(selectedPackage);
    formDrawerOpen = true;
  }

  function buildTierPayloads() {
    let sortOrder = 0;
    return ROOM_FIELDS
      .map((room) => {
        const price = Number(formState.prices[room.room_type] || 0);
        if (price <= 0) return null;
        const existing = (formState.existingPricingTiers || []).find((tier) => tier.room_type === room.room_type);
        return {
          id: existing?.id,
          room_type: room.room_type,
          price,
          label: room.label,
          is_early_bird: false,
          sort_order: sortOrder++,
        };
      })
      .filter(Boolean);
  }

  function buildPackagePayload() {
    return {
      name: formState.name.trim(),
      package_type: formState.packageType,
      departure_date: formState.departureDate || undefined,
      return_date: formState.returnDate || undefined,
      total_seats: Number(formState.totalSeats || 0),
      description: formState.description.trim() || undefined,
      airline: formState.airline.trim() || undefined,
      flight_number_go: formState.flightNumberGo.trim() || undefined,
      flight_number_return: formState.flightNumberReturn.trim() || undefined,
      hotel_makkah_name: formState.hotelMakkahName.trim() || undefined,
      hotel_madinah_name: formState.hotelMadinahName.trim() || undefined,
    };
  }

  function validateForm() {
    if (!formState.name.trim()) return 'Nama paket wajib diisi.';
    if (!formState.departureDate) return 'Tanggal berangkat wajib diisi.';
    if (!formState.returnDate) return 'Tanggal pulang wajib diisi.';
    if (new Date(formState.returnDate) < new Date(formState.departureDate)) {
      return 'Tanggal pulang tidak boleh lebih awal dari tanggal berangkat.';
    }
    if (Number(formState.totalSeats || 0) < 1) {
      return 'Total kursi minimal 1.';
    }
    if (buildTierPayloads().length === 0) {
      return 'Minimal satu harga kamar harus diisi.';
    }
    return '';
  }

  async function syncPricingTiers(packageId, existingPricingTiers, desiredPricingTiers) {
    const existingByRoom = new Map((existingPricingTiers || []).map((tier) => [tier.room_type, tier]));
    const desiredRooms = new Set(desiredPricingTiers.map((tier) => tier.room_type));

    for (const tier of desiredPricingTiers) {
      const existing = existingByRoom.get(tier.room_type);
      if (existing) {
        await ApiService.updatePricingTier(packageId, existing.id, {
          room_type: tier.room_type,
          price: tier.price,
          label: tier.label,
          is_early_bird: false,
          sort_order: tier.sort_order,
        });
      } else {
        await ApiService.createPricingTier(packageId, {
          room_type: tier.room_type,
          price: tier.price,
          label: tier.label,
          is_early_bird: false,
          sort_order: tier.sort_order,
        });
      }
    }

    for (const existing of existingPricingTiers || []) {
      if (!desiredRooms.has(existing.room_type)) {
        await ApiService.deletePricingTier(packageId, existing.id);
      }
    }
  }

  async function saveForm() {
    if (!canEditPackages) return;

    formError = validateForm();
    if (formError) {
      return;
    }

    savingForm = true;
    try {
      const tierPayloads = buildTierPayloads();
      let savedPackage;

      if (formMode === 'create') {
        const response = await ApiService.createPackage({
          ...buildPackagePayload(),
          pricing_tiers: tierPayloads,
        });
        savedPackage = normalizePackage(response.data ?? response);
      } else {
        await ApiService.updatePackage(formState.id, buildPackagePayload());
        await syncPricingTiers(formState.id, formState.existingPricingTiers, tierPayloads);
        await ApiService.updatePackageStatus(formState.id, formState.status);
        const response = await ApiService.getPackage(formState.id);
        savedPackage = normalizePackage(response.data ?? response);
      }

      if (formMode === 'create') {
        packages = [savedPackage, ...packages];
      } else {
        mergePackage(savedPackage);
      }

      selectedPackage = savedPackage;
      drawerOpen = true;
      formDrawerOpen = false;
      showToast(
        formMode === 'create' ? 'Paket berhasil dibuat' : 'Paket berhasil diperbarui',
        'success'
      );
    } catch (error) {
      formError = error.message || 'Gagal menyimpan paket';
    } finally {
      savingForm = false;
    }
  }

  function typeLabel(packageType) {
    return PACKAGE_TYPES.find((type) => type.value === packageType)?.label || packageType;
  }
</script>

<div class="flex h-screen flex-col">
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Paket & Harga</h1>
        <p class="mt-0.5 text-sm text-slate-500">{packages.length} paket tersedia</p>
      </div>
      {#if canEditPackages}
        <button
          type="button"
          onclick={openCreateForm}
          class="flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-primary-600/30 transition-all hover:bg-primary-700 hover:shadow-md"
        >
          <Plus class="h-4 w-4" />
          Buat Paket
        </button>
      {/if}
    </div>

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

  <div class="flex-1 overflow-y-auto bg-slate-50 p-6">
    {#if isLoading}
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each [1, 2, 3] as item}
          <div class="h-52 animate-pulse rounded-2xl bg-white" aria-hidden="true">{item}</div>
        {/each}
      </div>
    {:else if filtered.length === 0}
      <div class="flex flex-col items-center justify-center py-24 text-slate-400">
        <Package class="mb-3 h-12 w-12 opacity-30" />
        <p class="font-medium">Belum ada paket</p>
        <p class="mt-1 text-sm">
          {#if canEditPackages}
            Buat paket pertama untuk mulai membagikan penawaran ke jamaah.
          {:else}
            Belum ada paket yang bisa ditampilkan.
          {/if}
        </p>
      </div>
    {:else}
      <div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {#each filtered as pkg}
          <button
            type="button"
            onclick={() => openDetail(pkg)}
            class="group relative rounded-2xl bg-white p-5 text-left shadow-sm ring-1 ring-slate-200/60 transition-all hover:shadow-md hover:ring-primary-200"
          >
            <div class="mb-3 flex items-center justify-between">
              <StatusBadge status={pkg.status} size="xs" />
              <span class="flex items-center gap-1 text-[11px] font-medium text-slate-400">
                {#if pkg.is_published}
                  <Globe class="h-3 w-3" /> Publik
                {:else}
                  <Lock class="h-3 w-3" /> Internal
                {/if}
              </span>
            </div>

            <h3 class="mb-1 text-[15px] font-bold leading-snug text-slate-800 group-hover:text-primary-700">
              {pkg.name}
            </h3>
            <p class="text-[12px] font-medium text-slate-400">{typeLabel(pkg.package_type)}</p>

            <div class="mt-3 space-y-1.5 text-[12px] text-slate-500">
              <div class="flex items-center gap-1.5">
                <CalendarDays class="h-3.5 w-3.5 flex-shrink-0" />
                {formatDate(pkg.departure_date)} - {formatDate(pkg.return_date)}
              </div>
              <div class="flex items-center gap-1.5">
                <Plane class="h-3.5 w-3.5 flex-shrink-0" />
                {pkg.airline || '-'} {#if pkg.flight_number_go}&middot; {pkg.flight_number_go}{/if}
              </div>
              <div class="flex items-center gap-1.5">
                <Hotel class="h-3.5 w-3.5 flex-shrink-0" />
                {pkg.hotel_makkah_name || '-'}
              </div>
            </div>

            <div class="mt-4">
              <div class="mb-1 flex items-center justify-between text-[11px]">
                <span class="text-slate-400">Kuota terisi</span>
                <span class="font-semibold text-slate-600">{pkg.reserved_seats}/{pkg.total_seats}</span>
              </div>
              <div class="h-1.5 overflow-hidden rounded-full bg-slate-100">
                <div
                  class="h-full rounded-full {pkg.reserved_seats >= pkg.total_seats ? 'bg-red-400' : 'bg-emerald-400'}"
                  style="width: {pkg.total_seats > 0 ? Math.min(100, Math.round((pkg.reserved_seats / pkg.total_seats) * 100)) : 0}%"
                ></div>
              </div>
            </div>

            <div class="mt-4 border-t border-slate-100 pt-3">
              <p class="text-[11px] text-slate-400">Mulai dari</p>
              {#if getLowestPrice(pkg)}
                <p class="text-sm font-bold text-primary-700">{formatIDR(getLowestPrice(pkg))}</p>
              {:else}
                <p class="text-sm font-semibold text-slate-400">Harga belum diatur</p>
              {/if}
            </div>

            <ChevronRight class="absolute right-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-300 group-hover:text-primary-400" />
          </button>
        {/each}
      </div>
    {/if}
  </div>
</div>

<SlideDrawer
  open={drawerOpen}
  title={selectedPackage?.name || 'Detail Paket'}
  width="640px"
  onClose={() => (drawerOpen = false)}
>
  {#if detailLoading}
    <div class="flex h-full min-h-[320px] items-center justify-center gap-3 text-slate-500">
      <Loader2 class="h-5 w-5 animate-spin" />
      <span>Memuat detail paket...</span>
    </div>
  {:else if selectedPackage}
    <div class="space-y-6 p-6">
      <div class="flex flex-wrap items-center gap-3">
        <StatusBadge status={selectedPackage.status} />
        <span class="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
          {#if selectedPackage.is_published}
            <Globe class="h-3.5 w-3.5" /> Publik
          {:else}
            <Lock class="h-3.5 w-3.5" /> Internal
          {/if}
        </span>
        <span class="inline-flex rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-700">
          {typeLabel(selectedPackage.package_type)}
        </span>
      </div>

      <div class="rounded-2xl border border-slate-100 p-4">
        <div class="mb-3 flex items-center gap-2">
          <Link2 class="h-4 w-4 text-slate-500" />
          <h3 class="text-sm font-bold text-slate-800">Link Publik Paket</h3>
        </div>
        <div class="rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-600">
          {getPublicLink(selectedPackage.slug)}
        </div>
        <div class="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            onclick={() => copyPublicLink(selectedPackage)}
            class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
          >
            <Copy class="h-4 w-4" />
            Salin Link
          </button>
          <button
            type="button"
            onclick={() => openPublicLink(selectedPackage)}
            disabled={!selectedPackage.is_published}
            class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <ExternalLink class="h-4 w-4" />
            Buka Halaman
          </button>
          {#if canPublishPackages}
            <button
              type="button"
              onclick={() => togglePublish(selectedPackage)}
              disabled={publishingId === selectedPackage.id}
              class="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {#if publishingId === selectedPackage.id}
                <Loader2 class="h-4 w-4 animate-spin" />
              {:else if selectedPackage.is_published}
                <Lock class="h-4 w-4" />
              {:else}
                <Globe class="h-4 w-4" />
              {/if}
              {selectedPackage.is_published ? 'Jadikan Internal' : 'Publikasikan'}
            </button>
          {/if}
        </div>
        <p class="mt-3 text-xs text-slate-400">
          {#if selectedPackage.is_published}
            Link aktif dan bisa dibagikan ke calon jamaah.
          {:else}
            Link sudah tersedia tetapi belum bisa diakses publik sampai owner mempublikasikan paket.
          {/if}
        </p>
      </div>

      <div class="rounded-2xl border border-slate-100 p-4">
        <div class="mb-3 flex items-center justify-between gap-3">
          <h3 class="text-sm font-bold text-slate-800">Status Paket</h3>
          {#if canEditPackages}
            <select
              value={selectedPackage.status}
              disabled={changingStatus}
              onchange={(event) => updatePackageStatus(selectedPackage, event.currentTarget.value)}
              class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-100 disabled:opacity-60"
            >
              {#each STATUS_OPTIONS as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
          {/if}
        </div>
        <p class="text-sm text-slate-500">
          Status operasional paket dipakai untuk filter internal dan kontrol kuota.
        </p>
      </div>

      <div class="rounded-2xl border border-slate-100 p-4 space-y-3">
        <h3 class="text-sm font-bold text-slate-800">Info Keberangkatan</h3>
        {@render InfoRow('Tanggal Berangkat', formatDate(selectedPackage.departure_date))}
        {@render InfoRow('Tanggal Pulang', formatDate(selectedPackage.return_date))}
        {@render InfoRow('Maskapai', selectedPackage.airline || '-')}
        {@render InfoRow('Flight Berangkat', selectedPackage.flight_number_go || '-')}
        {@render InfoRow('Flight Pulang', selectedPackage.flight_number_return || '-')}
        {@render InfoRow('Hotel Makkah', selectedPackage.hotel_makkah_name || '-')}
        {@render InfoRow('Hotel Madinah', selectedPackage.hotel_madinah_name || '-')}
        {@render InfoRow('Deskripsi', selectedPackage.description || '-')}
      </div>

      <div class="rounded-2xl border border-slate-100 p-4">
        <h3 class="mb-3 text-sm font-bold text-slate-800">Harga per Tipe Kamar</h3>
        {#if selectedPackage.pricing_tiers?.length > 0}
          <table class="w-full text-sm">
            <thead>
              <tr class="text-left text-xs text-slate-400">
                <th class="pb-2 font-semibold">Tipe</th>
                <th class="pb-2 text-right font-semibold">Harga</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-50">
              {#each ROOM_FIELDS as room}
                {@const tier = selectedPackage.pricing_tiers.find((item) => item.room_type === room.room_type)}
                {#if tier}
                  <tr>
                    <td class="py-2 text-slate-700">{room.label}</td>
                    <td class="py-2 text-right font-semibold text-slate-800">{formatIDR(tier.price)}</td>
                  </tr>
                {/if}
              {/each}
            </tbody>
          </table>
        {:else}
          <p class="text-sm text-slate-400">Harga kamar belum diatur.</p>
        {/if}
      </div>

      <div class="rounded-2xl border border-slate-100 p-4">
        <h3 class="mb-3 text-sm font-bold text-slate-800">Kuota</h3>
        <div class="mb-2 flex items-end justify-between">
          <span class="text-3xl font-bold text-slate-800">{selectedPackage.reserved_seats}</span>
          <span class="text-slate-400">/ {selectedPackage.total_seats} kursi</span>
        </div>
        <div class="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            class="h-full rounded-full {selectedPackage.reserved_seats >= selectedPackage.total_seats ? 'bg-red-400' : 'bg-emerald-400'}"
            style="width: {selectedPackage.total_seats > 0 ? Math.min(100, Math.round((selectedPackage.reserved_seats / selectedPackage.total_seats) * 100)) : 0}%"
          ></div>
        </div>
        <p class="mt-1.5 text-xs text-slate-400">{selectedPackage.available_seats} kursi tersisa</p>
      </div>

      <div class="flex flex-wrap gap-3">
        {#if canEditPackages}
          <button
            type="button"
            onclick={openEditForm}
            class="flex items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
          >
            <Edit class="h-4 w-4" />
            Edit Paket
          </button>
        {/if}
        {#if canDeletePackages}
          <button
            type="button"
            onclick={() => deletePackage(selectedPackage)}
            disabled={deletingId === selectedPackage.id}
            class="flex items-center justify-center gap-2 rounded-xl border border-red-200 px-4 py-2.5 text-sm font-semibold text-red-600 transition-colors hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {#if deletingId === selectedPackage.id}
              <Loader2 class="h-4 w-4 animate-spin" />
            {:else}
              <Trash2 class="h-4 w-4" />
            {/if}
            Hapus Paket
          </button>
        {/if}
        <button
          type="button"
          onclick={() => {
            onNavigate?.('crm');
            drawerOpen = false;
          }}
          class="flex items-center justify-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
        >
          <Users class="h-4 w-4" />
          Lihat CRM
        </button>
      </div>
    </div>
  {/if}
</SlideDrawer>

<SlideDrawer
  open={formDrawerOpen}
  title={formMode === 'create' ? 'Buat Paket Baru' : 'Edit Paket'}
  width="700px"
  onClose={() => (formDrawerOpen = false)}
>
  <div class="space-y-6 p-6">
    {#if formError}
      <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        {formError}
      </div>
    {/if}

    <div class="grid gap-4 sm:grid-cols-2">
      <div class="sm:col-span-2">
        <label class="mb-1 block text-sm font-medium text-slate-700">Nama Paket</label>
        <input
          type="text"
          bind:value={formState.name}
          placeholder="Contoh: Umroh Reguler Ramadan 2027"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Jenis Paket</label>
        <select
          bind:value={formState.packageType}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        >
          {#each PACKAGE_TYPES as type}
            <option value={type.value}>{type.label}</option>
          {/each}
        </select>
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Status</label>
        <select
          bind:value={formState.status}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        >
          {#each STATUS_OPTIONS as option}
            <option value={option.value}>{option.label}</option>
          {/each}
        </select>
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Tanggal Berangkat</label>
        <input
          type="date"
          bind:value={formState.departureDate}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Tanggal Pulang</label>
        <input
          type="date"
          bind:value={formState.returnDate}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Total Kursi</label>
        <input
          type="number"
          min="1"
          bind:value={formState.totalSeats}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Maskapai</label>
        <input
          type="text"
          bind:value={formState.airline}
          placeholder="Contoh: Saudi Airlines"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Flight Berangkat</label>
        <input
          type="text"
          bind:value={formState.flightNumberGo}
          placeholder="Contoh: SV812"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Flight Pulang</label>
        <input
          type="text"
          bind:value={formState.flightNumberReturn}
          placeholder="Contoh: SV813"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Hotel Makkah</label>
        <input
          type="text"
          bind:value={formState.hotelMakkahName}
          placeholder="Contoh: Hilton Makkah"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div>
        <label class="mb-1 block text-sm font-medium text-slate-700">Hotel Madinah</label>
        <input
          type="text"
          bind:value={formState.hotelMadinahName}
          placeholder="Contoh: Anwar Al Madinah"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>

      <div class="sm:col-span-2">
        <label class="mb-1 block text-sm font-medium text-slate-700">Deskripsi Paket</label>
        <textarea
          rows="4"
          bind:value={formState.description}
          placeholder="Ringkasan itinerary, fasilitas, atau catatan paket"
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        ></textarea>
      </div>
    </div>

    <div class="rounded-2xl border border-slate-100 p-4">
      <h3 class="mb-4 text-sm font-bold text-slate-800">Harga per Tipe Kamar</h3>
      <div class="grid gap-4 sm:grid-cols-2">
        {#each ROOM_FIELDS as room}
          <IDRInput bind:value={formState.prices[room.room_type]} label={room.label} />
        {/each}
      </div>
    </div>

    <div class="flex flex-wrap justify-end gap-3 border-t border-slate-100 pt-4">
      <button
        type="button"
        onclick={() => (formDrawerOpen = false)}
        class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
      >
        Batal
      </button>
      <button
        type="button"
        onclick={saveForm}
        disabled={savingForm}
        class="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {#if savingForm}
          <Loader2 class="h-4 w-4 animate-spin" />
        {/if}
        {formMode === 'create' ? 'Simpan Paket' : 'Perbarui Paket'}
      </button>
    </div>
  </div>
</SlideDrawer>

{#snippet InfoRow(label, value)}
  <div class="flex items-start justify-between gap-4 text-sm">
    <span class="flex-shrink-0 text-slate-400">{label}</span>
    <span class="text-right font-medium text-slate-700">{value}</span>
  </div>
{/snippet}

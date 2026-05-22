<script>
  import { onMount } from 'svelte';
  import {
    Copy,
    Eye,
    FileSignature,
    FileText,
    Link2,
    Loader2,
    Pencil,
    Plus,
    Save,
    Send,
    ShieldCheck,
    Sparkles,
    Trash2,
  } from 'lucide-svelte';
  import SlideDrawer from '../components/SlideDrawer.svelte';
  import { ApiService } from '../services/api';
  import { showToast } from '../services/toast.svelte.js';

  let { user = null } = $props();

  const PACKAGE_TYPES = [
    { value: '', label: 'Semua Paket' },
    { value: 'umroh_reguler', label: 'Umroh Reguler' },
    { value: 'umroh_plus', label: 'Umroh Plus' },
    { value: 'haji_khusus', label: 'Haji Khusus' },
    { value: 'haji_onh_plus', label: 'Haji ONH Plus' },
  ];

  const CONTRACT_STATUSES = [
    { value: '', label: 'Semua Status' },
    { value: 'terkirim', label: 'Terkirim' },
    { value: 'ditandatangani', label: 'Ditandatangani' },
    { value: 'expired', label: 'Expired' },
  ];

  const VARIABLES = [
    'nama_jamaah',
    'no_paspor',
    'nama_paket',
    'tanggal_berangkat',
    'tanggal_pulang',
    'tipe_kamar',
    'harga_paket',
    'skema_bayar',
    'nama_travel',
    'tanggal_kontrak',
    'ketentuan_refund',
  ];

  const SAMPLE_VALUES = {
    nama_jamaah: 'Ahmad Fauzi',
    no_paspor: 'X1234567',
    nama_paket: 'Umroh Reguler Ramadan 2027',
    tanggal_berangkat: '12 Maret 2027',
    tanggal_pulang: '24 Maret 2027',
    tipe_kamar: 'Quad',
    harga_paket: 'Rp 29.500.000',
    skema_bayar: 'DP Rp 8.000.000, pelunasan H-45',
    nama_travel: 'Jamaah.in Travel',
    tanggal_kontrak: '22 Mei 2026',
    ketentuan_refund: 'Pembatalan >45 hari: potongan 10%. Pembatalan <30 hari: mengikuti biaya vendor aktual.',
  };

  let templates = $state([]);
  let contracts = $state([]);
  let isLoadingTemplates = $state(true);
  let isLoadingContracts = $state(true);
  let selectedType = $state('');
  let selectedStatus = $state('');
  let drawerOpen = $state(false);
  let previewOpen = $state(false);
  let generateOpen = $state(false);
  let saving = $state(false);
  let generating = $state(false);
  let deletingId = $state('');
  let previewLoading = $state(false);
  let previewHtml = $state('');
  let previewTitle = $state('');
  let formError = $state('');
  let generateError = $state('');
  let editor = $state(createEmptyTemplate());
  let generator = $state(createEmptyGenerator());

  let currentRole = $derived(user?.is_super_admin ? 'owner' : (user?.role ?? 'viewer'));
  let canEditContracts = $derived(currentRole === 'owner' || currentRole === 'admin');

  let filteredTemplates = $derived(
    selectedType
      ? templates.filter((tpl) => (tpl.package_type || '') === selectedType)
      : templates
  );

  onMount(async () => {
    await Promise.all([loadTemplates(), loadContracts()]);
  });

  function createEmptyTemplate() {
    return {
      id: '',
      name: '',
      package_type: '',
      content: `PERJANJIAN PERJALANAN UMRAH\n\nSaya yang bertanda tangan di bawah ini {{nama_jamaah}} dengan nomor paspor {{no_paspor}} setuju mengikuti paket {{nama_paket}} pada tanggal {{tanggal_berangkat}} sampai {{tanggal_pulang}}.\n\nTipe kamar: {{tipe_kamar}}\nHarga paket: {{harga_paket}}\nSkema bayar: {{skema_bayar}}\n\nDengan ini saya menyetujui seluruh ketentuan perjalanan dari {{nama_travel}}, termasuk kebijakan refund berikut:\n{{ketentuan_refund}}\n\nKontrak ini dibuat pada {{tanggal_kontrak}}.`,
      is_active: true,
    };
  }

  function createEmptyGenerator() {
    return {
      template_id: '',
      recipient_name: '',
      recipient_phone: '',
      recipient_email: '',
      package_type: '',
      expires_in_days: 7,
      variables: { ...SAMPLE_VALUES },
    };
  }

  function typeLabel(value) {
    return PACKAGE_TYPES.find((item) => item.value === value)?.label || 'Semua Paket';
  }

  function statusTone(status) {
    switch (status) {
      case 'ditandatangani':
        return 'bg-emerald-50 text-emerald-700';
      case 'expired':
        return 'bg-rose-50 text-rose-700';
      default:
        return 'bg-amber-50 text-amber-700';
    }
  }

  function statusLabel(status) {
    return CONTRACT_STATUSES.find((item) => item.value === status)?.label || status;
  }

  function renderContent(content) {
    return String(content || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  }

  function publicLink(token) {
    if (typeof window === 'undefined') return `/#/kontrak/${token}`;
    return `${window.location.origin}/#/kontrak/${token}`;
  }

  function formatDateTime(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString('id-ID', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  async function loadTemplates() {
    isLoadingTemplates = true;
    try {
      const response = await ApiService.listContractTemplates(true);
      templates = response.data ?? response ?? [];
    } catch (error) {
      templates = [];
      showToast(error.message || 'Gagal memuat template kontrak', 'error');
    } finally {
      isLoadingTemplates = false;
    }
  }

  async function loadContracts() {
    isLoadingContracts = true;
    try {
      const response = await ApiService.listContracts(selectedStatus);
      contracts = response.data ?? response ?? [];
    } catch (error) {
      contracts = [];
      showToast(error.message || 'Gagal memuat kontrak yang dikirim', 'error');
    } finally {
      isLoadingContracts = false;
    }
  }

  function openCreateDrawer() {
    if (!canEditContracts) return;
    editor = createEmptyTemplate();
    formError = '';
    drawerOpen = true;
  }

  function openEditDrawer(template) {
    if (!canEditContracts) return;
    editor = {
      id: template.id,
      name: template.name,
      package_type: template.package_type || '',
      content: template.content,
      is_active: template.is_active,
    };
    formError = '';
    drawerOpen = true;
  }

  function openGenerateDrawer(template = null) {
    if (!canEditContracts) return;
    generator = createEmptyGenerator();
    if (template) {
      generator.template_id = template.id;
      generator.package_type = template.package_type || '';
    }
    generateError = '';
    generateOpen = true;
  }

  function insertVariable(variableName) {
    editor.content = `${editor.content} {{${variableName}}}`.trim();
  }

  async function openPreview(template = editor) {
    previewOpen = true;
    previewLoading = true;
    previewTitle = template.name || 'Preview Template';
    try {
      const response = await ApiService.previewContractTemplate({
        content: template.content,
        data: SAMPLE_VALUES,
      });
      previewHtml = renderContent((response.data ?? response)?.rendered || '');
    } catch (error) {
      previewHtml = '';
      showToast(error.message || 'Gagal menampilkan preview kontrak', 'error');
    } finally {
      previewLoading = false;
    }
  }

  async function saveTemplate() {
    if (!canEditContracts) return;
    formError = '';
    if (!editor.name.trim()) {
      formError = 'Nama template wajib diisi.';
      return;
    }
    if (!editor.content.trim()) {
      formError = 'Isi template wajib diisi.';
      return;
    }

    saving = true;
    try {
      let response;
      const payload = {
        name: editor.name.trim(),
        package_type: editor.package_type || undefined,
        content: editor.content.trim(),
        is_active: editor.is_active,
      };
      if (editor.id) {
        response = await ApiService.updateContractTemplate(editor.id, payload);
      } else {
        response = await ApiService.createContractTemplate(payload);
      }
      const saved = response.data ?? response;
      if (editor.id) {
        templates = templates.map((tpl) => (tpl.id === saved.id ? saved : tpl));
      } else {
        templates = [saved, ...templates];
      }
      drawerOpen = false;
      showToast(editor.id ? 'Template kontrak diperbarui' : 'Template kontrak dibuat', 'success');
    } catch (error) {
      formError = error.message || 'Gagal menyimpan template';
    } finally {
      saving = false;
    }
  }

  async function saveContractGeneration() {
    if (!canEditContracts) return;
    generateError = '';
    if (!generator.template_id) {
      generateError = 'Pilih template kontrak terlebih dahulu.';
      return;
    }
    if (!generator.recipient_name.trim()) {
      generateError = 'Nama jamaah wajib diisi.';
      return;
    }

    generating = true;
    try {
      const payload = {
        template_id: generator.template_id,
        recipient_name: generator.recipient_name.trim(),
        recipient_phone: generator.recipient_phone.trim() || undefined,
        recipient_email: generator.recipient_email.trim() || undefined,
        package_type: generator.package_type || undefined,
        expires_in_days: Number(generator.expires_in_days || 7),
        variables: Object.fromEntries(
          Object.entries(generator.variables)
            .map(([key, value]) => [key, String(value || '').trim()])
            .filter(([, value]) => value)
        ),
      };
      const response = await ApiService.createContract(payload);
      const saved = response.data ?? response;
      contracts = [saved, ...contracts];
      generateOpen = false;
      showToast('Kontrak berhasil digenerate', 'success');
    } catch (error) {
      generateError = error.message || 'Gagal generate kontrak';
    } finally {
      generating = false;
    }
  }

  async function deleteTemplate(template) {
    if (!canEditContracts) return;
    if (!confirm(`Hapus template "${template.name}"?`)) return;
    deletingId = template.id;
    try {
      await ApiService.deleteContractTemplate(template.id);
      templates = templates.filter((tpl) => tpl.id !== template.id);
      showToast('Template kontrak dihapus', 'success');
    } catch (error) {
      showToast(error.message || 'Gagal menghapus template kontrak', 'error');
    } finally {
      deletingId = '';
    }
  }

  async function copySigningLink(contract) {
    try {
      await navigator.clipboard.writeText(publicLink(contract.public_token));
      showToast('Link kontrak disalin', 'success');
    } catch {
      showToast('Gagal menyalin link kontrak', 'error');
    }
  }

  function fillGeneratorVariable(key, value) {
    generator.variables = {
      ...generator.variables,
      [key]: value,
    };
  }
</script>

<div class="flex h-screen flex-col bg-slate-50">
  <div class="border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between gap-4">
      <div>
        <h1 class="text-xl font-bold text-slate-800">E-Kontrak</h1>
        <p class="mt-0.5 text-sm text-slate-500">Kelola template, generate kontrak per jamaah, dan bagikan link tanda tangan 7 hari.</p>
      </div>
      <div class="flex flex-wrap gap-2">
        {#if canEditContracts}
          <button
            type="button"
            onclick={() => openGenerateDrawer()}
            class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700 transition-colors hover:bg-slate-50"
          >
            <Send class="h-4 w-4" />
            Generate Kontrak
          </button>
          <button
            type="button"
            onclick={openCreateDrawer}
            class="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700"
          >
            <Plus class="h-4 w-4" />
            Template Baru
          </button>
        {/if}
      </div>
    </div>

    <div class="mt-4 flex flex-wrap items-center gap-3">
      <select
        bind:value={selectedType}
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-100"
      >
        {#each PACKAGE_TYPES as item}
          <option value={item.value}>{item.label}</option>
        {/each}
      </select>
      <select
        bind:value={selectedStatus}
        onchange={loadContracts}
        class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-primary-400 focus:outline-none focus:ring-2 focus:ring-primary-100"
      >
        {#each CONTRACT_STATUSES as item}
          <option value={item.value}>{item.label}</option>
        {/each}
      </select>
      <div class="flex items-center gap-2 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
        <ShieldCheck class="h-4 w-4" />
        Phase 3.1: generate + public signing
      </div>
    </div>
  </div>

  <div class="grid flex-1 gap-6 overflow-y-auto p-6 xl:grid-cols-[1.1fr_0.9fr]">
    <section class="space-y-4">
      <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center gap-2">
          <FileText class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-bold text-slate-800">Template Kontrak</h2>
        </div>

        {#if isLoadingTemplates}
          <div class="flex items-center justify-center gap-3 py-20 text-slate-500">
            <Loader2 class="h-5 w-5 animate-spin" />
            <span>Memuat template...</span>
          </div>
        {:else if filteredTemplates.length === 0}
          <div class="flex flex-col items-center justify-center py-20 text-center text-slate-400">
            <FileText class="mb-3 h-12 w-12 opacity-30" />
            <p class="font-medium">Belum ada template kontrak</p>
            <p class="mt-1 text-sm">Buat template untuk paket reguler, plus, atau haji khusus.</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each filteredTemplates as template}
              <article class="rounded-2xl border border-slate-200 p-4">
                <div class="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <h3 class="text-sm font-bold text-slate-800">{template.name}</h3>
                      <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                        {typeLabel(template.package_type || '')}
                      </span>
                      <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold {template.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}">
                        {template.is_active ? 'Aktif' : 'Nonaktif'}
                      </span>
                    </div>
                    <p class="mt-2 line-clamp-3 text-sm leading-relaxed text-slate-500">
                      {template.content}
                    </p>
                  </div>

                  <div class="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      onclick={() => openPreview(template)}
                      class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50"
                    >
                      <Eye class="h-3.5 w-3.5" />
                      Preview
                    </button>
                    {#if canEditContracts}
                      <button
                        type="button"
                        onclick={() => openGenerateDrawer(template)}
                        class="inline-flex items-center gap-1 rounded-lg border border-emerald-200 px-3 py-1.5 text-xs font-semibold text-emerald-700 transition-colors hover:bg-emerald-50"
                      >
                        <FileSignature class="h-3.5 w-3.5" />
                        Generate
                      </button>
                      <button
                        type="button"
                        onclick={() => openEditDrawer(template)}
                        class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50"
                      >
                        <Pencil class="h-3.5 w-3.5" />
                        Edit
                      </button>
                      <button
                        type="button"
                        onclick={() => deleteTemplate(template)}
                        disabled={deletingId === template.id}
                        class="inline-flex items-center gap-1 rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 transition-colors hover:bg-red-50 disabled:opacity-50"
                      >
                        {#if deletingId === template.id}
                          <Loader2 class="h-3.5 w-3.5 animate-spin" />
                        {:else}
                          <Trash2 class="h-3.5 w-3.5" />
                        {/if}
                        Hapus
                      </button>
                    {/if}
                  </div>
                </div>
              </article>
            {/each}
          </div>
        {/if}
      </div>
    </section>

    <aside class="space-y-4">
      <div class="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center gap-2">
          <Link2 class="h-5 w-5 text-primary-600" />
          <h2 class="text-lg font-bold text-slate-800">Kontrak Terkirim</h2>
        </div>

        {#if isLoadingContracts}
          <div class="flex items-center justify-center gap-3 py-20 text-slate-500">
            <Loader2 class="h-5 w-5 animate-spin" />
            <span>Memuat kontrak...</span>
          </div>
        {:else if contracts.length === 0}
          <div class="flex flex-col items-center justify-center py-16 text-center text-slate-400">
            <FileSignature class="mb-3 h-12 w-12 opacity-30" />
            <p class="font-medium">Belum ada kontrak yang digenerate</p>
            <p class="mt-1 text-sm">Generate kontrak dari template untuk mulai kirim link ke jamaah.</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each contracts as contract}
              <article class="rounded-2xl border border-slate-200 p-4">
                <div class="flex items-start justify-between gap-3">
                  <div>
                    <div class="flex flex-wrap items-center gap-2">
                      <h3 class="text-sm font-bold text-slate-800">{contract.recipient_name}</h3>
                      <span class="rounded-full px-2.5 py-1 text-[11px] font-semibold {statusTone(contract.status)}">
                        {statusLabel(contract.status)}
                      </span>
                    </div>
                    <p class="mt-1 text-xs text-slate-500">{contract.template_name}</p>
                    <p class="mt-2 text-xs text-slate-500">Expired: {formatDateTime(contract.expires_at)}</p>
                    {#if contract.signed_at}
                      <p class="mt-1 text-xs text-emerald-700">Signed: {formatDateTime(contract.signed_at)}</p>
                    {/if}
                  </div>
                  <button
                    type="button"
                    onclick={() => copySigningLink(contract)}
                    class="inline-flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50"
                  >
                    <Copy class="h-3.5 w-3.5" />
                    Copy Link
                  </button>
                </div>
                <div class="mt-3 rounded-2xl bg-slate-50 px-3 py-2 text-xs text-slate-500">
                  {publicLink(contract.public_token)}
                </div>
              </article>
            {/each}
          </div>
        {/if}
      </div>

      <div class="rounded-3xl border border-amber-200 bg-[linear-gradient(180deg,#fff8eb_0%,#ffffff_100%)] p-5 shadow-sm">
        <div class="mb-4 flex items-center gap-2">
          <Sparkles class="h-5 w-5 text-amber-600" />
          <h2 class="text-lg font-bold text-slate-800">Variabel Otomatis</h2>
        </div>
        <p class="mb-4 text-sm leading-relaxed text-slate-500">
          Klik variabel saat drawer template terbuka untuk menyisipkan placeholder sesuai PRD.
        </p>
        <div class="flex flex-wrap gap-2">
          {#each VARIABLES as variableName}
            <button
              type="button"
              onclick={() => {
                if (canEditContracts && drawerOpen) insertVariable(variableName);
              }}
              class="rounded-full border border-amber-200 bg-white px-3 py-1.5 text-xs font-semibold text-amber-700 transition-colors hover:bg-amber-50"
            >
              {'{{'}{variableName}{'}}'}
            </button>
          {/each}
        </div>
      </div>
    </aside>
  </div>
</div>

<SlideDrawer
  open={drawerOpen}
  title={editor.id ? 'Edit Template Kontrak' : 'Template Kontrak Baru'}
  width="760px"
  onClose={() => (drawerOpen = false)}
>
  <div class="space-y-6 p-6">
    {#if formError}
      <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        {formError}
      </div>
    {/if}

    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label for="contract-template-name" class="mb-1 block text-sm font-medium text-slate-700">Nama Template</label>
        <input
          id="contract-template-name"
          type="text"
          bind:value={editor.name}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div>
        <label for="contract-template-type" class="mb-1 block text-sm font-medium text-slate-700">Jenis Paket</label>
        <select
          id="contract-template-type"
          bind:value={editor.package_type}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        >
          {#each PACKAGE_TYPES as item}
            <option value={item.value}>{item.label}</option>
          {/each}
        </select>
      </div>
      <label class="inline-flex items-center gap-2 text-sm font-medium text-slate-700">
        <input type="checkbox" bind:checked={editor.is_active} class="rounded border-slate-300" />
        Template aktif
      </label>
    </div>

    <div>
      <label for="contract-template-content" class="mb-1 block text-sm font-medium text-slate-700">Isi Template</label>
      <textarea
        id="contract-template-content"
        rows="16"
        bind:value={editor.content}
        class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm leading-relaxed text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
      ></textarea>
    </div>

    <div class="flex flex-wrap justify-between gap-3 border-t border-slate-100 pt-4">
      <button
        type="button"
        onclick={() => openPreview(editor)}
        class="inline-flex items-center gap-2 rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
      >
        <Eye class="h-4 w-4" />
        Preview
      </button>
      <div class="flex flex-wrap gap-3">
        <button
          type="button"
          onclick={() => (drawerOpen = false)}
          class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
        >
          Batal
        </button>
        <button
          type="button"
          onclick={saveTemplate}
          disabled={saving}
          class="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700 disabled:opacity-60"
        >
          {#if saving}
            <Loader2 class="h-4 w-4 animate-spin" />
          {:else}
            <Save class="h-4 w-4" />
          {/if}
          Simpan Template
        </button>
      </div>
    </div>
  </div>
</SlideDrawer>

<SlideDrawer
  open={generateOpen}
  title="Generate Kontrak Jamaah"
  width="760px"
  onClose={() => (generateOpen = false)}
>
  <div class="space-y-6 p-6">
    {#if generateError}
      <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        {generateError}
      </div>
    {/if}

    <div class="grid gap-4 sm:grid-cols-2">
      <div>
        <label for="contract-generator-template" class="mb-1 block text-sm font-medium text-slate-700">Template</label>
        <select
          id="contract-generator-template"
          bind:value={generator.template_id}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        >
          <option value="">Pilih template</option>
          {#each templates.filter((tpl) => tpl.is_active) as template}
            <option value={template.id}>{template.name}</option>
          {/each}
        </select>
      </div>
      <div>
        <label for="contract-generator-type" class="mb-1 block text-sm font-medium text-slate-700">Jenis Paket</label>
        <select
          id="contract-generator-type"
          bind:value={generator.package_type}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        >
          {#each PACKAGE_TYPES as item}
            <option value={item.value}>{item.label}</option>
          {/each}
        </select>
      </div>
      <div>
        <label for="contract-generator-name" class="mb-1 block text-sm font-medium text-slate-700">Nama Jamaah</label>
        <input
          id="contract-generator-name"
          type="text"
          bind:value={generator.recipient_name}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div>
        <label for="contract-generator-phone" class="mb-1 block text-sm font-medium text-slate-700">WhatsApp</label>
        <input
          id="contract-generator-phone"
          type="text"
          bind:value={generator.recipient_phone}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div>
        <label for="contract-generator-email" class="mb-1 block text-sm font-medium text-slate-700">Email</label>
        <input
          id="contract-generator-email"
          type="email"
          bind:value={generator.recipient_email}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
      <div>
        <label for="contract-generator-expiry" class="mb-1 block text-sm font-medium text-slate-700">Expiry (hari)</label>
        <input
          id="contract-generator-expiry"
          type="number"
          min="1"
          max="30"
          bind:value={generator.expires_in_days}
          class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
        />
      </div>
    </div>

    <div>
      <div class="mb-2 flex items-center justify-between">
        <p class="block text-sm font-medium text-slate-700">Variabel Kontrak</p>
        <button
          type="button"
          onclick={() => (generator.variables = { ...SAMPLE_VALUES, nama_jamaah: generator.recipient_name || SAMPLE_VALUES.nama_jamaah })}
          class="text-xs font-semibold text-primary-600"
        >
          Reset Sample
        </button>
      </div>
      <div class="grid gap-3 sm:grid-cols-2">
        {#each VARIABLES as variableName}
          <div>
            <label for={`generator-${variableName}`} class="mb-1 block text-xs font-bold uppercase tracking-wide text-slate-400">{'{{'}{variableName}{'}}'}</label>
            <input
              id={`generator-${variableName}`}
              type="text"
              value={generator.variables?.[variableName] || ''}
              oninput={(event) => fillGeneratorVariable(variableName, event.currentTarget.value)}
              class="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
            />
          </div>
        {/each}
      </div>
    </div>

    <div class="flex flex-wrap justify-end gap-3 border-t border-slate-100 pt-4">
      <button
        type="button"
        onclick={() => (generateOpen = false)}
        class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-50"
      >
        Batal
      </button>
      <button
        type="button"
        onclick={saveContractGeneration}
        disabled={generating}
        class="inline-flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-700 disabled:opacity-60"
      >
        {#if generating}
          <Loader2 class="h-4 w-4 animate-spin" />
        {:else}
          <Send class="h-4 w-4" />
        {/if}
        Generate Link
      </button>
    </div>
  </div>
</SlideDrawer>

<SlideDrawer
  open={previewOpen}
  title={previewTitle}
  width="720px"
  onClose={() => (previewOpen = false)}
>
  {#if previewLoading}
    <div class="flex min-h-[320px] items-center justify-center gap-3 text-slate-500">
      <Loader2 class="h-5 w-5 animate-spin" />
      <span>Memuat preview kontrak...</span>
    </div>
  {:else}
    <div class="p-6">
      <div class="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
        <div class="text-sm leading-relaxed text-slate-700">
          {@html previewHtml}
        </div>
      </div>
    </div>
  {/if}
</SlideDrawer>

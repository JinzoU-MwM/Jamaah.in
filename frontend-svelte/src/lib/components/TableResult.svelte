<script>
  import { onMount, onDestroy } from "svelte";
  import SkeletonLoader from './SkeletonLoader.svelte';
  import {
    Edit3,
    Eye,
    X,
    CheckCircle,
    Loader2,
    Download,
    FileText,
    IdCard,
    Plane,
    AlertTriangle,
    Crown,
    Lock,
    FolderPlus,
    Settings,
    Shirt,
    Users,
    Search,
    Replace,
    Trash2,
    CheckSquare,
  } from "lucide-svelte";

  let {
    isOpen,
    data = $bindable([]),
    isGenerating,
    onClose,
    onSave,
    onSaveToGroup = null,
    isSavingToGroup = false,
    groupName = "",
    onUpgrade,
    validationWarnings = [],
    fileResults = [],
    readOnly = false,
    showOperational = false, // Toggle for operational columns (Pro only)
    isPro = false, // Is Pro user
    loading = false, // Loading state for skeleton (passed from parent)
  } = $props();

  // State for operational columns toggle
  // Use $derived to reactively sync with prop, with local toggle capability
  let showOperationalFields = $state(false);

  // Sync with prop on mount
  $effect(() => {
    if (showOperational) {
      showOperationalFields = showOperational;
    }
  });

  // Column definitions - Complete 32 columns matching Excel output
  const columns = [
    { key: "title", label: "Title", width: "70px" },
    { key: "nama", label: "Nama", width: "150px" },
    { key: "nama_ayah", label: "Nama Ayah", width: "130px" },
    { key: "jenis_identitas", label: "Jenis ID", width: "80px" },
    { key: "no_identitas", label: "No Identitas", width: "130px" },
    { key: "nama_paspor", label: "Nama Paspor", width: "150px" },
    { key: "no_paspor", label: "No Paspor", width: "100px" },
    { key: "tanggal_paspor", label: "Tgl Paspor", width: "110px" },
    { key: "kota_paspor", label: "Kota Paspor", width: "100px" },
    { key: "tempat_lahir", label: "Tempat Lahir", width: "100px" },
    { key: "tanggal_lahir", label: "Tgl Lahir", width: "110px" },
    { key: "alamat", label: "Alamat", width: "180px" },
    { key: "provinsi", label: "Provinsi", width: "100px" },
    { key: "kabupaten", label: "Kabupaten", width: "100px" },
    { key: "kecamatan", label: "Kecamatan", width: "100px" },
    { key: "kelurahan", label: "Kelurahan", width: "100px" },
    { key: "no_telepon", label: "No. Telepon", width: "110px" },
    { key: "no_hp", label: "No HP", width: "110px" },
    { key: "kewarganegaraan", label: "Kewarganegaraan", width: "110px" },
    { key: "status_pernikahan", label: "Status Nikah", width: "100px" },
    { key: "pendidikan", label: "Pendidikan", width: "100px" },
    { key: "pekerjaan", label: "Pekerjaan", width: "100px" },
    { key: "provider_visa", label: "Provider Visa", width: "100px" },
    { key: "no_visa", label: "No Visa", width: "100px" },
    { key: "tanggal_visa", label: "Tgl Visa", width: "110px" },
    { key: "tanggal_visa_akhir", label: "Tgl Visa Akhir", width: "110px" },
    { key: "asuransi", label: "Asuransi", width: "100px" },
    { key: "no_polis", label: "No Polis", width: "100px" },
    { key: "tanggal_input_polis", label: "Tgl Input Polis", width: "110px" },
    { key: "tanggal_awal_polis", label: "Tgl Awal Polis", width: "110px" },
    { key: "tanggal_akhir_polis", label: "Tgl Akhir Polis", width: "110px" },
    { key: "no_bpjs", label: "No BPJS", width: "100px" },
  ];

  // Operational columns (internal use, for Pro users - Inventory & Rooming)
  const operationalColumns = [
    {
      key: "baju_size",
      label: "Ukuran Baju",
      width: "90px",
      type: "select",
      options: ["", "S", "M", "L", "XL", "XXL"],
    },
    {
      key: "family_id",
      label: "Family ID",
      width: "100px",
      type: "text",
      placeholder: "e.g., F001",
    },
  ];

  function updateCell(rowIndex, key, value) {
    data[rowIndex][key] = value;
  }

  function getDocTypeIcon(type) {
    if (type === "KTP") return IdCard;
    if (type === "PASSPORT") return Plane;
    if (type === "VISA") return FileText;
    return FileText;
  }

  function getDocTypeColor(type) {
    if (type === "KTP") return "bg-blue-100 text-blue-700";
    if (type === "PASSPORT") return "bg-purple-100 text-purple-700";
    if (type === "VISA") return "bg-amber-100 text-amber-700";
    if (type === "MERGED") return "bg-emerald-100 text-emerald-700";
    return "bg-slate-100 text-slate-700";
  }

  /**
   * Check if a specific cell has a validation warning
   * Returns the warning message or null
   */
  function getCellWarning(rowIndex, fieldKey) {
    if (!validationWarnings || !validationWarnings[rowIndex]) return null;
    const rowWarnings = validationWarnings[rowIndex];
    const warning = rowWarnings.find((w) => w.field === fieldKey);
    return warning ? warning.message : null;
  }

  // Date columns that should auto-normalize
  const DATE_COLUMNS = new Set([
    "tanggal_lahir",
    "tanggal_paspor",
    "tanggal_visa",
    "tanggal_visa_akhir",
    "tanggal_input_polis",
    "tanggal_awal_polis",
    "tanggal_akhir_polis",
  ]);

  /**
   * Auto-normalize dates to YYYY-MM-DD on blur
   * Handles: DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY, DD MM YYYY
   */
  function normalizeDate(rowIndex, key, value) {
    if (!DATE_COLUMNS.has(key) || !value) return;
    const v = value.trim();

    // Already in YYYY-MM-DD format
    if (/^\d{4}-\d{2}-\d{2}$/.test(v)) return;

    // DD-MM-YYYY, DD/MM/YYYY, DD.MM.YYYY
    const match = v.match(/^(\d{1, 2})[\/\-.\s](\d{1, 2})[\/\-.\s](\d{4})$/);
    if (match) {
      const [, dd, mm, yyyy] = match;
      const normalized = `${yyyy}-${mm.padStart(2, "0")}-${dd.padStart(2, "0")}`;
      data[rowIndex][key] = normalized;
    }
  }

  // Count total warnings
  let totalWarnings = $derived(
    validationWarnings
      ? validationWarnings.reduce((sum, row) => sum + (row ? row.length : 0), 0)
      : 0,
  );

  // === BULK EDIT STATE ===
  let selectedRows = $state(new Set());
  let lastClickedRow = $state(-1);
  let bulkColumn = $state("");
  let bulkValue = $state("");
  let showFindReplace = $state(false);
  let searchTerm = $state("");
  let replaceTerm = $state("");

  let selectedCount = $derived(selectedRows.size);
  let allSelected = $derived(
    data.length > 0 && selectedRows.size === data.length,
  );
  let allColumns = $derived([
    ...columns,
    ...(showOperationalFields ? operationalColumns : []),
  ]);

  function toggleSelectAll() {
    if (allSelected) {
      selectedRows = new Set();
    } else {
      selectedRows = new Set(data.map((_, i) => i));
    }
  }

  function toggleRow(index, event) {
    const next = new Set(selectedRows);
    if (event?.shiftKey && lastClickedRow >= 0) {
      const from = Math.min(lastClickedRow, index);
      const to = Math.max(lastClickedRow, index);
      for (let i = from; i <= to; i++) next.add(i);
    } else if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    selectedRows = next;
    lastClickedRow = index;
  }

  function applyBulkEdit() {
    if (!bulkColumn || selectedRows.size === 0) return;
    for (const idx of selectedRows) {
      data[idx][bulkColumn] = bulkValue;
    }
    data = [...data]; // trigger reactivity
    bulkValue = "";
  }

  function deleteSelectedRows() {
    if (selectedRows.size === 0) return;
    if (!confirm(`Hapus ${selectedRows.size} baris yang dipilih?`)) return;
    data = data.filter((_, i) => !selectedRows.has(i));
    selectedRows = new Set();
  }

  // Find & Replace
  function cellMatchesSearch(value) {
    if (!searchTerm) return false;
    return String(value || "")
      .toLowerCase()
      .includes(searchTerm.toLowerCase());
  }

  let matchCount = $derived(() => {
    if (!searchTerm) return 0;
    let count = 0;
    for (const row of data) {
      for (const col of allColumns) {
        if (cellMatchesSearch(row[col.key])) count++;
      }
    }
    return count;
  });

  function replaceAll(inSelectionOnly = false) {
    if (!searchTerm) return;
    const regex = new RegExp(
      searchTerm.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"),
      "gi",
    );
    for (let i = 0; i < data.length; i++) {
      if (inSelectionOnly && !selectedRows.has(i)) continue;
      for (const col of allColumns) {
        const val = String(data[i][col.key] || "");
        if (regex.test(val)) {
          data[i][col.key] = val.replace(regex, replaceTerm);
        }
      }
    }
    data = [...data];
  }

  // Keyboard shortcuts
  function handleKeydown(e) {
    if (!isOpen || readOnly) return;
    if (
      e.ctrlKey &&
      e.key === "a" &&
      !e.target.closest("input, textarea, select")
    ) {
      e.preventDefault();
      toggleSelectAll();
    }
    if (e.ctrlKey && e.key === "f") {
      e.preventDefault();
      showFindReplace = !showFindReplace;
    }
    if (e.key === "Escape") {
      if (showFindReplace) {
        showFindReplace = false;
      } else if (selectedRows.size > 0) {
        selectedRows = new Set();
      }
    }
  }

  onMount(() => {
    if (typeof window !== "undefined")
      window.addEventListener("keydown", handleKeydown);
  });
  onDestroy(() => {
    if (typeof window !== "undefined")
      window.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isOpen}
  <div
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl w-full max-w-[95vw] max-h-[90vh] overflow-hidden flex flex-col"
    >
      <!-- Modal Header -->
      <div
        class="flex items-center justify-between p-6 border-b border-slate-200 bg-gradient-to-r from-emerald-50 to-white"
      >
        <div class="flex items-center gap-3">
          <div
            class="{readOnly ? 'bg-blue-100' : 'bg-emerald-100'} p-2 rounded-lg"
          >
            {#if readOnly}
              <Eye class="h-6 w-6 text-blue-600" />
            {:else}
              <Edit3 class="h-6 w-6 text-emerald-600" />
            {/if}
          </div>
          <div>
            <h2 class="text-xl font-bold text-slate-800">
              {readOnly
                ? "Preview Hasil Ekstraksi"
                : "Tinjau Data Hasil Ekstraksi"}
            </h2>
            <p class="text-sm text-slate-500">
              {readOnly
                ? "Upgrade ke Pro untuk mengedit dan mengunduh Excel."
                : "Klik sel manapun untuk mengedit. Data dari KTP, Paspor, dan Visa sudah digabung otomatis."}
            </p>
          </div>
        </div>
        <button
          onclick={onClose}
          class="text-slate-400 hover:text-slate-600 hover:bg-slate-100 p-2 rounded-lg transition-colors"
        >
          <X class="h-6 w-6" />
        </button>
      </div>

      <!-- File Results Summary -->
      {#if fileResults && fileResults.length > 0}
        <div class="px-6 pt-4 flex flex-wrap gap-2">
          {#each fileResults as fr}
            <span
              class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium
            {fr.status === 'success'
                ? 'bg-emerald-50 text-emerald-700'
                : fr.status === 'failed'
                  ? 'bg-red-50 text-red-700'
                  : 'bg-amber-50 text-amber-700'}"
            >
              {#if fr.status === "success"}
                <CheckCircle class="h-3 w-3" />
              {:else}
                <AlertTriangle class="h-3 w-3" />
              {/if}
              {fr.filename}
              {#if fr.cached}
                <span class="text-blue-500 ml-0.5">⚡ cache</span>
              {/if}
            </span>
          {/each}
        </div>
      {/if}

      <!-- Validation Warnings Banner -->
      {#if totalWarnings > 0}
        <div
          class="mx-6 mt-3 bg-amber-50 border border-amber-200 rounded-lg px-4 py-2.5 flex items-center gap-2"
        >
          <AlertTriangle class="h-4 w-4 text-amber-500 flex-shrink-0" />
          <span class="text-sm text-amber-700">
            <strong>{totalWarnings}</strong> peringatan validasi ditemukan. Sel yang
            bermasalah ditandai kuning.
          </span>
        </div>
      {/if}

      <!-- Operational Fields Toggle (Pro only) -->
      {#if isPro && !readOnly}
        <div class="mx-6 mt-3 flex items-center gap-3">
          <button
            onclick={() => (showOperationalFields = !showOperationalFields)}
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
              {showOperationalFields
              ? 'bg-purple-100 text-purple-700 border border-purple-200'
              : 'bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200'}"
          >
            <Settings class="h-4 w-4" />
            <Shirt class="h-4 w-4" />
            Data Operasional (Inventori & Rooming)
          </button>
          {#if showOperationalFields}
            <span class="text-xs text-slate-500">
              Kolom tambahan untuk ukuran baju dan family ID (tidak diekspor ke
              Excel Siskopatuh)
            </span>
          {/if}
        </div>
      {/if}

      <!-- Bulk Edit Toolbar -->
      {#if !readOnly && selectedCount > 0}
        <div
          class="mx-6 mt-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-2.5 flex items-center gap-3 flex-wrap"
        >
          <span
            class="text-sm font-medium text-blue-700 flex items-center gap-1.5"
          >
            <CheckSquare class="h-4 w-4" />
            {selectedCount} baris dipilih
          </span>
          <div class="h-5 w-px bg-blue-200"></div>
          <select
            bind:value={bulkColumn}
            class="px-2 py-1.5 border border-blue-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-400"
          >
            <option value="">Pilih kolom...</option>
            {#each allColumns as col}
              <option value={col.key}>{col.label}</option>
            {/each}
          </select>
          <input
            type="text"
            bind:value={bulkValue}
            placeholder="Nilai baru"
            class="px-2 py-1.5 border border-blue-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-blue-400 w-32"
          />
          <button
            type="button"
            onclick={applyBulkEdit}
            disabled={!bulkColumn}
            class="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-xs font-medium rounded-lg disabled:opacity-40 transition-colors"
            >Terapkan</button
          >
          <div class="h-5 w-px bg-blue-200"></div>
          <button
            type="button"
            onclick={deleteSelectedRows}
            class="px-3 py-1.5 bg-red-500 hover:bg-red-600 text-white text-xs font-medium rounded-lg flex items-center gap-1 transition-colors"
          >
            <Trash2 class="h-3 w-3" /> Hapus
          </button>
          <button
            type="button"
            onclick={() => {
              selectedRows = new Set();
            }}
            class="ml-auto text-xs text-blue-500 hover:text-blue-700"
            >Batal pilih</button
          >
        </div>
      {/if}

      <!-- Find & Replace Panel -->
      {#if !readOnly && showFindReplace}
        <div
          class="mx-6 mt-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 flex items-center gap-3 flex-wrap"
        >
          <Search class="h-4 w-4 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            bind:value={searchTerm}
            placeholder="Cari..."
            class="px-2 py-1.5 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-emerald-400 w-36"
          />
          <Replace class="h-4 w-4 text-slate-400 flex-shrink-0" />
          <input
            type="text"
            bind:value={replaceTerm}
            placeholder="Ganti dengan..."
            class="px-2 py-1.5 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-emerald-400 w-36"
          />
          {#if searchTerm}
            <span class="text-xs text-slate-500">{matchCount()} ditemukan</span>
          {/if}
          <button
            type="button"
            onclick={() => replaceAll(false)}
            disabled={!searchTerm}
            class="px-3 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-medium rounded-lg disabled:opacity-40 transition-colors"
            >Ganti Semua</button
          >
          {#if selectedCount > 0}
            <button
              type="button"
              onclick={() => replaceAll(true)}
              disabled={!searchTerm}
              class="px-3 py-1.5 bg-blue-500 hover:bg-blue-600 text-white text-xs font-medium rounded-lg disabled:opacity-40 transition-colors"
              >Ganti di {selectedCount} Terpilih</button
            >
          {/if}
          <button
            type="button"
            onclick={() => {
              showFindReplace = false;
              searchTerm = "";
              replaceTerm = "";
            }}
            class="ml-auto p-1 hover:bg-slate-200 rounded"
            ><X class="h-3.5 w-3.5 text-slate-500" /></button
          >
        </div>
      {/if}

      <!-- Find/Replace toggle button -->
      {#if !readOnly && !showFindReplace && data.length > 0}
        <div class="mx-6 mt-2 flex justify-end">
          <button
            type="button"
            onclick={() => (showFindReplace = true)}
            class="text-xs text-slate-400 hover:text-slate-600 flex items-center gap-1 transition-colors"
          >
            <Search class="h-3 w-3" /> Cari & Ganti (Ctrl+F)
          </button>
        </div>
      {/if}

      <!-- Modal Body - Scrollable Table -->
      <div class="flex-1 overflow-auto p-6">
        {#if loading}
          <div class="p-4">
            <SkeletonLoader count={10} type="row" />
          </div>
        {:else}
        <div class="rounded-lg border border-slate-200">
          <table class="w-full border-collapse text-sm">
            <thead>
              <tr class="bg-slate-100">
                {#if !readOnly}
                  <th
                    class="border-b border-r border-slate-200 px-2 py-3 text-center sticky left-0 bg-slate-100 z-10 w-10"
                  >
                    <input
                      type="checkbox"
                      checked={allSelected}
                      onchange={toggleSelectAll}
                      class="rounded border-slate-300 text-blue-500 focus:ring-blue-400 cursor-pointer"
                    />
                  </th>
                {/if}
                <th
                  class="border-b border-r border-slate-200 px-3 py-3 text-center font-semibold text-slate-700 {readOnly
                    ? 'sticky left-0'
                    : ''} bg-slate-100 z-10">#</th
                >
                {#each columns as col}
                  <th
                    class="border-b border-slate-200 px-3 py-3 text-left font-semibold text-slate-700 whitespace-nowrap bg-slate-100"
                    style="min-width: {col.width}"
                  >
                    {col.label}
                  </th>
                {/each}
                {#if showOperationalFields}
                  {#each operationalColumns as col}
                    <th
                      class="border-b border-slate-200 px-3 py-3 text-left font-semibold text-purple-700 whitespace-nowrap bg-purple-50"
                      style="min-width: {col.width}"
                    >
                      <div class="flex items-center gap-1">
                        {#if col.key === "baju_size"}
                          <Shirt class="h-3.5 w-3.5" />
                        {:else if col.key === "family_id"}
                          <Users class="h-3.5 w-3.5" />
                        {/if}
                        {col.label}
                      </div>
                    </th>
                  {/each}
                {/if}
              </tr>
            </thead>
            <tbody>
              {#each data as row, rowIndex}
                <tr
                  class="{selectedRows.has(rowIndex)
                    ? 'bg-blue-50'
                    : 'hover:bg-emerald-50/50'} transition-colors"
                >
                  {#if !readOnly}
                    <td
                      class="border-b border-r border-slate-200 px-2 py-2 text-center sticky left-0 {selectedRows.has(
                        rowIndex,
                      )
                        ? 'bg-blue-50'
                        : 'bg-white'} z-10 w-10"
                    >
                      <input
                        type="checkbox"
                        checked={selectedRows.has(rowIndex)}
                        onchange={(e) => toggleRow(rowIndex, e)}
                        class="rounded border-slate-300 text-blue-500 focus:ring-blue-400 cursor-pointer"
                      />
                    </td>
                  {/if}
                  <td
                    class="border-b border-r border-slate-200 px-3 py-2 text-slate-500 text-center font-medium {readOnly
                      ? 'sticky left-0'
                      : ''} {selectedRows.has(rowIndex)
                      ? 'bg-blue-50'
                      : 'bg-white'} z-10"
                  >
                    {rowIndex + 1}
                  </td>
                  {#each columns as col}
                    {@const warning = getCellWarning(rowIndex, col.key)}
                    <td
                      class="border-b border-slate-200 px-1 py-1 {warning
                        ? 'bg-amber-50'
                        : ''}"
                    >
                      {#if col.key === "jenis_identitas"}
                        <div class="flex items-center justify-center">
                          <span
                            class="px-2 py-1 rounded-full text-xs font-medium {getDocTypeColor(
                              row[col.key],
                            )}"
                          >
                            {row[col.key] || "N/A"}
                          </span>
                        </div>
                      {:else}
                        <div class="relative group/cell">
                          {#if readOnly}
                            <span
                              class="block w-full px-2 py-1.5 text-sm text-slate-700 {warning
                                ? 'ring-1 ring-amber-400 rounded'
                                : ''}"
                            >
                              {row[col.key] || "-"}
                            </span>
                          {:else}
                            <input
                              type="text"
                              value={row[col.key] || ""}
                              oninput={(e) =>
                                updateCell(
                                  rowIndex,
                                  col.key,
                                  /** @type {any} */ (e.target).value,
                                )}
                              onblur={(e) =>
                                normalizeDate(
                                  rowIndex,
                                  col.key,
                                  /** @type {any} */ (e.target).value,
                                )}
                              class="w-full px-2 py-1.5 border-0 bg-transparent focus:bg-emerald-50 focus:outline-none focus:ring-1 focus:ring-emerald-500 rounded text-sm {warning
                                ? 'ring-1 ring-amber-400'
                                : cellMatchesSearch(row[col.key])
                                  ? 'bg-yellow-100 ring-1 ring-yellow-400'
                                  : ''}"
                              placeholder="-"
                            />
                          {/if}
                          {#if warning}
                            <div
                              class="absolute bottom-full left-0 mb-1 z-20 hidden group-hover/cell:block"
                            >
                              <div
                                class="bg-amber-700 text-white text-xs rounded-lg px-3 py-1.5 shadow-lg whitespace-nowrap max-w-xs"
                              >
                                ⚠️ {warning}
                              </div>
                            </div>
                          {/if}
                        </div>
                      {/if}
                    </td>
                  {/each}
                  <!-- Operational Columns (Pro only) -->
                  {#if showOperationalFields}
                    {#each operationalColumns as opCol}
                      <td
                        class="border-b border-slate-200 px-1 py-1 bg-purple-50/50"
                      >
                        {#if opCol.type === "select"}
                          <select
                            value={row[opCol.key] || ""}
                            onchange={(e) =>
                              updateCell(
                                rowIndex,
                                opCol.key,
                                /** @type {any} */ (e.target).value,
                              )}
                            class="w-full px-2 py-1.5 border-0 bg-white focus:ring-1 focus:ring-purple-500 rounded text-sm"
                          >
                            {#each opCol.options as opt}
                              <option value={opt}>{opt || "-"}</option>
                            {/each}
                          </select>
                        {:else}
                          <input
                            type="text"
                            value={row[opCol.key] || ""}
                            oninput={(e) =>
                              updateCell(
                                rowIndex,
                                opCol.key,
                                /** @type {any} */ (e.target).value,
                              )}
                            class="w-full px-2 py-1.5 border-0 bg-white focus:ring-1 focus:ring-purple-500 rounded text-sm"
                            placeholder={opCol.placeholder || "-"}
                          />
                        {/if}
                      </td>
                    {/each}
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>

        {#if data.length === 0}
          <div class="text-center py-16 text-slate-500">
            <FileText class="h-16 w-16 mx-auto mb-4 text-slate-300" />
            <p class="text-lg font-medium">Tidak ada data yang diekstrak</p>
            <p class="text-sm mt-2">
              Coba lagi dengan gambar yang lebih jelas.
            </p>
          </div>
        {/if}
        {/if}
      </div>
      <!-- Make table scrollable on mobile -->
      <style>
        .action-column {
          position: sticky;
          right: 0;
          background: white;
          z-index: 10;
        }
        .dark .action-column {
          background: #1e293b;
        }
      </style>

      <!-- Modal Footer -->
      <div
        class="flex items-center justify-between p-6 border-t border-slate-200 bg-slate-50"
      >
        <div class="flex items-center gap-4 text-sm text-slate-600">
          <div class="flex items-center gap-1">
            <CheckCircle class="h-5 w-5 text-emerald-500" />
            <span><strong>{data.length}</strong> data berhasil diekstrak</span>
          </div>
          <div class="h-4 w-px bg-slate-300"></div>
          <div class="flex items-center gap-2">
            <span
              class="px-2 py-0.5 rounded text-xs bg-emerald-100 text-emerald-700"
              >Digabung Otomatis</span
            >
            <span class="text-xs text-slate-400"
              >KTP + Paspor + Visa → 1 Baris</span
            >
          </div>
          {#if totalWarnings > 0}
            <div class="h-4 w-px bg-slate-300"></div>
            <div class="flex items-center gap-1">
              <AlertTriangle class="h-4 w-4 text-amber-500" />
              <span class="text-xs text-amber-600"
                ><strong>{totalWarnings}</strong> peringatan</span
              >
            </div>
          {/if}
        </div>
        <div class="flex items-center gap-3">
          <button
            onclick={onClose}
            class="px-6 py-2.5 border border-slate-300 rounded-lg text-slate-600 hover:bg-slate-100 transition-colors font-medium"
          >
            {readOnly ? "Tutup" : "Batal"}
          </button>
          {#if readOnly}
            <button
              onclick={onUpgrade}
              class="px-8 py-2.5 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-lg font-semibold flex items-center gap-2 transition-all shadow-lg hover:shadow-xl"
            >
              <Crown class="h-5 w-5" />
              Upgrade untuk Edit & Unduh
            </button>
          {:else}
            <div class="flex items-center gap-2">
              {#if onSaveToGroup}
                <button
                  onclick={onSaveToGroup}
                  disabled={isSavingToGroup || data.length === 0}
                  class="px-6 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
                >
                  {#if isSavingToGroup}
                    <Loader2 class="h-5 w-5 animate-spin" />
                    Menyimpan...
                  {:else}
                    <FolderPlus class="h-5 w-5" />
                    Simpan ke Grup
                  {/if}
                </button>
              {/if}
              <button
                onclick={onSave}
                disabled={isGenerating || data.length === 0}
                class="px-8 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg font-semibold flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
              >
                {#if isGenerating}
                  <Loader2 class="h-5 w-5 animate-spin" />
                  Mengunduh...
                {:else}
                  <Download class="h-5 w-5" />
                  Unduh Excel
                {/if}
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
{/if}

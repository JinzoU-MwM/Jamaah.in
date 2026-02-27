<!--
  InventoryPage.svelte — Professional Logistics Dashboard
  
  Design: Compact card-based layout, efficient use of space
  Tone: Clean, data-dense, professional travel agency tool
-->
<script>
  import {
    Package,
    Shirt,
    CheckCircle,
    Loader2,
    AlertTriangle,
    RefreshCw,
    X,
    Users,
    Filter,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";

  let { isOpen = false, onClose, groups = [], isPro = false } = $props();

  // State
  let selectedGroupId = $state(null);
  let forecast = $state(null);
  let fulfillment = $state(null);
  let isLoading = $state(false);
  let error = $state(null);
  let selectedMembers = $state(new Set());
  let isMarking = $state(false);

  // Derived values
  let selectedGroup = $derived(groups.find((g) => g.id === selectedGroupId));
  let canMarkSelected = $derived(selectedMembers.size > 0 && !isMarking);

  // Size options
  const sizes = ["", "S", "M", "L", "XL", "XXL"];

  // Fetch forecast when group changes
  async function loadGroupData() {
    if (!selectedGroupId) {
      forecast = null;
      fulfillment = null;
      return;
    }

    isLoading = true;
    error = null;

    try {
      const [forecastData, fulfillmentData] = await Promise.all([
        ApiService.getInventoryForecast(selectedGroupId),
        ApiService.getFulfillmentStatus(selectedGroupId),
      ]);

      forecast = forecastData;
      fulfillment = fulfillmentData;
      selectedMembers = new Set();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  // Mark selected members as received
  async function markSelectedAsReceived() {
    if (!selectedGroupId || selectedMembers.size === 0) return;

    isMarking = true;
    try {
      const memberIds = Array.from(selectedMembers);
      await ApiService.markMembersReceived(selectedGroupId, memberIds);

      if (fulfillment) {
        for (const id of memberIds) {
          const pending = fulfillment.pending.find((m) => m.id === id);
          if (pending) {
            pending.is_equipment_received = true;
            fulfillment.received.push(pending);
          }
        }
        fulfillment.pending = fulfillment.pending.filter(
          (m) => !memberIds.includes(m.id),
        );
      }

      selectedMembers = new Set();
    } catch (e) {
      error = e.message;
    } finally {
      isMarking = false;
    }
  }

  function toggleMember(memberId) {
    const newSet = new Set(selectedMembers);
    if (newSet.has(memberId)) {
      newSet.delete(memberId);
    } else {
      newSet.add(memberId);
    }
    selectedMembers = newSet;
  }

  function selectAllPending() {
    if (fulfillment) {
      const newSet = new Set();
      for (const m of fulfillment.pending) {
        newSet.add(m.id);
      }
      selectedMembers = newSet;
    }
  }

  function clearSelection() {
    selectedMembers = new Set();
  }

  async function updateBajuSize(memberId, size) {
    try {
      await ApiService.updateMemberOperational(memberId, size, "");
      if (forecast) {
        const detail = forecast.details.find((d) => d.member_id === memberId);
        if (detail) detail.baju_size = size;
      }
    } catch (e) {
      error = e.message;
    }
  }

  async function updateFamilyId(memberId, familyId) {
    try {
      const detail = forecast?.details.find((d) => d.member_id === memberId);
      await ApiService.updateMemberOperational(
        memberId,
        detail?.baju_size || "",
        familyId,
      );
      if (forecast) {
        const d = forecast.details.find((d) => d.member_id === memberId);
        if (d) d.family_id = familyId;
      }
    } catch (e) {
      error = e.message;
    }
  }
</script>

{#if isOpen}
  <div class="flex flex-col h-full min-h-screen bg-white">
    <!-- Compact Header -->
    <header
      class="flex items-center px-4 py-3 border-b border-slate-200 bg-slate-50"
    >
      <div class="flex items-center gap-3">
        <div
          class="w-8 h-8 bg-violet-100 rounded-lg flex items-center justify-center"
        >
          <Package class="w-4 h-4 text-violet-600" />
        </div>
        <div>
          <h1 class="text-sm font-semibold text-slate-800">
            Inventori & Logistik
          </h1>
          <p class="text-xs text-slate-500">Kelola distribusi perlengkapan</p>
        </div>
      </div>
    </header>

    <!-- Toolbar -->
    <div
      class="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 bg-white"
    >
      <select
        id="inv-group-select"
        bind:value={selectedGroupId}
        onchange={loadGroupData}
        class="flex-1 max-w-[200px] text-sm px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-violet-500"
      >
        <option value="">Pilih Grup</option>
        {#each groups as group}
          <option value={group.id}>{group.name} ({group.member_count})</option>
        {/each}
      </select>

      {#if selectedGroupId}
        <button
          type="button"
          onclick={loadGroupData}
          disabled={isLoading}
          class="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg disabled:opacity-50"
        >
          <RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
        </button>
      {/if}

      <!-- Bulk Actions -->
      {#if fulfillment && fulfillment.pending?.length > 0}
        <div class="flex items-center gap-2 ml-auto">
          <span class="text-xs text-slate-500"
            >{selectedMembers.size} dipilih</span
          >
          <button
            type="button"
            onclick={selectAllPending}
            class="text-xs text-violet-600 hover:underline">Semua</button
          >
          <button
            type="button"
            onclick={clearSelection}
            class="text-xs text-slate-500 hover:underline">Batal</button
          >
          <button
            type="button"
            onclick={markSelectedAsReceived}
            disabled={!canMarkSelected}
            class="px-3 py-1.5 bg-violet-600 text-white text-xs font-medium rounded-lg hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            {#if isMarking}<Loader2
                class="w-3 h-3 animate-spin"
              />{:else}<CheckCircle class="w-3 h-3" />{/if}
            Tandai Terima
          </button>
        </div>
      {/if}
    </div>

    <!-- Error -->
    {#if error}
      <div
        class="mx-4 mt-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 flex items-center gap-2 text-sm"
      >
        <AlertTriangle class="w-4 h-4 text-red-500" />
        <span class="text-red-700 flex-1">{error}</span>
        <button
          type="button"
          onclick={() => (error = null)}
          class="text-red-500 hover:text-red-700"
        >
          <X class="w-4 h-4" />
        </button>
      </div>
    {/if}

    <!-- Content -->
    <div class="flex-1 overflow-auto">
      {#if isLoading}
        <div class="flex items-center justify-center py-12">
          <Loader2 class="w-6 h-6 animate-spin text-violet-500" />
        </div>
      {:else if !selectedGroupId}
        <div
          class="flex flex-col items-center justify-center py-12 text-slate-400"
        >
          <Package class="w-10 h-10 mb-2" />
          <p class="text-sm">Pilih grup untuk memulai</p>
        </div>
      {:else if forecast}
        <!-- Stats Grid - Compact -->
        <div class="grid grid-cols-4 gap-2 p-3">
          <div class="stat-card">
            <span class="stat-value text-slate-800"
              >{forecast.total_members}</span
            >
            <span class="stat-label">Total</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-blue-600"
              >{forecast.requirements?.koper || 0}</span
            >
            <span class="stat-label">Koper</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-emerald-600"
              >{forecast.requirements?.ihram || 0}</span
            >
            <span class="stat-label">Ihram</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-pink-600"
              >{forecast.requirements?.mukena || 0}</span
            >
            <span class="stat-label">Mukena</span>
          </div>
        </div>

        <!-- Size & Status Row -->
        <div class="flex gap-2 px-3 pb-3">
          <!-- Sizes -->
          <div class="flex-1 bg-white border border-slate-200 rounded-lg p-2.5">
            <div class="flex items-center gap-1.5 mb-2">
              <Shirt class="w-3.5 h-3.5 text-slate-500" />
              <span class="text-xs font-medium text-slate-600">Ukuran Baju</span
              >
            </div>
            <div class="flex flex-wrap gap-1.5">
              {#each Object.entries(forecast.size_breakdown || {}) as [size, count]}
                <span
                  class="px-2 py-0.5 bg-slate-100 rounded text-xs font-medium text-slate-700"
                >
                  {size || "N/A"}: {count}
                </span>
              {/each}
            </div>
          </div>
          <!-- Status -->
          {#if fulfillment}
            <div
              class="bg-white border border-slate-200 rounded-lg p-2.5 min-w-[120px]"
            >
              <div class="text-xs font-medium text-slate-600 mb-2">Status</div>
              <div class="flex items-center gap-3 text-xs">
                <span class="flex items-center gap-1">
                  <CheckCircle class="w-3 h-3 text-emerald-500" />
                  <span class="font-medium text-emerald-700"
                    >{fulfillment.received_count || 0}</span
                  >
                </span>
                <span class="flex items-center gap-1">
                  <Package class="w-3 h-3 text-amber-500" />
                  <span class="font-medium text-amber-700"
                    >{fulfillment.pending_count || 0}</span
                  >
                </span>
              </div>
            </div>
          {/if}
        </div>

        <!-- Member Table - Compact -->
        <div class="px-3 pb-3">
          <div class="overflow-x-auto rounded-lg border border-slate-200">
            <table class="w-full text-xs">
              <thead class="bg-slate-50">
                <tr>
                  <th class="w-8 px-2 py-2 text-left">
                    <input
                      type="checkbox"
                      checked={fulfillment?.pending?.length > 0 &&
                        selectedMembers.size === fulfillment?.pending?.length}
                      onchange={() => {
                        if (
                          selectedMembers.size === fulfillment?.pending?.length
                        )
                          clearSelection();
                        else selectAllPending();
                      }}
                      class="rounded"
                    />
                  </th>
                  <th class="px-2 py-2 text-left font-semibold text-slate-600"
                    >Nama</th
                  >
                  <th
                    class="px-2 py-2 text-left font-semibold text-slate-600 w-16"
                    >Gender</th
                  >
                  <th
                    class="px-2 py-2 text-left font-semibold text-slate-600 w-20"
                    >Baju</th
                  >
                  <th
                    class="px-2 py-2 text-left font-semibold text-slate-600 w-20"
                    >Family</th
                  >
                  <th
                    class="px-2 py-2 text-left font-semibold text-slate-600 w-20"
                    >Status</th
                  >
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                {#each forecast.details || [] as member}
                  {@const isReceived = member.is_equipment_received}
                  <tr
                    class="hover:bg-slate-50 {isReceived
                      ? 'bg-emerald-50/30'
                      : ''}"
                  >
                    <td class="px-2 py-1.5">
                      {#if !isReceived}
                        <input
                          type="checkbox"
                          checked={selectedMembers.has(member.member_id)}
                          onchange={() => toggleMember(member.member_id)}
                          class="rounded"
                        />
                      {:else}
                        <CheckCircle class="w-3.5 h-3.5 text-emerald-500" />
                      {/if}
                    </td>
                    <td
                      class="px-2 py-1.5 font-medium text-slate-800 truncate max-w-[150px]"
                      >{member.nama}</td
                    >
                    <td class="px-2 py-1.5">
                      <span
                        class="px-1.5 py-0.5 rounded text-[10px] font-medium {member.gender ===
                        'male'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-pink-100 text-pink-700'}"
                      >
                        {member.gender === "male" ? "L" : "P"}
                      </span>
                    </td>
                    <td class="px-2 py-1.5">
                      <select
                        value={member.baju_size || ""}
                        onchange={(e) =>
                          updateBajuSize(
                            member.member_id,
                            /** @type {HTMLSelectElement} */ (e.target).value,
                          )}
                        class="w-full px-1.5 py-1 border border-slate-200 rounded text-xs bg-white"
                      >
                        {#each sizes as s}<option value={s}>{s || "-"}</option
                          >{/each}
                      </select>
                    </td>
                    <td class="px-2 py-1.5">
                      <input
                        type="text"
                        value={member.family_id || ""}
                        onblur={(e) =>
                          updateFamilyId(
                            member.member_id,
                            /** @type {HTMLInputElement} */ (e.target).value,
                          )}
                        placeholder="F00"
                        class="w-full px-1.5 py-1 border border-slate-200 rounded text-xs"
                      />
                    </td>
                    <td class="px-2 py-1.5">
                      {#if isReceived}
                        <span class="badge badge-success">✓</span>
                      {:else}
                        <span class="badge badge-warning">Menunggu</span>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {:else}
        <div class="text-center py-8 text-slate-400 text-sm">
          Tidak ada data
        </div>
      {/if}
    </div>
  </div>
{/if}

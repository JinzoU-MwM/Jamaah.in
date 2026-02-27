<!--
  RoomingPage.svelte — Professional Room Allocation Dashboard
  
  Design: Compact card-based layout, efficient use of space
  Tone: Clean, data-dense, professional travel agency tool
-->
<script>
  import {
    Hotel,
    Bed,
    RefreshCw,
    Loader2,
    AlertTriangle,
    CheckCircle,
    Trash2,
    Sparkles,
    Users,
    X,
    Plus,
    FileDown,
    MessageCircle,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";
  import WhatsAppBlast from "../components/WhatsAppBlast.svelte";

  let { isOpen = false, onClose, groups = [], isPro = false } = $props();

  // State
  let selectedGroupId = $state(null);
  let summary = $state(null);
  let rooms = $state([]);
  let isLoading = $state(false);
  let isAutoRooming = $state(false);
  let error = $state(null);
  let success = $state(null);

  // Drag state
  let draggedMember = $state(null);
  let dragSourceRoomId = $state(null);

  // Add room state
  let showAddRoom = $state(false);
  let newRoomNumber = $state("");
  let newRoomGender = $state("male");
  let isAddingRoom = $state(false);

  // WA Blast state
  let waBlastOpen = $state(false);
  let waBlastGroup = $derived(
    selectedGroupId
      ? groups.find((g) => g.id == selectedGroupId) || null
      : null,
  );

  function exportRoomingPDF() {
    const groupName =
      groups.find((g) => g.id == selectedGroupId)?.name || "Rooming List";
    const now = new Date().toLocaleDateString("id-ID", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });

    let tableRows = "";
    rooms.forEach((room) => {
      const members = room.members || [];
      const genderLabel =
        room.gender_type === "male"
          ? "Laki-laki"
          : room.gender_type === "female"
            ? "Perempuan"
            : "Keluarga";
      if (members.length === 0) {
        tableRows += `<tr><td>${room.room_number}</td><td>${genderLabel}</td><td>${room.capacity || 4}</td><td>-</td><td>-</td></tr>`;
      } else {
        members.forEach((m, idx) => {
          tableRows += `<tr>
            ${idx === 0 ? `<td rowspan="${members.length}">${room.room_number}</td><td rowspan="${members.length}">${genderLabel}</td><td rowspan="${members.length}">${members.length}/${room.capacity || 4}</td>` : ""}
            <td>${m.nama || "-"}</td>
            <td>${m.no_paspor || "-"}</td>
          </tr>`;
        });
      }
    });

    const html = `<!DOCTYPE html><html><head><title>Rooming - ${groupName}</title>
      <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; padding: 2rem; color: #1e293b; }
        h1 { font-size: 1.25rem; margin: 0 0 0.25rem; }
        .subtitle { color: #64748b; font-size: 0.875rem; margin-bottom: 1.5rem; }
        table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
        th { background: #f1f5f9; padding: 0.5rem 0.75rem; text-align: left; font-weight: 600; border: 1px solid #e2e8f0; }
        td { padding: 0.5rem 0.75rem; border: 1px solid #e2e8f0; }
        .summary { display: flex; gap: 2rem; margin-bottom: 1rem; font-size: 0.8125rem; color: #475569; }
        @media print { body { padding: 0.5rem; } }
      </style>
    </head><body>
      <h1>🏨 ${groupName} — Rooming List</h1>
      <p class="subtitle">${now}</p>
      <div class="summary">
        <span>Total Kamar: <strong>${summary?.total_rooms || 0}</strong></span>
        <span>Assigned: <strong>${summary?.assigned_count || 0}</strong></span>
        <span>Unassigned: <strong>${summary?.unassigned_count || 0}</strong></span>
      </div>
      <table><thead><tr><th>No. Kamar</th><th>Gender</th><th>Kapasitas</th><th>Nama Jamaah</th><th>No. Paspor</th></tr></thead>
      <tbody>${tableRows}</tbody></table>
    </body></html>`;

    const printWindow = window.open("", "_blank");
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => {
      printWindow.print();
    }, 500);
  }

  // Derived
  let unassignedCount = $derived(summary?.unassigned_count || 0);

  async function loadData() {
    if (!selectedGroupId) {
      summary = null;
      rooms = [];
      return;
    }

    isLoading = true;
    error = null;

    try {
      const [summaryData, roomsData] = await Promise.all([
        ApiService.getRoomingSummary(selectedGroupId),
        ApiService.getGroupRooms(selectedGroupId),
      ]);

      summary = summaryData;
      rooms = roomsData.rooms || [];
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  async function runAutoRooming() {
    if (!selectedGroupId) return;

    isAutoRooming = true;
    error = null;
    success = null;

    try {
      const result = await ApiService.autoRooming(selectedGroupId, 4);
      success = result.summary;
      await loadData();
    } catch (e) {
      error = e.message;
    } finally {
      isAutoRooming = false;
    }
  }

  async function clearRooms() {
    if (!selectedGroupId) return;
    if (
      !confirm(
        "Reset semua kamar dan assignment? Tindakan ini tidak bisa dibatalkan.",
      )
    )
      return;

    isLoading = true;
    error = null;
    try {
      await ApiService.clearAutoRooming(selectedGroupId);
      await loadData();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  function handleDragStart(member, roomId) {
    draggedMember = member;
    dragSourceRoomId = roomId;
  }

  function handleDragOver(e) {
    // Allow drop only from same room type
    e.preventDefault();
  }

  async function handleDrop(targetRoomId) {
    if (!draggedMember || dragSourceRoomId === targetRoomId) {
      draggedMember = null;
      dragSourceRoomId = null;
      return;
    }

    // Find target room and check capacity
    const targetRoom = rooms.find((r) => r.id === targetRoomId);
    if (targetRoom && targetRoom.is_full) {
      error = "Kamar sudah penuh";
      draggedMember = null;
      dragSourceRoomId = null;
      return;
    }

    // --- OPTIMISTIC UI UPDATE --- move member instantly
    const memberId = draggedMember.id;
    const sourceRoomId = dragSourceRoomId;

    // Snapshot for rollback
    const prevRooms = JSON.parse(JSON.stringify(rooms));
    const prevSummary = summary ? JSON.parse(JSON.stringify(summary)) : null;

    // Find member data from source room
    let memberData = null;
    if (sourceRoomId !== null) {
      const srcRoom = rooms.find((r) => r.id === sourceRoomId);
      if (srcRoom) {
        memberData = srcRoom.members.find((m) => m.id === memberId);
        // Remove from source room
        srcRoom.members = srcRoom.members.filter((m) => m.id !== memberId);
        srcRoom.occupied = srcRoom.members.length;
        srcRoom.is_full = srcRoom.occupied >= srcRoom.capacity;
      }
    }

    // Add to target room
    if (targetRoom && memberData) {
      targetRoom.members = [...targetRoom.members, memberData];
      targetRoom.occupied = targetRoom.members.length;
      targetRoom.is_full = targetRoom.occupied >= targetRoom.capacity;
    }

    // Auto-delete empty source room
    if (sourceRoomId !== null) {
      const srcRoom = rooms.find((r) => r.id === sourceRoomId);
      if (srcRoom && srcRoom.members.length === 0) {
        rooms = rooms.filter((r) => r.id !== sourceRoomId);
        if (summary) {
          summary = { ...summary, total_rooms: summary.total_rooms - 1 };
        }
      }
    }

    // Force Svelte reactivity
    rooms = [...rooms];

    // Update summary counts optimistically
    if (summary && sourceRoomId === null) {
      // Moving from unassigned → room
      summary = {
        ...summary,
        assigned_count: summary.assigned_count + 1,
        unassigned_count: summary.unassigned_count - 1,
      };
    }

    // Clear drag state immediately
    draggedMember = null;
    dragSourceRoomId = null;

    // --- BACKGROUND SYNC ---
    try {
      if (sourceRoomId !== null) {
        await ApiService.unassignMember(memberId);
      }
      await ApiService.assignMemberToRoom(memberId, targetRoomId);
    } catch (e) {
      // Revert on failure
      rooms = prevRooms;
      summary = prevSummary;
      error = e.message;
    }
  }

  async function removeFromRoom(memberId) {
    // --- OPTIMISTIC UI UPDATE ---
    const prevRooms = JSON.parse(JSON.stringify(rooms));
    const prevSummary = summary ? JSON.parse(JSON.stringify(summary)) : null;

    // Find and remove the member from their room locally
    for (const room of rooms) {
      const idx = room.members.findIndex((m) => m.id === memberId);
      if (idx !== -1) {
        room.members.splice(idx, 1);
        room.occupied = room.members.length;
        room.is_full = room.occupied >= room.capacity;
        break;
      }
    }
    // Auto-delete empty rooms
    const emptyCount = rooms.filter((r) => r.members.length === 0).length;
    rooms = rooms.filter((r) => r.members.length > 0);

    if (summary) {
      summary = {
        ...summary,
        assigned_count: summary.assigned_count - 1,
        unassigned_count: summary.unassigned_count + 1,
        total_rooms: summary.total_rooms - emptyCount,
      };
    }

    // --- BACKGROUND SYNC ---
    try {
      await ApiService.unassignMember(memberId);
    } catch (e) {
      rooms = prevRooms;
      summary = prevSummary;
      error = e.message;
    }
  }

  function getGenderColor(genderType) {
    if (genderType === "male") return "border-blue-200 bg-blue-50";
    if (genderType === "female") return "border-pink-200 bg-pink-50";
    return "border-purple-200 bg-purple-50";
  }

  function getGenderBadge(gender) {
    if (gender === "male") return "bg-blue-100 text-blue-700";
    if (gender === "female") return "bg-pink-100 text-pink-700";
    return "bg-slate-100 text-slate-600";
  }

  async function addRoom() {
    if (!selectedGroupId || !newRoomNumber.trim()) return;

    isAddingRoom = true;
    error = null;

    try {
      const newRoom = await ApiService.createRoom(
        selectedGroupId,
        newRoomNumber.trim(),
        newRoomGender,
        "quad",
        4,
      );
      // Optimistic: add to local state
      rooms = [
        ...rooms,
        { ...newRoom, members: [], occupied: 0, is_full: false },
      ];
      if (summary) {
        summary = { ...summary, total_rooms: summary.total_rooms + 1 };
      }
      // Reset form
      newRoomNumber = "";
      newRoomGender = "male";
      showAddRoom = false;
    } catch (e) {
      error = e.message;
    } finally {
      isAddingRoom = false;
    }
  }

  async function deleteRoom(roomId) {
    // --- OPTIMISTIC UI ---
    const prevRooms = JSON.parse(JSON.stringify(rooms));
    const prevSummary = summary ? JSON.parse(JSON.stringify(summary)) : null;

    const room = rooms.find((r) => r.id === roomId);
    const memberCount = room ? room.members.length : 0;

    rooms = rooms.filter((r) => r.id !== roomId);
    if (summary) {
      summary = {
        ...summary,
        total_rooms: summary.total_rooms - 1,
        assigned_count: summary.assigned_count - memberCount,
        unassigned_count: summary.unassigned_count + memberCount,
      };
    }

    // --- BACKGROUND SYNC ---
    try {
      await ApiService.deleteRoom(roomId);
    } catch (e) {
      rooms = prevRooms;
      summary = prevSummary;
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
          class="w-8 h-8 bg-indigo-100 rounded-lg flex items-center justify-center"
        >
          <Hotel class="w-4 h-4 text-indigo-600" />
        </div>
        <div>
          <h1 class="text-sm font-semibold text-slate-800">Auto-Rooming</h1>
          <p class="text-xs text-slate-500">Alokasi kamar hotel otomatis</p>
        </div>
      </div>
    </header>

    <!-- Toolbar -->
    <div
      class="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 bg-white"
    >
      <select
        id="room-group-select"
        bind:value={selectedGroupId}
        onchange={loadData}
        class="flex-1 max-w-[200px] text-sm px-2.5 py-1.5 border border-slate-300 rounded-lg bg-white focus:ring-2 focus:ring-indigo-500"
      >
        <option value="">Pilih Grup</option>
        {#each groups as group}
          <option value={group.id}>{group.name} ({group.member_count})</option>
        {/each}
      </select>

      {#if selectedGroupId}
        <button
          type="button"
          onclick={loadData}
          disabled={isLoading}
          class="p-1.5 text-slate-500 hover:bg-slate-100 rounded-lg disabled:opacity-50"
        >
          <RefreshCw class="w-4 h-4 {isLoading ? 'animate-spin' : ''}" />
        </button>
      {/if}

      <div class="flex items-center gap-2 ml-auto">
        <button
          type="button"
          onclick={runAutoRooming}
          disabled={isAutoRooming || unassignedCount === 0}
          class="px-3 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1.5"
        >
          {#if isAutoRooming}<Loader2
              class="w-3 h-3 animate-spin"
            />{:else}<Sparkles class="w-3 h-3" />{/if}
          Auto-Generate
        </button>
        {#if summary?.total_rooms > 0}
          <button
            type="button"
            onclick={exportRoomingPDF}
            class="px-3 py-1.5 border border-indigo-200 text-indigo-600 text-xs font-medium rounded-lg hover:bg-indigo-50 flex items-center gap-1.5"
          >
            <FileDown class="w-3 h-3" />
            PDF
          </button>
          <button
            type="button"
            onclick={() => (waBlastOpen = true)}
            class="px-3 py-1.5 border border-green-200 text-green-600 text-xs font-medium rounded-lg hover:bg-green-50 flex items-center gap-1.5"
          >
            <MessageCircle class="w-3 h-3" />
            WA
          </button>
          <button
            type="button"
            onclick={clearRooms}
            disabled={isLoading}
            class="px-3 py-1.5 border border-red-200 text-red-600 text-xs font-medium rounded-lg hover:bg-red-50 disabled:opacity-50 flex items-center gap-1.5"
          >
            <Trash2 class="w-3 h-3" />
            Reset
          </button>
        {/if}
      </div>
    </div>

    <!-- Messages -->
    {#if error}
      <div
        class="mx-4 mt-2 bg-red-50 border border-red-200 rounded-lg px-3 py-2 flex items-center gap-2 text-sm"
      >
        <AlertTriangle class="w-4 h-4 text-red-500" />
        <span class="text-red-700 flex-1">{error}</span>
        <button
          type="button"
          onclick={() => (error = null)}
          class="text-red-500"><X class="w-4 h-4" /></button
        >
      </div>
    {/if}

    {#if success}
      <div
        class="mx-4 mt-2 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 flex items-center gap-2 text-sm"
      >
        <CheckCircle class="w-4 h-4 text-emerald-500" />
        <span class="text-emerald-700 flex-1">{success}</span>
        <button
          type="button"
          onclick={() => (success = null)}
          class="text-emerald-500"><X class="w-4 h-4" /></button
        >
      </div>
    {/if}

    <!-- Content -->
    <div class="flex-1 overflow-auto">
      {#if isLoading}
        <div class="flex items-center justify-center py-12">
          <Loader2 class="w-6 h-6 animate-spin text-indigo-500" />
        </div>
      {:else if !selectedGroupId}
        <div
          class="flex flex-col items-center justify-center py-12 text-slate-400"
        >
          <Hotel class="w-10 h-10 mb-2" />
          <p class="text-sm">Pilih grup untuk memulai</p>
        </div>
      {:else if summary}
        <!-- Stats - Ultra Compact -->
        <div class="grid grid-cols-4 gap-2 p-3">
          <div class="stat-card">
            <span class="stat-value text-slate-800"
              >{summary.total_members}</span
            >
            <span class="stat-label">Total</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-emerald-600"
              >{summary.assigned_count}</span
            >
            <span class="stat-label">Ditempat</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-amber-600">{unassignedCount}</span>
            <span class="stat-label">Belum</span>
          </div>
          <div class="stat-card">
            <span class="stat-value text-indigo-600">{summary.total_rooms}</span
            >
            <span class="stat-label">Kamar</span>
          </div>
        </div>

        <!-- Rooms Grid -->
        {#if rooms.length > 0}
          <div
            class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 px-3 pb-3"
          >
            {#each rooms as room}
              <article
                class="rounded-lg border-2 {getGenderColor(
                  room.gender_type,
                )} p-2.5 text-xs"
                ondragover={handleDragOver}
                ondrop={() => handleDrop(room.id)}
                role="region"
                aria-label="Kamar {room.room_number}"
              >
                <!-- Room Header -->
                <div class="flex items-center justify-between mb-1.5">
                  <div class="flex items-center gap-1">
                    <Bed class="w-3.5 h-3.5 text-slate-500" />
                    <span class="font-bold text-slate-800"
                      >{room.room_number}</span
                    >
                  </div>
                  <div class="flex items-center gap-1">
                    <span
                      class="px-1 py-0.5 rounded text-[10px] font-medium {getGenderBadge(
                        room.gender_type,
                      )}"
                    >
                      {room.gender_type === "male"
                        ? "L"
                        : room.gender_type === "female"
                          ? "P"
                          : "M"}
                    </span>
                    {#if room.is_auto_assigned}
                      <span
                        class="px-1 py-0.5 rounded text-[10px] bg-indigo-100 text-indigo-600"
                        >A</span
                      >
                    {/if}
                    <button
                      type="button"
                      onclick={() => deleteRoom(room.id)}
                      class="p-0.5 text-slate-300 hover:text-red-500 transition-colors"
                      title="Hapus kamar"
                    >
                      <Trash2 class="w-3 h-3" />
                    </button>
                  </div>
                </div>

                <!-- Capacity Bar -->
                <div class="h-1 bg-slate-200 rounded-full mb-2 overflow-hidden">
                  <div
                    class="h-full {room.is_full
                      ? 'bg-red-400'
                      : 'bg-emerald-400'} transition-all"
                    style="width: {(room.occupied / room.capacity) * 100}%"
                  ></div>
                </div>
                <div class="text-[10px] text-slate-500 mb-1.5">
                  {room.occupied}/{room.capacity}
                  {room.is_full ? "(Penuh)" : ""}
                </div>

                <!-- Members -->
                <div class="space-y-1">
                  {#each room.members as member}
                    <div
                      class="bg-white rounded px-2 py-1 flex items-center justify-between border border-slate-100 cursor-move"
                      draggable="true"
                      role="listitem"
                      ondragstart={() =>
                        handleDragStart({ id: member.id }, room.id)}
                    >
                      <span class="truncate text-slate-700"
                        >{member.nama || "Tanpa Nama"}</span
                      >
                      <button
                        type="button"
                        onclick={() => removeFromRoom(member.id)}
                        class="text-slate-300 hover:text-red-500 ml-1"
                      >
                        <X class="w-3 h-3" />
                      </button>
                    </div>
                  {/each}
                </div>

                <!-- Drop Zone -->
                {#if !room.is_full}
                  <div
                    class="mt-1.5 border border-dashed border-slate-300 rounded p-2 text-center text-slate-400 text-[10px]"
                  >
                    Drop di sini
                  </div>
                {/if}
              </article>
            {/each}

            <!-- Add Room Card -->
            {#if showAddRoom}
              <article
                class="rounded-lg border-2 border-dashed border-indigo-300 bg-indigo-50/50 p-2.5 text-xs"
              >
                <div class="flex items-center justify-between mb-2">
                  <span class="font-bold text-indigo-700 text-xs"
                    >Kamar Baru</span
                  >
                  <button
                    type="button"
                    onclick={() => {
                      showAddRoom = false;
                    }}
                    class="text-slate-400 hover:text-red-500"
                  >
                    <X class="w-3.5 h-3.5" />
                  </button>
                </div>
                <div class="space-y-1.5">
                  <input
                    type="text"
                    bind:value={newRoomNumber}
                    placeholder="No. kamar (cth: 301)"
                    class="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-md bg-white focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 outline-none"
                  />
                  <select
                    bind:value={newRoomGender}
                    class="w-full px-2 py-1.5 text-xs border border-slate-300 rounded-md bg-white focus:ring-2 focus:ring-indigo-400"
                  >
                    <option value="male">Laki-laki</option>
                    <option value="female">Perempuan</option>
                    <option value="family">Keluarga</option>
                  </select>
                  <button
                    type="button"
                    onclick={addRoom}
                    disabled={isAddingRoom || !newRoomNumber.trim()}
                    class="w-full px-2 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-1"
                  >
                    {#if isAddingRoom}<Loader2
                        class="w-3 h-3 animate-spin"
                      />{:else}<Plus class="w-3 h-3" />{/if}
                    Buat Kamar
                  </button>
                </div>
              </article>
            {:else}
              <button
                type="button"
                onclick={() => {
                  showAddRoom = true;
                }}
                class="rounded-lg border-2 border-dashed border-slate-300 p-2.5 text-xs flex flex-col items-center justify-center gap-1.5 text-slate-400 hover:border-indigo-400 hover:text-indigo-500 hover:bg-indigo-50/30 transition-colors min-h-[80px] cursor-pointer"
              >
                <Plus class="w-5 h-5" />
                <span class="font-medium">Tambah Kamar</span>
              </button>
            {/if}
          </div>
        {:else}
          <div class="text-center py-8 text-slate-400 text-sm">
            <Hotel class="w-8 h-8 mx-auto mb-2" />
            <p>Belum ada kamar</p>
            <p class="text-xs mt-1">Klik "Auto-Generate" atau tambah manual</p>
            <button
              type="button"
              onclick={() => {
                showAddRoom = true;
              }}
              class="mt-3 inline-flex items-center gap-1 px-3 py-1.5 border border-dashed border-indigo-300 text-indigo-500 text-xs font-medium rounded-lg hover:bg-indigo-50 transition-colors"
            >
              <Plus class="w-3.5 h-3.5" />
              Tambah Kamar Manual
            </button>
          </div>
        {/if}

        <!-- Unassigned Notice -->
        {#if unassignedCount > 0}
          <div
            class="mx-3 mb-3 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 flex items-center gap-2 text-xs"
          >
            <Users class="w-4 h-4 text-amber-500" />
            <span class="text-amber-700">
              <strong>{unassignedCount}</strong> jamaah belum ditempatkan
            </span>
          </div>
        {/if}
      {:else}
        <div class="text-center py-8 text-slate-400 text-sm">
          Tidak ada data
        </div>
      {/if}
    </div>
  </div>
{/if}

<!-- WhatsApp Blast Modal -->
<WhatsAppBlast
  isOpen={waBlastOpen}
  onClose={() => (waBlastOpen = false)}
  group={waBlastGroup}
/>

<script>
  import { onMount } from "svelte";
  import {
    AlertCircle,
    FileText,
    Loader2,
    Search,
    UserPlus,
    UsersRound,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";

  let { onNavigate = () => {} } = $props();

  let groups = $state([]);
  let selectedGroupId = $state("");
  let members = $state([]);
  let isLoadingGroups = $state(true);
  let isLoadingMembers = $state(false);
  let error = $state("");
  let search = $state("");

  let selectedGroup = $derived(
    groups.find((group) => String(group.id) === String(selectedGroupId)) || null,
  );

  let filteredMembers = $derived(
    members.filter((member) => {
      const needle = search.trim().toLowerCase();
      if (!needle) return true;
      return [
        member.nama,
        member.nama_paspor,
        member.no_paspor,
        member.no_identitas,
        member.no_visa,
      ]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    }),
  );

  onMount(loadGroups);

  async function loadGroups() {
    isLoadingGroups = true;
    error = "";
    try {
      const result = await ApiService.listGroups();
      groups = result.groups || [];
      selectedGroupId = groups[0]?.id ? String(groups[0].id) : "";
      await loadMembers();
    } catch (e) {
      error = e.message;
    } finally {
      isLoadingGroups = false;
    }
  }

  async function loadMembers() {
    members = [];
    if (!selectedGroupId) return;
    isLoadingMembers = true;
    error = "";
    try {
      const group = await ApiService.getGroup(selectedGroupId);
      members = group.members || [];
    } catch (e) {
      error = e.message;
    } finally {
      isLoadingMembers = false;
    }
  }

  function displayName(member) {
    return member.nama || member.nama_paspor || "Tanpa nama";
  }
</script>

<div class="min-h-screen bg-slate-50/70 p-4 lg:p-8">
  <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-xl font-bold text-slate-900">Data Jamaah</h1>
      <p class="text-sm text-slate-500">Kelola seluruh data calon jamaah dari setiap grup keberangkatan.</p>
    </div>
    <button
      type="button"
      onclick={() => onNavigate("scanner")}
      class="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary-500/20 transition-all hover:-translate-y-0.5"
    >
      <UserPlus class="h-4 w-4" />
      Tambah via Scanner
    </button>
  </div>

  {#if error}
    <div class="mb-5 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-5 w-5 flex-shrink-0" />
      <span>{error}</span>
    </div>
  {/if}

  <div class="mb-6 grid gap-4 lg:grid-cols-[minmax(0,1fr)_280px]">
    <div class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <label for="jamaah-group-select" class="mb-2 block text-xs font-bold uppercase tracking-wide text-slate-400">Grup Keberangkatan</label>
      <select
        id="jamaah-group-select"
        bind:value={selectedGroupId}
        onchange={loadMembers}
        class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 outline-none transition focus:border-primary-400 focus:bg-white"
      >
        {#if isLoadingGroups}
          <option>Memuat grup...</option>
        {:else if groups.length === 0}
          <option value="">Belum ada grup</option>
        {:else}
          {#each groups as group}
            <option value={String(group.id)}>{group.name} - {group.member_count || 0} jamaah</option>
          {/each}
        {/if}
      </select>
    </div>

    <div class="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
      <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Total di Grup</p>
      <div class="mt-2 flex items-end gap-2">
        <span class="text-3xl font-extrabold text-slate-900">{members.length}</span>
        <span class="pb-1 text-sm text-slate-500">jamaah</span>
      </div>
    </div>
  </div>

  <div class="rounded-3xl border border-slate-100 bg-white shadow-sm">
    <div class="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h2 class="text-sm font-bold text-slate-900">{selectedGroup?.name || "Daftar Jamaah"}</h2>
        <p class="text-xs text-slate-500">Data operasional yang tersimpan dari hasil scan dan input grup.</p>
      </div>
      <div class="relative w-full sm:w-72">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          bind:value={search}
          class="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none transition focus:border-primary-400 focus:bg-white"
          placeholder="Cari nama, paspor, NIK..."
        />
      </div>
    </div>

    {#if isLoadingMembers}
      <div class="flex items-center justify-center gap-3 p-12 text-sm text-slate-500">
        <Loader2 class="h-5 w-5 animate-spin text-primary-500" />
        Memuat data jamaah...
      </div>
    {:else if filteredMembers.length === 0}
      <div class="p-12 text-center">
        <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100">
          <UsersRound class="h-7 w-7 text-slate-400" />
        </div>
        <h3 class="text-sm font-bold text-slate-900">Belum ada data jamaah</h3>
        <p class="mt-1 text-sm text-slate-500">Pilih grup lain atau tambah data dari AI Scanner.</p>
      </div>
    {:else}
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-400">
            <tr>
              <th class="px-5 py-3 font-bold">Nama</th>
              <th class="px-5 py-3 font-bold">Paspor</th>
              <th class="px-5 py-3 font-bold">Identitas</th>
              <th class="px-5 py-3 font-bold">Visa</th>
              <th class="px-5 py-3 font-bold">Dokumen</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            {#each filteredMembers as member}
              <tr class="hover:bg-slate-50/70">
                <td class="px-5 py-4">
                  <p class="font-semibold text-slate-900">{displayName(member)}</p>
                  <p class="text-xs text-slate-400">{member.title || "-"} {member.tanggal_lahir || ""}</p>
                </td>
                <td class="px-5 py-4 text-slate-600">{member.no_paspor || "-"}</td>
                <td class="px-5 py-4 text-slate-600">{member.no_identitas || "-"}</td>
                <td class="px-5 py-4 text-slate-600">{member.no_visa || "-"}</td>
                <td class="px-5 py-4">
                  <span class="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-700">
                    <FileText class="h-3.5 w-3.5" />
                    Tersimpan
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
  </div>
</div>

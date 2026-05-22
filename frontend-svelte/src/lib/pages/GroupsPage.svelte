<script>
  import { onMount } from "svelte";
  import {
    AlertCircle,
    Building2,
    CalendarDays,
    Hotel,
    Loader2,
    Plus,
    UsersRound,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";

  let { onNavigate = () => {} } = $props();

  let groups = $state([]);
  let isLoading = $state(true);
  let isCreating = $state(false);
  let showCreate = $state(false);
  let newGroupName = $state("");
  let newGroupDescription = $state("");
  let error = $state("");

  onMount(loadGroups);

  async function loadGroups() {
    isLoading = true;
    error = "";
    try {
      const result = await ApiService.listGroups();
      groups = result.groups || [];
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  async function createGroup() {
    if (!newGroupName.trim()) return;
    isCreating = true;
    error = "";
    try {
      const group = await ApiService.createGroup(newGroupName.trim(), newGroupDescription.trim());
      groups = [group, ...groups];
      newGroupName = "";
      newGroupDescription = "";
      showCreate = false;
    } catch (e) {
      error = e.message;
    } finally {
      isCreating = false;
    }
  }

  function formatDate(value) {
    if (!value) return "-";
    return new Date(value).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }
</script>

<div class="min-h-screen bg-slate-50/70 p-4 lg:p-8">
  <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-xl font-bold text-slate-900">Grup & Hotel</h1>
      <p class="text-sm text-slate-500">Atur grup keberangkatan sebelum masuk ke rooming hotel.</p>
    </div>
    <button
      type="button"
      onclick={() => (showCreate = !showCreate)}
      class="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary-500/20 transition-all hover:-translate-y-0.5"
    >
      <Plus class="h-4 w-4" />
      Buat Grup Baru
    </button>
  </div>

  {#if error}
    <div class="mb-5 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-5 w-5 flex-shrink-0" />
      <span>{error}</span>
    </div>
  {/if}

  {#if showCreate}
    <div class="mb-6 rounded-3xl border border-primary-100 bg-white p-5 shadow-sm">
      <div class="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
        <input
          bind:value={newGroupName}
          class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-primary-400 focus:bg-white"
          placeholder="Nama grup, mis. Umrah Maret 2026"
        />
        <input
          bind:value={newGroupDescription}
          class="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-primary-400 focus:bg-white"
          placeholder="Catatan singkat"
        />
        <button
          type="button"
          onclick={createGroup}
          disabled={isCreating || !newGroupName.trim()}
          class="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {#if isCreating}
            <Loader2 class="h-4 w-4 animate-spin" />
          {/if}
          Simpan
        </button>
      </div>
    </div>
  {/if}

  {#if isLoading}
    <div class="flex items-center justify-center gap-3 rounded-3xl border border-slate-100 bg-white p-12 text-sm text-slate-500 shadow-sm">
      <Loader2 class="h-5 w-5 animate-spin text-primary-500" />
      Memuat grup...
    </div>
  {:else if groups.length === 0}
    <div class="rounded-3xl border border-slate-100 bg-white p-12 text-center shadow-sm">
      <div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-50">
        <Building2 class="h-7 w-7 text-primary-600" />
      </div>
      <h3 class="text-sm font-bold text-slate-900">Belum ada grup keberangkatan</h3>
      <p class="mt-1 text-sm text-slate-500">Buat grup untuk menampung data jamaah, hotel, rooming, dan manifest.</p>
    </div>
  {:else}
    <div class="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
      {#each groups as group}
        <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-lg">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div class="flex items-center gap-3">
              <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-50 text-primary-600">
                <Building2 class="h-5 w-5" />
              </div>
              <div>
                <h2 class="font-bold text-slate-900">{group.name}</h2>
                <p class="text-xs text-slate-500">{group.description || "Tanpa catatan"}</p>
              </div>
            </div>
          </div>

          <div class="mb-5 grid grid-cols-2 gap-3">
            <div class="rounded-2xl bg-slate-50 p-3">
              <div class="mb-1 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
                <UsersRound class="h-3.5 w-3.5" />
                Jamaah
              </div>
              <p class="text-xl font-extrabold text-slate-900">{group.member_count || 0}</p>
            </div>
            <div class="rounded-2xl bg-slate-50 p-3">
              <div class="mb-1 flex items-center gap-1.5 text-xs font-semibold text-slate-500">
                <CalendarDays class="h-3.5 w-3.5" />
                Update
              </div>
              <p class="text-sm font-bold text-slate-900">{formatDate(group.updated_at || group.created_at)}</p>
            </div>
          </div>

          <div class="flex gap-2">
            <button
              type="button"
              onclick={() => onNavigate("jamaah")}
              class="flex-1 rounded-xl border border-slate-200 px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Lihat Jamaah
            </button>
            <button
              type="button"
              onclick={() => onNavigate("rooming")}
              class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-primary-600 px-3 py-2.5 text-sm font-semibold text-white transition hover:bg-primary-700"
            >
              <Hotel class="h-4 w-4" />
              Rooming
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}
</div>

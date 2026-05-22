<script>
  import { onMount } from "svelte";
  import {
    AlertCircle,
    ClipboardCheck,
    Copy,
    ExternalLink,
    Loader2,
    LockKeyhole,
    Share2,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";

  let groups = $state([]);
  let selectedGroupId = $state("");
  let pin = $state("");
  let expiry = $state(30);
  let isLoading = $state(true);
  let isSharing = $state(false);
  let error = $state("");
  let shareResult = $state(null);
  let copied = $state(false);

  let selectedGroup = $derived(
    groups.find((group) => String(group.id) === String(selectedGroupId)) || null,
  );

  onMount(loadGroups);

  async function loadGroups() {
    isLoading = true;
    error = "";
    try {
      const result = await ApiService.listGroups();
      groups = result.groups || [];
      selectedGroupId = groups[0]?.id ? String(groups[0].id) : "";
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  async function createShareLink() {
    if (!selectedGroupId) return;
    if (!/^\d{4,6}$/.test(pin)) {
      error = "PIN harus 4-6 digit angka.";
      return;
    }
    isSharing = true;
    error = "";
    shareResult = null;
    try {
      shareResult = await ApiService.shareGroup(selectedGroupId, pin, expiry);
    } catch (e) {
      error = e.message;
    } finally {
      isSharing = false;
    }
  }

  async function copyUrl() {
    if (!shareResult?.shared_url) return;
    await navigator.clipboard.writeText(shareResult.shared_url);
    copied = true;
    setTimeout(() => (copied = false), 1800);
  }
</script>

<div class="min-h-screen bg-slate-50/70 p-4 lg:p-8">
  <div class="mb-6">
    <h1 class="text-xl font-bold text-slate-900">Manifest Digital</h1>
    <p class="text-sm text-slate-500">Buat link manifest ber-PIN untuk mutawwif dan tim lapangan.</p>
  </div>

  {#if error}
    <div class="mb-5 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-5 w-5 flex-shrink-0" />
      <span>{error}</span>
    </div>
  {/if}

  <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
    <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div class="mb-5 flex items-center gap-3">
        <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
          <ClipboardCheck class="h-5 w-5" />
        </div>
        <div>
          <h2 class="text-sm font-bold text-slate-900">Pilih Grup</h2>
          <p class="text-xs text-slate-500">Manifest mengikuti data jamaah dan rooming pada grup yang dipilih.</p>
        </div>
      </div>

      {#if isLoading}
        <div class="flex items-center gap-3 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
          <Loader2 class="h-5 w-5 animate-spin text-primary-500" />
          Memuat grup...
        </div>
      {:else}
        <select
          bind:value={selectedGroupId}
          class="mb-5 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-slate-700 outline-none transition focus:border-primary-400 focus:bg-white"
        >
          {#each groups as group}
            <option value={String(group.id)}>{group.name} - {group.member_count || 0} jamaah</option>
          {/each}
        </select>

        <div class="grid gap-4 sm:grid-cols-2">
          <div>
            <label for="manifest-pin" class="mb-2 block text-xs font-bold uppercase tracking-wide text-slate-400">PIN Manifest</label>
            <div class="relative">
              <LockKeyhole class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                id="manifest-pin"
                bind:value={pin}
                maxlength="6"
                class="w-full rounded-xl border border-slate-200 bg-slate-50 py-3 pl-10 pr-3 text-sm outline-none transition focus:border-primary-400 focus:bg-white"
                placeholder="1234"
              />
            </div>
          </div>
          <div>
            <label for="manifest-expiry" class="mb-2 block text-xs font-bold uppercase tracking-wide text-slate-400">Masa Berlaku</label>
            <select
              id="manifest-expiry"
              bind:value={expiry}
              class="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm outline-none transition focus:border-primary-400 focus:bg-white"
            >
              <option value={7}>7 hari</option>
              <option value={30}>30 hari</option>
              <option value={90}>90 hari</option>
            </select>
          </div>
        </div>

        <button
          type="button"
          onclick={createShareLink}
          disabled={isSharing || !selectedGroupId}
          class="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-primary-500/20 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          {#if isSharing}
            <Loader2 class="h-4 w-4 animate-spin" />
          {:else}
            <Share2 class="h-4 w-4" />
          {/if}
          Buat Link Manifest
        </button>
      {/if}
    </div>

    <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <h2 class="text-sm font-bold text-slate-900">Status Manifest</h2>
      <p class="mt-1 text-xs text-slate-500">{selectedGroup?.name || "Pilih grup untuk membuat manifest digital."}</p>

      {#if shareResult}
        <div class="mt-5 rounded-2xl border border-emerald-100 bg-emerald-50 p-4">
          <p class="text-xs font-bold uppercase tracking-wide text-emerald-700">Link Aktif</p>
          <p class="mt-2 break-all text-sm font-medium text-emerald-900">{shareResult.shared_url}</p>
          <div class="mt-4 flex gap-2">
            <button
              type="button"
              onclick={copyUrl}
              class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-white px-3 py-2.5 text-sm font-semibold text-emerald-700 shadow-sm"
            >
              <Copy class="h-4 w-4" />
              {copied ? "Tersalin" : "Salin"}
            </button>
            <a
              href={shareResult.shared_url}
              target="_blank"
              rel="noreferrer"
              class="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-600 px-3 py-2.5 text-sm font-semibold text-white"
            >
              <ExternalLink class="h-4 w-4" />
              Buka
            </a>
          </div>
        </div>
      {:else}
        <div class="mt-5 rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">
          Link manifest akan muncul di sini setelah dibuat.
        </div>
      {/if}
    </div>
  </div>
</div>

<script>
  import { onMount } from "svelte";
  import {
    AlertCircle,
    BarChart3,
    CheckCircle,
    Loader2,
    TrendingUp,
    UsersRound,
  } from "lucide-svelte";
  import { ApiService } from "../services/api.js";

  let stats = $state(null);
  let isLoading = $state(true);
  let error = $state("");

  onMount(loadStats);

  async function loadStats() {
    isLoading = true;
    error = "";
    try {
      stats = await ApiService.getDashboardStats();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  }

  let maxTrend = $derived(
    Math.max(...(stats?.monthly_trend || []).map((item) => item.count || 0), 1),
  );
</script>

<div class="min-h-screen bg-slate-50/70 p-4 lg:p-8">
  <div class="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-xl font-bold text-slate-900">Analytics</h1>
      <p class="text-sm text-slate-500">Statistik operasional jamaah, grup, dokumen, dan perlengkapan.</p>
    </div>
    <button
      type="button"
      onclick={loadStats}
      class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50"
    >
      Refresh
    </button>
  </div>

  {#if error}
    <div class="mb-5 flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 p-4 text-sm text-red-700">
      <AlertCircle class="mt-0.5 h-5 w-5 flex-shrink-0" />
      <span>{error}</span>
    </div>
  {/if}

  {#if isLoading}
    <div class="flex items-center justify-center gap-3 rounded-3xl border border-slate-100 bg-white p-12 text-sm text-slate-500 shadow-sm">
      <Loader2 class="h-5 w-5 animate-spin text-primary-500" />
      Memuat analytics...
    </div>
  {:else if stats}
    <div class="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <UsersRound class="mb-4 h-6 w-6 text-primary-600" />
        <p class="text-3xl font-extrabold text-slate-900">{stats.total_jamaah || 0}</p>
        <p class="text-sm text-slate-500">Total Jamaah</p>
      </div>
      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <BarChart3 class="mb-4 h-6 w-6 text-emerald-600" />
        <p class="text-3xl font-extrabold text-slate-900">{stats.total_groups || 0}</p>
        <p class="text-sm text-slate-500">Total Grup</p>
      </div>
      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <CheckCircle class="mb-4 h-6 w-6 text-violet-600" />
        <p class="text-3xl font-extrabold text-slate-900">{stats.equipment_rate || 0}%</p>
        <p class="text-sm text-slate-500">Perlengkapan</p>
      </div>
      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <TrendingUp class="mb-4 h-6 w-6 text-amber-600" />
        <p class="text-3xl font-extrabold text-slate-900">{stats.jamaah_this_month || 0}</p>
        <p class="text-sm text-slate-500">Jamaah Bulan Ini</p>
      </div>
    </div>

    <div class="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <h2 class="mb-5 text-sm font-bold text-slate-900">Trend 6 Bulan</h2>
        <div class="space-y-4">
          {#each stats.monthly_trend || [] as item}
            <div>
              <div class="mb-1 flex items-center justify-between text-xs">
                <span class="font-semibold text-slate-600">{item.label}</span>
                <span class="text-slate-400">{item.count}</span>
              </div>
              <div class="h-2 overflow-hidden rounded-full bg-slate-100">
                <div class="h-full rounded-full bg-gradient-to-r from-primary-600 to-emerald-500" style={`width: ${Math.max(6, ((item.count || 0) / maxTrend) * 100)}%`}></div>
              </div>
            </div>
          {/each}
          {#if (stats.monthly_trend || []).length === 0}
            <p class="rounded-2xl bg-slate-50 p-5 text-sm text-slate-500">Belum ada data trend.</p>
          {/if}
        </div>
      </div>

      <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <h2 class="mb-5 text-sm font-bold text-slate-900">Komposisi Jamaah</h2>
        <div class="space-y-3">
          <div class="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
            <span class="text-sm font-semibold text-slate-600">Laki-laki</span>
            <span class="font-extrabold text-slate-900">{stats.gender_breakdown?.male || 0}</span>
          </div>
          <div class="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
            <span class="text-sm font-semibold text-slate-600">Perempuan</span>
            <span class="font-extrabold text-slate-900">{stats.gender_breakdown?.female || 0}</span>
          </div>
          <div class="flex items-center justify-between rounded-2xl bg-slate-50 p-4">
            <span class="text-sm font-semibold text-slate-600">Data belum lengkap</span>
            <span class="font-extrabold text-slate-900">{stats.gender_breakdown?.unknown || 0}</span>
          </div>
        </div>
      </div>
    </div>
  {/if}
</div>

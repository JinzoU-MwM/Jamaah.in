<!--
  Dashboard.svelte — Analytics Dashboard for Agency Owners
  Shows stats, trends, and overview of jamaah data.
-->
<script>
  import { onMount } from "svelte";
  import {
    Users,
    FolderOpen,
    TrendingUp,
    Shield,
    AlertTriangle,
    CalendarDays,
    BarChart3,
    Loader2,
    ScanLine,
  } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let {
    user = null,
    subscription = null,
    onLogout,
    onSubscriptionChange = null,
    onNavigate = null,
  } = $props();

  let stats = $state(null);
  let isLoading = $state(true);
  let error = $state("");

  let isPro = $derived(
    subscription?.plan === "pro" && subscription?.status === "active",
  );

  onMount(async () => {
    try {
      stats = await ApiService.getDashboardStats();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  });

  // SVG sparkline helper
  function sparklinePath(data, width = 200, height = 40) {
    if (!data || data.length < 2) return "";
    const max = Math.max(...data.map((d) => d.count), 1);
    const step = width / (data.length - 1);
    return data
      .map((d, i) => {
        const x = i * step;
        const y = height - (d.count / max) * (height - 4);
        return `${i === 0 ? "M" : "L"} ${x} ${y}`;
      })
      .join(" ");
  }
</script>

<div class="bg-slate-50 min-h-screen">
  <div class="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">Selamat datang 👋</h1>
        <p class="text-sm text-slate-500 mt-1">
          Ringkasan data jamaah & grup Anda
        </p>
      </div>
      <button
        type="button"
        onclick={() => onNavigate?.("scanner")}
        class="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white font-medium rounded-xl flex items-center gap-2 transition-colors shadow-sm"
      >
        <ScanLine class="w-4 h-4" />
        Scan Dokumen
      </button>
    </div>

    {#if isLoading}
      <div class="flex items-center justify-center py-20 text-slate-400">
        <Loader2 class="w-6 h-6 animate-spin mr-2" /> Memuat statistik...
      </div>
    {:else if error}
      <div
        class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm"
      >
        {error}
      </div>
    {:else if stats}
      <!-- Stat Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-6">
        <!-- Total Groups -->
        <div
          class="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-3 mb-2">
            <div
              class="w-9 h-9 bg-blue-50 rounded-xl flex items-center justify-center"
            >
              <FolderOpen class="w-4.5 h-4.5 text-blue-500" />
            </div>
          </div>
          <div class="text-2xl font-bold text-slate-800">
            {stats.total_groups}
          </div>
          <div class="text-xs text-slate-500 mt-0.5">
            Total Grup
            {#if stats.groups_this_month > 0}
              <span class="text-emerald-500 font-medium"
                >+{stats.groups_this_month} bulan ini</span
              >
            {/if}
          </div>
        </div>

        <!-- Total Jamaah -->
        <div
          class="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-3 mb-2">
            <div
              class="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center"
            >
              <Users class="w-4.5 h-4.5 text-emerald-500" />
            </div>
          </div>
          <div class="text-2xl font-bold text-slate-800">
            {stats.total_jamaah}
          </div>
          <div class="text-xs text-slate-500 mt-0.5">
            Total Jamaah
            {#if stats.jamaah_this_month > 0}
              <span class="text-emerald-500 font-medium"
                >+{stats.jamaah_this_month} bulan ini</span
              >
            {/if}
          </div>
        </div>

        <!-- Equipment Rate -->
        <div
          class="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-3 mb-2">
            <div
              class="w-9 h-9 bg-amber-50 rounded-xl flex items-center justify-center"
            >
              <Shield class="w-4.5 h-4.5 text-amber-500" />
            </div>
          </div>
          <div class="text-2xl font-bold text-slate-800">
            {stats.equipment_rate}%
          </div>
          <div class="text-xs text-slate-500 mt-0.5">
            Perlengkapan Terpenuhi
          </div>
        </div>

        <!-- Passport Expiry -->
        <div
          class="bg-white rounded-2xl border border-slate-200 p-4 sm:p-5 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center gap-3 mb-2">
            <div
              class="w-9 h-9 rounded-xl flex items-center justify-center {stats.passport_expiring_soon >
              0
                ? 'bg-red-50'
                : 'bg-slate-50'}"
            >
              <AlertTriangle
                class="w-4.5 h-4.5 {stats.passport_expiring_soon > 0
                  ? 'text-red-500'
                  : 'text-slate-400'}"
              />
            </div>
          </div>
          <div
            class="text-2xl font-bold {stats.passport_expiring_soon > 0
              ? 'text-red-600'
              : 'text-slate-800'}"
          >
            {stats.passport_expiring_soon}
          </div>
          <div class="text-xs text-slate-500 mt-0.5">Paspor Segera Habis</div>
        </div>
      </div>

      <!-- Second Row: Trend + Gender + Recent -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <!-- Monthly Trend -->
        <div
          class="bg-white rounded-2xl border border-slate-200 p-5 lg:col-span-2"
        >
          <h3
            class="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-4"
          >
            <TrendingUp class="w-4 h-4 text-emerald-500" />
            Tren Jamaah (6 Bulan)
          </h3>
          {#if stats.monthly_trend.length >= 2}
            <div class="relative h-24 w-full">
              <svg
                viewBox="0 0 200 50"
                class="w-full h-full"
                preserveAspectRatio="none"
              >
                <!-- Area fill -->
                <path
                  d="{sparklinePath(stats.monthly_trend)} L 200 50 L 0 50 Z"
                  fill="url(#gradient)"
                  opacity="0.15"
                />
                <!-- Line -->
                <path
                  d={sparklinePath(stats.monthly_trend)}
                  fill="none"
                  stroke="#10b981"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <defs>
                  <linearGradient id="gradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stop-color="#10b981" />
                    <stop offset="100%" stop-color="#10b981" stop-opacity="0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="flex justify-between mt-2">
              {#each stats.monthly_trend as m}
                <div class="text-center">
                  <div class="text-[10px] text-slate-400">{m.label}</div>
                  <div class="text-xs font-semibold text-slate-600">
                    {m.count}
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="text-sm text-slate-400 text-center py-8">
              Belum cukup data untuk menampilkan tren
            </div>
          {/if}
        </div>

        <!-- Gender Breakdown -->
        <div class="bg-white rounded-2xl border border-slate-200 p-5">
          <h3
            class="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-4"
          >
            <BarChart3 class="w-4 h-4 text-blue-500" />
            Komposisi Gender
          </h3>
          {#if stats.gender_breakdown.male + stats.gender_breakdown.female + stats.gender_breakdown.unknown > 0}
            {@const total =
              stats.gender_breakdown.male +
              stats.gender_breakdown.female +
              stats.gender_breakdown.unknown}
            <div class="space-y-3">
              <!-- Male -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-slate-600">👨 Laki-laki</span>
                  <span class="font-medium text-slate-700"
                    >{stats.gender_breakdown.male}</span
                  >
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-blue-400 rounded-full transition-all"
                    style="width: {(stats.gender_breakdown.male / total) *
                      100}%"
                  ></div>
                </div>
              </div>
              <!-- Female -->
              <div>
                <div class="flex justify-between text-xs mb-1">
                  <span class="text-slate-600">👩 Perempuan</span>
                  <span class="font-medium text-slate-700"
                    >{stats.gender_breakdown.female}</span
                  >
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-pink-400 rounded-full transition-all"
                    style="width: {(stats.gender_breakdown.female / total) *
                      100}%"
                  ></div>
                </div>
              </div>
              <!-- Unknown -->
              {#if stats.gender_breakdown.unknown > 0}
                <div>
                  <div class="flex justify-between text-xs mb-1">
                    <span class="text-slate-600">❓ Belum diisi</span>
                    <span class="font-medium text-slate-700"
                      >{stats.gender_breakdown.unknown}</span
                    >
                  </div>
                  <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-slate-300 rounded-full transition-all"
                      style="width: {(stats.gender_breakdown.unknown / total) *
                        100}%"
                    ></div>
                  </div>
                </div>
              {/if}
            </div>
          {:else}
            <div class="text-sm text-slate-400 text-center py-8">
              Belum ada data
            </div>
          {/if}
        </div>
      </div>

      <!-- Recent Groups -->
      {#if stats.recent_groups.length > 0}
        <div class="bg-white rounded-2xl border border-slate-200 p-5">
          <h3
            class="text-sm font-semibold text-slate-700 flex items-center gap-2 mb-4"
          >
            <CalendarDays class="w-4 h-4 text-violet-500" />
            Grup Terbaru
          </h3>
          <div class="divide-y divide-slate-100">
            {#each stats.recent_groups as group}
              <div
                class="flex items-center justify-between py-3 first:pt-0 last:pb-0"
              >
                <div>
                  <p class="text-sm font-medium text-slate-700">
                    {group.name}
                  </p>
                  <p class="text-xs text-slate-400">
                    {group.member_count} jamaah ·
                    {new Date(group.created_at).toLocaleDateString("id-ID", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </p>
                </div>
                <span
                  class="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded-lg"
                >
                  {group.member_count} 👥
                </span>
              </div>
            {/each}
          </div>
        </div>
      {/if}
    {/if}
  </div>
</div>

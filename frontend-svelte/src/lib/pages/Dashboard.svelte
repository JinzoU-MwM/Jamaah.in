<script>
  import { onMount } from "svelte";
  import {
    AlertTriangle,
    Bell,
    Building2,
    CheckCircle,
    ClipboardCheck,
    FileText,
    Hotel,
    Loader2,
    Package,
    ScanLine,
    Search,
    TrendingUp,
    UserPlus,
    Users,
  } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let { user = null, subscription = null, onNavigate = null } = $props();

  let stats = $state(null);
  let isLoading = $state(true);
  let error = $state("");

  onMount(async () => {
    try {
      stats = await ApiService.getDashboardStats();
    } catch (e) {
      error = e.message;
    } finally {
      isLoading = false;
    }
  });

  let isPro = $derived(subscription?.plan === "pro" && subscription?.status !== "expired");
  let displayName = $derived(user?.name || "Admin Travel");
  let displayEmail = $derived(user?.email || "admin@travel.co.id");
  let initials = $derived(
    displayName
      .split(" ")
      .map((part) => part.charAt(0))
      .join("")
      .slice(0, 2)
      .toUpperCase(),
  );

  let gender = $derived(stats?.gender_breakdown || { male: 0, female: 0, unknown: 0 });
  let genderTotal = $derived(gender.male + gender.female + gender.unknown);
  let malePct = $derived(genderTotal > 0 ? Math.round((gender.male / genderTotal) * 100) : 0);
  let femalePct = $derived(genderTotal > 0 ? Math.round((gender.female / genderTotal) * 100) : 0);
  let unknownPct = $derived(Math.max(0, 100 - malePct - femalePct));
  let genderDonut = $derived(
    `conic-gradient(#2563eb 0 ${malePct}%, #ec4899 ${malePct}% ${malePct + femalePct}%, #cbd5e1 ${malePct + femalePct}% 100%)`,
  );
  let trend = $derived(stats?.monthly_trend || []);
  let trendMax = $derived(Math.max(...trend.map((item) => item.count), 1));

  let statCards = $derived([
    {
      icon: Users,
      label: "Total Jamaah",
      value: stats?.total_jamaah ?? 0,
      badge: stats?.jamaah_this_month > 0 ? `+${stats.jamaah_this_month} bulan ini` : "Live",
      color: "emerald",
      line: "from-emerald-500 to-emerald-400",
    },
    {
      icon: Building2,
      label: "Total Grup Keberangkatan",
      value: stats?.total_groups ?? 0,
      badge: stats?.groups_this_month > 0 ? `+${stats.groups_this_month} bulan ini` : `${stats?.total_groups ?? 0} grup`,
      color: "primary",
      line: "from-primary-500 to-primary-400",
    },
    {
      icon: CheckCircle,
      label: "Perlengkapan Terpenuhi",
      value: `${stats?.equipment_rate ?? 0}%`,
      badge: "Inventory",
      color: "amber",
      line: "from-amber-500 to-amber-400",
    },
    {
      icon: AlertTriangle,
      label: "Paspor Segera Habis",
      value: stats?.passport_expiring_soon ?? 0,
      badge: "90 hari",
      color: (stats?.passport_expiring_soon ?? 0) > 0 ? "red" : "slate",
      line: (stats?.passport_expiring_soon ?? 0) > 0 ? "from-red-500 to-red-400" : "from-slate-400 to-slate-300",
    },
  ]);

  const quickActions = [
    {
      label: "Scan Dokumen",
      desc: "KTP/Paspor -> Excel",
      icon: ScanLine,
      page: "scanner",
      color: "from-primary-500 to-primary-600",
      shadow: "shadow-primary-500/20",
    },
    {
      label: "Auto-Rooming",
      desc: "Alokasi kamar",
      icon: Hotel,
      page: "rooming",
      color: "from-emerald-500 to-emerald-600",
      shadow: "shadow-emerald-500/20",
    },
    {
      label: "Manifest",
      desc: "Akses tim lapangan",
      icon: ClipboardCheck,
      page: "team",
      color: "from-amber-500 to-orange-500",
      shadow: "shadow-amber-500/20",
    },
    {
      label: "Tambah Jamaah",
      desc: "Input atau import",
      icon: UserPlus,
      page: "scanner",
      color: "from-violet-500 to-purple-600",
      shadow: "shadow-violet-500/20",
    },
  ];

  let operationCards = $derived([
    {
      label: "Dokumen selesai",
      value: stats?.total_jamaah ? Math.min(98, Math.max(0, stats.equipment_rate || 0)) : 0,
      icon: FileText,
      color: "primary",
    },
    {
      label: "Rooming siap",
      value: isPro ? 84 : 0,
      icon: Hotel,
      color: "emerald",
    },
    {
      label: "Inventory",
      value: stats?.equipment_rate ?? 0,
      icon: Package,
      color: "amber",
    },
    {
      label: "Manifest lapangan",
      value: isPro ? 76 : 0,
      icon: ClipboardCheck,
      color: "violet",
    },
  ]);

  function formatDate(value) {
    if (!value) return "-";
    return new Date(value).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function iconTone(color) {
    const tones = {
      emerald: "bg-emerald-50 text-emerald-600",
      primary: "bg-primary-50 text-primary-600",
      amber: "bg-amber-50 text-amber-600",
      violet: "bg-violet-50 text-violet-600",
      red: "bg-red-50 text-red-600",
      slate: "bg-slate-50 text-slate-500",
    };
    return tones[color] || tones.slate;
  }

  function badgeTone(color) {
    const tones = {
      emerald: "bg-emerald-50 text-emerald-600",
      primary: "bg-primary-50 text-primary-600",
      amber: "bg-amber-50 text-amber-600",
      violet: "bg-violet-50 text-violet-600",
      red: "bg-red-50 text-red-600",
      slate: "bg-slate-100 text-slate-500",
    };
    return tones[color] || tones.slate;
  }
</script>

<div class="min-h-screen bg-slate-50/70">
  <header class="sticky top-16 z-20 flex min-h-[72px] items-center justify-between gap-4 border-b border-slate-200/80 bg-white/80 px-4 backdrop-blur-xl lg:top-0 lg:px-8">
    <div class="min-w-0">
      <h1 class="text-lg font-bold text-slate-900">Dashboard</h1>
      <p class="hidden text-xs text-slate-400 sm:block">Selamat datang kembali, {displayName}</p>
    </div>

    <div class="flex items-center gap-2 sm:gap-3">
      <label class="relative hidden md:flex">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input type="search" placeholder="Cari jamaah, grup..." class="w-56 rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-4 text-sm outline-none transition-all focus:border-primary-400 lg:w-72" />
      </label>
      <button type="button" class="flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100 md:hidden" aria-label="Cari">
        <Search class="h-5 w-5" />
      </button>
      <button type="button" class="relative flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100" aria-label="Notifikasi">
        <Bell class="h-5 w-5" />
        <span class="badge-pulse absolute right-1.5 top-1.5 h-2.5 w-2.5 rounded-full border-2 border-white bg-red-500"></span>
      </button>
      <div class="hidden h-8 w-px bg-slate-200 sm:block"></div>
      <div class="flex cursor-pointer items-center gap-3 rounded-xl px-2 py-1.5 transition-colors hover:bg-slate-50">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-sm font-bold text-white shadow-lg shadow-primary-500/20">{initials}</div>
        <div class="hidden min-w-0 text-left sm:block">
          <p class="truncate text-sm font-semibold leading-none text-slate-800">{displayName}</p>
          <p class="mt-1 truncate text-[11px] text-slate-400">{displayEmail}</p>
        </div>
      </div>
    </div>
  </header>

  <div class="space-y-6 p-4 lg:p-8">
    <div class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
      <div class="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <p class="text-xs font-bold uppercase tracking-wider text-primary-600">Ringkasan Operasional</p>
          <h2 class="mt-1 text-xl font-extrabold text-slate-900">Pantau semua progres jamaah hari ini.</h2>
          <p class="mt-1 text-sm text-slate-500">Data jamaah, grup, dokumen, dan kesiapan lapangan dalam satu dashboard.</p>
        </div>
        <span class="w-fit rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold uppercase text-emerald-700">{isPro ? "Pro Active" : "Starter"}</span>
      </div>
    </div>
    {#if isLoading}
      <div class="flex min-h-[360px] items-center justify-center rounded-3xl border border-slate-200 bg-white text-slate-400 shadow-sm">
        <Loader2 class="mr-2 h-6 w-6 animate-spin" /> Memuat statistik...
      </div>
    {:else if error}
      <div class="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">{error}</div>
    {:else if stats}
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-4 lg:gap-4">
        {#each quickActions as action}
          {@const ActionIcon = action.icon}
          <button type="button" onclick={() => onNavigate?.(action.page)} class="quick-action flex min-h-[92px] items-center gap-3 rounded-2xl border border-slate-100 bg-white p-4 text-left shadow-sm">
            <div class={`flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${action.color} shadow-lg ${action.shadow}`}>
              <ActionIcon class="h-5 w-5 text-white" />
            </div>
            <div class="min-w-0">
              <p class="truncate text-sm font-bold text-slate-800">{action.label}</p>
              <p class="truncate text-[11px] text-slate-400">{action.desc}</p>
            </div>
          </button>
        {/each}
      </div>

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-5">
        {#each statCards as card}
          {@const CardIcon = card.icon}
          <div class={`relative overflow-hidden rounded-2xl border border-slate-100 bg-white p-5 shadow-sm before:absolute before:left-0 before:right-0 before:top-0 before:h-[3px] before:bg-gradient-to-r before:${card.line}`}>
            <div class="mb-3 flex items-center justify-between">
              <div class={`flex h-11 w-11 items-center justify-center rounded-xl ${iconTone(card.color)}`}>
                <CardIcon class="h-6 w-6" />
              </div>
              <span class={`rounded-full px-2 py-0.5 text-xs font-semibold ${badgeTone(card.color)}`}>{card.badge}</span>
            </div>
            <p class="text-2xl font-extrabold text-slate-900">{card.value}</p>
            <p class="mt-0.5 text-xs text-slate-400">{card.label}</p>
          </div>
        {/each}
      </div>

      {#if stats.passport_expiring_soon > 0}
        <div class="flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-900 sm:flex-row sm:items-center sm:justify-between">
          <div class="flex items-start gap-3">
            <AlertTriangle class="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-600" />
            <div>
              <p class="text-sm font-bold">{stats.passport_expiring_soon} paspor perlu dicek sebelum 90 hari.</p>
              <p class="text-xs text-amber-700">Prioritaskan verifikasi dokumen sebelum export final atau keberangkatan.</p>
            </div>
          </div>
          <button type="button" onclick={() => onNavigate?.("scanner")} class="rounded-xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-amber-700">Cek Dokumen</button>
        </div>
      {/if}

      <div class="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-2">
          <div class="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 class="text-base font-bold text-slate-900">Tren Pendaftaran</h2>
              <p class="mt-0.5 text-xs text-slate-400">6 bulan terakhir</p>
            </div>
            <span class="inline-flex items-center gap-1 rounded-full bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-600"><TrendingUp class="h-3.5 w-3.5" /> Live</span>
          </div>

          {#if trend.length >= 2}
            <div class="flex h-64 items-end gap-3 rounded-2xl bg-slate-50 p-4">
              {#each trend as item}
                <div class="flex h-full min-w-0 flex-1 flex-col justify-end gap-2">
                  <div class="relative flex flex-1 items-end">
                    <div class="w-full rounded-t-xl bg-gradient-to-t from-primary-600 to-primary-400 shadow-lg shadow-primary-500/10" style:height={`${Math.max(8, Math.round((item.count / trendMax) * 100))}%`}></div>
                  </div>
                  <div class="text-center">
                    <p class="truncate text-[10px] font-medium text-slate-400">{item.label}</p>
                    <p class="text-xs font-bold text-slate-700">{item.count}</p>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <div class="flex h-64 items-center justify-center rounded-2xl bg-slate-50 text-sm text-slate-400">Belum cukup data untuk menampilkan tren.</div>
          {/if}
        </section>

        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <div class="mb-5">
            <h2 class="text-base font-bold text-slate-900">Komposisi Gender</h2>
            <p class="mt-0.5 text-xs text-slate-400">Distribusi jamaah</p>
          </div>

          <div class="flex flex-col items-center">
            <div class="relative flex h-44 w-44 items-center justify-center rounded-full" style:background={genderDonut}>
              <div class="flex h-28 w-28 flex-col items-center justify-center rounded-full bg-white shadow-inner">
                <p class="text-2xl font-extrabold text-slate-900">{genderTotal}</p>
                <p class="text-[10px] text-slate-400">Total</p>
              </div>
            </div>

            <div class="mt-5 w-full space-y-3">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-primary-500"></span><span class="text-sm text-slate-600">Laki-laki</span></div>
                <span class="text-sm font-bold text-slate-800">{gender.male} <span class="font-medium text-slate-400">({malePct}%)</span></span>
              </div>
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-pink-500"></span><span class="text-sm text-slate-600">Perempuan</span></div>
                <span class="text-sm font-bold text-slate-800">{gender.female} <span class="font-medium text-slate-400">({femalePct}%)</span></span>
              </div>
              {#if gender.unknown > 0}
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2"><span class="h-3 w-3 rounded-full bg-slate-300"></span><span class="text-sm text-slate-600">Belum diisi</span></div>
                  <span class="text-sm font-bold text-slate-800">{gender.unknown} <span class="font-medium text-slate-400">({unknownPct}%)</span></span>
                </div>
              {/if}
            </div>
          </div>
        </section>
      </div>

      <div class="grid grid-cols-1 gap-5 xl:grid-cols-3">
        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm xl:col-span-2">
          <div class="mb-5 flex items-center justify-between">
            <div>
              <h2 class="text-base font-bold text-slate-900">Kesiapan Operasional</h2>
              <p class="mt-0.5 text-xs text-slate-400">Ringkasan modul utama dari referensi dashboard.</p>
            </div>
          </div>
          <div class="grid gap-4 sm:grid-cols-2">
            {#each operationCards as item}
              {@const OperationIcon = item.icon}
              <div class="rounded-2xl border border-slate-100 bg-slate-50/70 p-4">
                <div class="mb-3 flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <div class={`flex h-9 w-9 items-center justify-center rounded-xl ${iconTone(item.color)}`}><OperationIcon class="h-4.5 w-4.5" /></div>
                    <p class="text-sm font-bold text-slate-800">{item.label}</p>
                  </div>
                  <span class={`rounded-full px-2 py-0.5 text-xs font-semibold ${badgeTone(item.color)}`}>{item.value}%</span>
                </div>
                <div class="h-2 overflow-hidden rounded-full bg-white">
                  <div class={`h-full rounded-full bg-gradient-to-r ${item.color === "primary" ? "from-primary-500 to-primary-400" : item.color === "emerald" ? "from-emerald-500 to-emerald-400" : item.color === "amber" ? "from-amber-500 to-amber-400" : "from-violet-500 to-violet-400"}`} style:width={`${item.value}%`}></div>
                </div>
              </div>
            {/each}
          </div>
        </section>

        <section class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <h2 class="text-base font-bold text-slate-900">Grup Terbaru</h2>
              <p class="mt-0.5 text-xs text-slate-400">Aktivitas terakhir</p>
            </div>
            <Building2 class="h-5 w-5 text-slate-300" />
          </div>
          {#if stats.recent_groups?.length > 0}
            <div class="divide-y divide-slate-100">
              {#each stats.recent_groups as group}
                <div class="flex items-center justify-between gap-3 py-3 first:pt-0 last:pb-0">
                  <div class="min-w-0">
                    <p class="truncate text-sm font-semibold text-slate-700">{group.name}</p>
                    <p class="text-xs text-slate-400">{formatDate(group.created_at)}</p>
                  </div>
                  <span class="rounded-lg bg-primary-50 px-2 py-1 text-xs font-semibold text-primary-600">{group.member_count} jamaah</span>
                </div>
              {/each}
            </div>
          {:else}
            <div class="rounded-2xl bg-slate-50 p-6 text-center text-sm text-slate-400">Belum ada grup keberangkatan.</div>
          {/if}
        </section>
      </div>
    {/if}
  </div>
</div>

<style>
  .quick-action {
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .quick-action:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px -8px rgba(15, 23, 42, 0.16);
  }

  .badge-pulse {
    animation: pulse-ring 2s infinite;
  }

  @keyframes pulse-ring {
    0% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
    }
    70% {
      box-shadow: 0 0 0 6px rgba(239, 68, 68, 0);
    }
    100% {
      box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
    }
  }
</style>

<script>
  import { onMount } from "svelte";
  import { CalendarDays, Plane, Hotel, Users, ArrowRight, Loader2, AlertCircle } from "lucide-svelte";
  import BrandLogo from "../components/BrandLogo.svelte";
  import { ApiService } from "../services/api";

  let { slug } = $props();

  let loading = $state(true);
  let error = $state("");
  let pkg = $state(null);
  let registrationHref = $derived(buildRegistrationHref(pkg));

  onMount(async () => {
    try {
      const response = await ApiService.getPublicPackage(slug);
      pkg = response.data ?? response;
    } catch (e) {
      error = e.message || "Paket tidak ditemukan";
    } finally {
      loading = false;
    }
  });

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }

  function formatIDR(value) {
    return new Intl.NumberFormat("id-ID", {
      style: "currency",
      currency: "IDR",
      minimumFractionDigits: 0,
    }).format(value || 0);
  }

  function roomLabel(roomType) {
    switch (roomType) {
      case "quad":
        return "Quad";
      case "triple":
        return "Triple";
      case "double":
        return "Double";
      case "single":
        return "Single";
      default:
        return roomType;
    }
  }

  function buildRegistrationHref(currentPackage) {
    if (!currentPackage) return "#";
    const messageLines = [
      `Halo, saya tertarik mendaftar paket ${currentPackage.name}.`,
      currentPackage.departure_date ? `Keberangkatan: ${formatDate(currentPackage.departure_date)}` : null,
      typeof window !== "undefined" ? `Link paket: ${window.location.href}` : null,
    ].filter(Boolean);
    return `https://wa.me/?text=${encodeURIComponent(messageLines.join("\n"))}`;
  }
</script>

<div class="min-h-screen bg-[linear-gradient(180deg,#f7efe0_0%,#fffaf2_42%,#ffffff_100%)] text-slate-900">
  <div class="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="mb-8 flex items-center justify-between">
      <BrandLogo size="small" />
      <a href="/#/" class="text-sm font-semibold text-slate-500 transition-colors hover:text-slate-800">Kembali</a>
    </div>

    {#if loading}
      <div class="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 class="h-8 w-8 animate-spin" />
        <p>Memuat paket...</p>
      </div>
    {:else if error || !pkg}
      <div class="flex min-h-[50vh] flex-col items-center justify-center gap-3 rounded-3xl border border-red-100 bg-white p-10 text-center shadow-sm">
        <AlertCircle class="h-10 w-10 text-red-500" />
        <h1 class="text-xl font-bold">Paket tidak tersedia</h1>
        <p class="max-w-md text-sm text-slate-500">{error || "Link paket tidak valid atau sudah tidak aktif."}</p>
      </div>
    {:else}
      <section class="overflow-hidden rounded-[32px] border border-amber-100 bg-white shadow-[0_30px_80px_-40px_rgba(120,53,15,0.35)]">
        <div class="relative overflow-hidden border-b border-amber-100 bg-[radial-gradient(circle_at_top_left,#fde68a_0%,#f59e0b_32%,#78350f_100%)] px-6 py-10 text-white sm:px-10">
          <div class="absolute -right-16 top-0 h-40 w-40 rounded-full bg-white/10 blur-2xl"></div>
          <div class="absolute bottom-0 left-0 h-24 w-24 rounded-full bg-black/10 blur-2xl"></div>
          <div class="relative max-w-3xl">
            <p class="mb-3 text-xs font-bold uppercase tracking-[0.3em] text-amber-100">Paket Umrah</p>
            <h1 class="text-3xl font-black leading-tight sm:text-5xl">{pkg.name}</h1>
            {#if pkg.description}
              <p class="mt-4 max-w-2xl text-sm leading-relaxed text-amber-50 sm:text-base">{pkg.description}</p>
            {/if}
            <div class="mt-6 flex flex-wrap gap-3 text-sm">
              <span class="rounded-full bg-white/15 px-4 py-2 backdrop-blur">{formatDate(pkg.departure_date)} - {formatDate(pkg.return_date)}</span>
              <span class="rounded-full bg-white/15 px-4 py-2 backdrop-blur">{pkg.available_seats} kursi tersedia</span>
            </div>
          </div>
        </div>

        <div class="grid gap-8 px-6 py-8 sm:px-10 lg:grid-cols-[1.15fr_0.85fr]">
          <div class="space-y-6">
            <div class="grid gap-4 sm:grid-cols-3">
              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div class="mb-2 flex items-center gap-2 text-slate-500">
                  <CalendarDays class="h-4 w-4" />
                  <span class="text-xs font-bold uppercase tracking-wider">Tanggal</span>
                </div>
                <p class="text-sm font-semibold text-slate-900">{formatDate(pkg.departure_date)}</p>
                <p class="text-sm text-slate-500">{formatDate(pkg.return_date)}</p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div class="mb-2 flex items-center gap-2 text-slate-500">
                  <Plane class="h-4 w-4" />
                  <span class="text-xs font-bold uppercase tracking-wider">Maskapai</span>
                </div>
                <p class="text-sm font-semibold text-slate-900">{pkg.airline || "-"}</p>
                <p class="text-sm text-slate-500">{pkg.flight_number_go || "-"}</p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                <div class="mb-2 flex items-center gap-2 text-slate-500">
                  <Users class="h-4 w-4" />
                  <span class="text-xs font-bold uppercase tracking-wider">Kursi</span>
                </div>
                <p class="text-sm font-semibold text-slate-900">{pkg.available_seats} tersedia</p>
                <p class="text-sm text-slate-500">{pkg.reserved_seats}/{pkg.total_seats} terisi</p>
              </div>
            </div>

            <div class="rounded-3xl border border-slate-200 p-6">
              <div class="mb-5 flex items-center gap-2">
                <Hotel class="h-5 w-5 text-amber-600" />
                <h2 class="text-lg font-bold">Akomodasi</h2>
              </div>
              <div class="grid gap-4 sm:grid-cols-2">
                <div class="rounded-2xl bg-slate-50 p-4">
                  <p class="text-xs font-bold uppercase tracking-wider text-slate-400">Hotel Makkah</p>
                  <p class="mt-2 text-sm font-semibold text-slate-900">{pkg.hotel_makkah_name || "-"}</p>
                </div>
                <div class="rounded-2xl bg-slate-50 p-4">
                  <p class="text-xs font-bold uppercase tracking-wider text-slate-400">Hotel Madinah</p>
                  <p class="mt-2 text-sm font-semibold text-slate-900">{pkg.hotel_madinah_name || "-"}</p>
                </div>
              </div>
            </div>
          </div>

          <aside class="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            <h2 class="text-lg font-bold">Harga per Tipe Kamar</h2>
            {#if (pkg.pricing_tiers || []).length > 0}
              <div class="mt-5 space-y-3">
                {#each pkg.pricing_tiers || [] as tier}
                  <div class="flex items-center justify-between rounded-2xl bg-white px-4 py-3 shadow-sm">
                    <div>
                      <p class="text-sm font-semibold text-slate-900">{roomLabel(tier.room_type)}</p>
                      {#if tier.label}
                        <p class="text-xs text-slate-500">{tier.label}</p>
                      {/if}
                    </div>
                    <p class="text-sm font-bold text-amber-700">{formatIDR(tier.price)}</p>
                  </div>
                {/each}
              </div>
            {:else}
              <p class="mt-4 text-sm text-slate-500">Harga belum tersedia.</p>
            {/if}

            <a
              href={registrationHref}
              target="_blank"
              rel="noreferrer"
              class="mt-6 flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-4 text-sm font-bold text-white transition-colors hover:bg-slate-700"
            >
              Hubungi Travel untuk Daftar
              <ArrowRight class="h-4 w-4" />
            </a>
            <p class="mt-3 text-xs leading-relaxed text-slate-500">
              Tombol ini membuka template pesan WhatsApp agar calon jamaah bisa langsung menghubungi travel terkait paket ini.
            </p>
          </aside>
        </div>
      </section>
    {/if}
  </div>
</div>

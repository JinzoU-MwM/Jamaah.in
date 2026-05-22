<script lang="ts">
  import {
    ArrowRight,
    BarChart3,
    BookOpen,
    Briefcase,
    Building2,
    Check,
    ChevronDown,
    ChevronRight,
    ClipboardList,
    DollarSign,
    FileText,
    Instagram,
    Menu,
    MessageCircle,
    Package,
    Receipt,
    Rocket,
    ScanLine,
    Shield,
    Sparkles,
    Star,
    TrendingUp,
    Users,
    Wallet,
    X,
    Youtube,
    Zap,
    AlertCircle,
    Clock,
    PieChart,
  } from "lucide-svelte";
  import BrandLogo from "../components/BrandLogo.svelte";

  interface Props {
    onGoToLogin?: () => void;
    onGoToRegister?: () => void;
  }

  let { onGoToLogin = () => {}, onGoToRegister = () => {} }: Props = $props();

  let mobileMenuOpen = $state(false);
  let openFaq = $state(-1);

  const navItems = [
    { href: "#masalah", label: "Masalah" },
    { href: "#fitur", label: "Fitur" },
    { href: "#harga", label: "Harga" },
    { href: "#faq", label: "FAQ" },
  ];

  const painPoints = [
    {
      icon: Receipt,
      color: "text-red-500",
      bg: "bg-red-50",
      title: "Piutang tidak terpantau",
      desc: "Owner baru tahu jamaah belum lunas saat H-7 keberangkatan. Tidak ada sistem yang mengingatkan secara otomatis.",
    },
    {
      icon: PieChart,
      color: "text-orange-500",
      bg: "bg-orange-50",
      title: "Profit trip tidak terlihat",
      desc: "P&L dihitung manual di Excel setelah trip selesai — padahal keputusan bisnis butuh data real-time.",
    },
    {
      icon: Building2,
      color: "text-amber-500",
      bg: "bg-amber-50",
      title: "Pengeluaran vendor tidak tercatat",
      desc: "Bayar hotel, maskapai, dan katering tapi tidak ada catatan sistematis. HPP trip jadi estimasi, bukan angka nyata.",
    },
    {
      icon: DollarSign,
      color: "text-emerald-500",
      bg: "bg-emerald-50",
      title: "Komisi agen dihitung manual",
      desc: "Jaringan sub-agen yang aktif mendatangkan jamaah tapi komisinya dihitung di kertas dan sering terlambat dibayar.",
    },
    {
      icon: Users,
      color: "text-blue-500",
      bg: "bg-blue-50",
      title: "Database jamaah tercecer",
      desc: "Tidak tahu siapa yang sudah umroh dan berpotensi repeat order. Data tersebar di Excel lama dan chat WhatsApp.",
    },
    {
      icon: Package,
      color: "text-violet-500",
      bg: "bg-violet-50",
      title: "Paket dikelola di WhatsApp",
      desc: "Harga, kuota, dan detail paket diinformasikan ulang setiap kali ada yang tanya — tidak ada single source of truth.",
    },
  ];

  const modules = [
    {
      icon: Package,
      color: "from-primary-500 to-primary-600",
      shadow: "shadow-primary-500/20",
      title: "Paket & Harga",
      desc: "Buat paket umroh & haji dengan harga bertingkat per tipe kamar, komponen biaya untuk HPP, dan halaman publik shareable.",
      badge: null,
    },
    {
      icon: Users,
      color: "from-emerald-500 to-emerald-600",
      shadow: "shadow-emerald-500/20",
      title: "CRM & Pipeline",
      desc: "Lacak perjalanan jamaah dari Prospek → Survey → Booking → DP → Lunas → Berangkat dengan notifikasi otomatis.",
      badge: null,
    },
    {
      icon: Receipt,
      color: "from-amber-500 to-orange-500",
      shadow: "shadow-amber-500/20",
      title: "Invoice & Pembayaran",
      desc: "Generate invoice otomatis, skema cicilan fleksibel, rekam pembayaran, dan cetak kwitansi PDF dalam hitungan detik.",
      badge: "Kunci",
    },
    {
      icon: TrendingUp,
      color: "from-rose-500 to-pink-600",
      shadow: "shadow-rose-500/20",
      title: "Laporan Keuangan",
      desc: "P&L per trip real-time, piutang aging, arus kas proyeksi, dan dashboard owner dengan gross profit & total piutang.",
      badge: "Kunci",
    },
    {
      icon: Building2,
      color: "from-violet-500 to-purple-600",
      shadow: "shadow-violet-500/20",
      title: "Vendor & Biaya Ops",
      desc: "Catat tagihan hotel, maskapai, bus, dan vendor lain. Pantau hutang vendor dan status pembayaran per trip.",
      badge: null,
    },
    {
      icon: DollarSign,
      color: "from-cyan-500 to-blue-600",
      shadow: "shadow-cyan-500/20",
      title: "Komisi Agen",
      desc: "Hitung komisi sub-agen otomatis berdasarkan trigger status jamaah. Rekap per agen, per periode, dengan portal agen.",
      badge: null,
    },
    {
      icon: ScanLine,
      color: "from-teal-500 to-emerald-600",
      shadow: "shadow-teal-500/20",
      title: "AI Scanner",
      desc: "Scan KTP, KK, paspor, dan visa — data langsung masuk ke profil jamaah. Export Siskopatuh 32 kolom tetap tersedia.",
      badge: "AI",
    },
    {
      icon: ClipboardList,
      color: "from-slate-500 to-slate-700",
      shadow: "shadow-slate-500/20",
      title: "Dokumen & Paspor",
      desc: "Checklist dokumen per jamaah per trip. Alert paspor expired 90 dan 30 hari. Upload & simpan dokumen digital.",
      badge: null,
    },
    {
      icon: FileText,
      color: "from-indigo-500 to-blue-600",
      shadow: "shadow-indigo-500/20",
      title: "E-Kontrak Digital",
      desc: "Template kontrak dengan variabel otomatis. Jamaah tanda tangan digital di HP tanpa install app. PDF immutable tersimpan.",
      badge: null,
    },
    {
      icon: BarChart3,
      color: "from-orange-500 to-red-500",
      shadow: "shadow-orange-500/20",
      title: "Pembatalan & Refund",
      desc: "Workflow pembatalan transparan dengan kalkulasi potongan otomatis, approval owner, dan jurnal keuangan otomatis.",
      badge: null,
    },
    {
      icon: Briefcase,
      color: "from-lime-500 to-green-600",
      shadow: "shadow-lime-500/20",
      title: "Persediaan",
      desc: "Kelola stok koper, ihram, mukena, dan seragam. Proyeksi kebutuhan otomatis per trip. Distribusi dengan stock out real-time.",
      badge: null,
    },
    {
      icon: Wallet,
      color: "from-fuchsia-500 to-pink-600",
      shadow: "shadow-fuchsia-500/20",
      title: "Penggajian",
      desc: "Slip gaji karyawan tetap + honor muthawwif per trip. PPh 21, BPJS, kasbon, dan rekap transfer bank.",
      badge: null,
    },
  ];

  const compVsExcel = [
    { bad: "Piutang jamaah belum lunas baru ketahuan H-7", good: "Alert otomatis 30, 14, dan 7 hari sebelum jatuh tempo" },
    { bad: "P&L trip dihitung manual setelah selesai", good: "P&L real-time sejak hari pertama pendaftaran jamaah" },
    { bad: "Data jamaah tersebar di banyak file Excel", good: "Satu database terpusat, bisa dicari dan difilter kapan saja" },
    { bad: "Hitung komisi agen manual dan sering salah", good: "Komisi dihitung otomatis saat jamaah lunas — nol error" },
    { bad: "Multi-user overwrite data satu sama lain", good: "Role-based access: owner, admin, finance, CS — aman" },
    { bad: "Tidak ada audit trail siapa yang ubah data", good: "Setiap perubahan tercatat: siapa, kapan, apa yang diubah" },
  ];

  const compVsAccounting = [
    { aspect: "Setup", accounting: "Perlu kustomisasi chart of accounts", jamaah: "Langsung pakai, sudah terkonfigurasi untuk travel" },
    { aspect: "Paket umroh", accounting: "Tidak ada konsep paket trip", jamaah: "Native: paket, kuota, tanggal keberangkatan" },
    { aspect: "Skema cicilan", accounting: "Manual tanpa validasi total", jamaah: "DP + pelunasan / cicilan bebas dengan validasi" },
    { aspect: "Komisi agen", accounting: "Manual", jamaah: "Otomatis berdasarkan trigger status jamaah" },
    { aspect: "Dokumen paspor", accounting: "Tidak ada", jamaah: "Checklist per jamaah + alert expired" },
    { aspect: "AI Scanner", accounting: "Tidak ada", jamaah: "Ekstrak 32+ field dari foto dokumen" },
    { aspect: "Export Siskopatuh", accounting: "Tidak ada", jamaah: "Built-in, satu klik" },
  ];

  const stats = [
    { value: "2.200+", label: "PPIU terdaftar di Indonesia" },
    { value: "12", label: "Modul terintegrasi" },
    { value: "< 2 mnt", label: "Buat invoice jamaah" },
    { value: "95%+", label: "Akurasi AI Scanner" },
  ];

  const plans = [
    {
      name: "Free Trial",
      price: "Gratis",
      period: "14 hari",
      note: "Semua fitur Pro, tanpa kartu kredit",
      cta: "Mulai Trial 14 Hari",
      featured: false,
      badge: null,
      items: ["Semua fitur Pro selama 14 hari", "Setup < 30 menit", "Tanpa kartu kredit"],
      muted: [],
    },
    {
      name: "Starter",
      price: "Rp 149.000",
      period: "/bulan",
      note: "Untuk travel kecil dengan 1-2 user",
      cta: "Pilih Starter",
      featured: false,
      badge: null,
      items: [
        "Paket & Harga (maks 3 paket aktif)",
        "CRM & Pipeline Jamaah",
        "Invoice & Pembayaran",
        "Dokumen & Checklist Paspor",
        "Maks 2 user",
      ],
      muted: ["Laporan Keuangan & P&L", "Vendor & Komisi Agen"],
    },
    {
      name: "Pro",
      price: "Rp 299.000",
      period: "/bulan",
      note: "Untuk travel menengah aktif",
      cta: "Coba Pro 14 Hari Gratis",
      featured: true,
      badge: "Paling Populer",
      items: [
        "Semua modul kecuali Payroll",
        "Unlimited paket aktif",
        "Laporan P&L per trip",
        "Vendor & Biaya Operasional",
        "Komisi Agen otomatis",
        "AI Scanner unlimited",
        "E-Kontrak Digital",
        "Maks 5 user",
      ],
      muted: [],
    },
    {
      name: "Business",
      price: "Rp 599.000",
      period: "/bulan",
      note: "Untuk travel besar & multi-cabang",
      cta: "Pilih Business",
      featured: false,
      badge: "Lengkap",
      items: [
        "Semua 12 modul",
        "Penggajian & Payroll",
        "Portal Agen",
        "Multi-branch (segera)",
        "Unlimited user",
        "Priority support",
      ],
      muted: [],
    },
  ];

  const faqs = [
    {
      q: "Apakah ini cocok untuk travel kecil yang baru mulai?",
      a: "Ya. Paket Starter dirancang untuk travel dengan 1-2 staff dan 1-3 trip per tahun. Anda bisa mulai dari modul paling dasar (Paket, CRM, Invoice) dan upgrade seiring bisnis berkembang. Trial 14 hari memungkinkan Anda coba semua fitur dulu tanpa risiko.",
    },
    {
      q: "Bagaimana Jamaah.in berbeda dari Jurnal atau Accurate?",
      a: "Software akuntansi umum tidak mengerti konsep paket umroh, skema DP + cicilan per musim haji, komisi jaringan sub-agen, atau checklist kelengkapan paspor & visa. Jamaah.in dirancang dari awal untuk konteks PPIU Indonesia — Anda tidak perlu setup apapun, langsung bisa pakai.",
    },
    {
      q: "Apakah AI Scanner masih bisa export ke Excel Siskopatuh?",
      a: "Ya, export 32 kolom Siskopatuh tetap tersedia di v2. Bedanya sekarang hasil scan langsung masuk ke profil jamaah di CRM, bukan hanya ke Excel. Jika jamaah sudah ada di database (NIK / nomor paspor sama), data di-merge — tidak duplikasi.",
    },
    {
      q: "Bagaimana keamanan data jamaah?",
      a: "Data disimpan di server dedicated self-hosted dengan backup harian terenkripsi ke Google Drive via rclone crypt. PostgreSQL tidak exposed ke internet. Setiap aksi tercatat di audit log. SSL end-to-end untuk semua komunikasi.",
    },
    {
      q: "Bisa pakai banyak user dengan role berbeda?",
      a: "Ya. Owner mendapat full access termasuk laporan keuangan sensitif. Admin bisa kelola jamaah dan invoice tapi tidak bisa hapus data penting. Finance fokus di modul pembayaran. CS/Marketing hanya akses pipeline jamaah. Viewer read-only.",
    },
    {
      q: "Bisa batalkan atau downgrade langganan kapan saja?",
      a: "Bisa. Setelah pembatalan, akses tetap berjalan hingga akhir periode billing yang sudah dibayar. Data Anda tidak langsung dihapus — ada masa retensi 30 hari untuk export jika diperlukan.",
    },
  ];

  function closeMobileMenu() {
    mobileMenuOpen = false;
  }
</script>

<div class="landing">
  <!-- NAV -->
  <header class="fixed inset-x-0 top-0 z-50 border-b border-slate-200/70 bg-white/90 backdrop-blur-xl">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="flex h-16 items-center justify-between lg:h-20">
        <a href="/" class="flex items-center" aria-label="Jamaah.in home">
          <BrandLogo size="small" />
        </a>

        <nav class="hidden items-center gap-8 md:flex" aria-label="Navigasi utama">
          {#each navItems as item}
            <a href={item.href} class="text-sm font-semibold text-slate-600 transition-colors hover:text-primary-600">{item.label}</a>
          {/each}
        </nav>

        <div class="hidden items-center gap-3 md:flex">
          <button type="button" onclick={onGoToLogin} class="px-4 py-2 text-sm font-semibold text-slate-600 transition-colors hover:text-primary-600">Masuk</button>
          <button type="button" onclick={onGoToRegister} class="rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-primary-500/25 transition-all hover:-translate-y-0.5 hover:from-primary-700 hover:to-primary-600">
            Coba 14 Hari Gratis
          </button>
        </div>

        <button type="button" class="rounded-xl p-2 text-slate-600 hover:bg-slate-100 md:hidden" aria-label="Buka menu" onclick={() => (mobileMenuOpen = !mobileMenuOpen)}>
          {#if mobileMenuOpen}<X class="h-5 w-5" />{:else}<Menu class="h-5 w-5" />{/if}
        </button>
      </div>

      {#if mobileMenuOpen}
        <div class="border-t border-slate-100 py-4 md:hidden">
          <nav class="grid gap-2" aria-label="Navigasi mobile">
            {#each navItems as item}
              <a href={item.href} onclick={closeMobileMenu} class="rounded-xl px-3 py-2 text-sm font-semibold text-slate-600 hover:bg-slate-50">{item.label}</a>
            {/each}
          </nav>
          <div class="mt-4 grid grid-cols-2 gap-3">
            <button type="button" onclick={() => { closeMobileMenu(); onGoToLogin(); }} class="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-semibold text-slate-700">Masuk</button>
            <button type="button" onclick={() => { closeMobileMenu(); onGoToRegister(); }} class="rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white">Coba Gratis</button>
          </div>
        </div>
      {/if}
    </div>
  </header>

  <!-- HERO -->
  <section id="hero" class="animated-gradient hero-pattern relative flex min-h-screen items-center overflow-hidden pt-24">
    <div class="absolute left-10 top-20 h-80 w-80 rounded-full bg-primary-200/25 blur-[90px]"></div>
    <div class="absolute bottom-20 right-10 h-96 w-96 rounded-full bg-emerald-200/20 blur-[110px]"></div>

    <!-- Floating cards -->
    <div class="absolute right-16 top-28 z-10 hidden animate-float lg:flex">
      <div class="glass-card flex items-center gap-3 rounded-2xl px-4 py-3 shadow-xl shadow-primary-500/8">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-emerald-600">
          <TrendingUp class="h-5 w-5 text-white" />
        </div>
        <div>
          <p class="text-[11px] text-slate-400">Gross Profit — Jun 2026</p>
          <p class="text-sm font-bold text-slate-800">Rp 142.500.000</p>
        </div>
      </div>
    </div>
    <div class="absolute bottom-36 right-24 z-10 hidden animate-float-delay lg:flex">
      <div class="glass-card flex items-center gap-3 rounded-2xl px-4 py-3 shadow-xl shadow-rose-500/8">
        <div class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-rose-500 to-rose-600">
          <AlertCircle class="h-5 w-5 text-white" />
        </div>
        <div>
          <p class="text-[11px] text-slate-400">Piutang jatuh tempo hari ini</p>
          <p class="text-sm font-bold text-slate-800">3 jamaah — Rp 28.750.000</p>
        </div>
      </div>
    </div>
    <div class="absolute left-14 bottom-48 z-10 hidden animate-float lg:flex" style="animation-delay: 3s">
      <div class="glass-card flex items-center gap-3 rounded-2xl px-4 py-3 shadow-xl shadow-emerald-500/8">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-600">
          <ScanLine class="h-5 w-5 text-white" />
        </div>
        <div>
          <p class="text-[11px] text-slate-400">AI Scanner</p>
          <p class="text-sm font-bold text-slate-800">Paspor Ahmad — 4 detik</p>
        </div>
      </div>
    </div>

    <div class="relative mx-auto max-w-5xl px-4 pb-24 pt-8 text-center sm:px-6 lg:px-8">
      <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-primary-100 bg-primary-50 px-4 py-1.5 text-xs font-semibold text-primary-700">
        <Sparkles class="h-3.5 w-3.5" /> v2.1 — Travel Admin System
      </div>
      <h1 class="mb-6 text-4xl font-bold leading-[1.1] tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
        Satu Dashboard untuk<br /><span class="gradient-text">Seluruh Operasional Travel</span><br />Umroh & Haji Anda
      </h1>
      <p class="mx-auto mb-10 max-w-2xl text-lg leading-relaxed text-slate-500">
        Bukan sekadar tools input data — Jamaah.in adalah sistem administrasi bisnis lengkap khusus PPIU Indonesia. Invoice otomatis, P&L per trip real-time, CRM jamaah, dan 12 modul terintegrasi dalam satu platform.
      </p>
      <div class="mb-10 flex flex-wrap justify-center gap-4">
        <button type="button" onclick={onGoToRegister} class="group inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-primary-600 to-primary-500 px-8 py-4 text-sm font-semibold text-white shadow-xl shadow-primary-500/25 transition-all hover:-translate-y-1 hover:from-primary-700 hover:to-primary-600">
          Mulai Trial 14 Hari Gratis <ArrowRight class="h-5 w-5 transition-transform group-hover:translate-x-1" />
        </button>
        <a href="#fitur" class="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-8 py-4 text-sm font-semibold text-slate-700 shadow-sm transition-all hover:-translate-y-1 hover:bg-slate-50">
          <Zap class="h-5 w-5 text-primary-500" /> Lihat 12 Modul
        </a>
      </div>
      <div class="flex flex-wrap justify-center gap-6 text-sm text-slate-500">
        <div class="flex items-center gap-1.5"><Check class="h-4 w-4 text-emerald-500" />Tanpa kartu kredit</div>
        <div class="flex items-center gap-1.5"><Check class="h-4 w-4 text-emerald-500" />Setup &lt; 30 menit</div>
        <div class="flex items-center gap-1.5"><Check class="h-4 w-4 text-emerald-500" />Khusus untuk PPIU Indonesia</div>
      </div>

      <!-- Dashboard preview -->
      <div class="relative mx-auto mt-16 max-w-4xl">
        <div class="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white shadow-2xl shadow-slate-900/12">
          <div class="flex items-center gap-2 border-b border-slate-100 bg-slate-50 px-5 py-3">
            <span class="h-3 w-3 rounded-full bg-red-400"></span>
            <span class="h-3 w-3 rounded-full bg-yellow-400"></span>
            <span class="h-3 w-3 rounded-full bg-green-400"></span>
            <div class="ml-3 flex-1 rounded-lg border border-slate-100 bg-white px-4 py-1.5 text-xs text-slate-400">app.jamaah.in/dashboard</div>
          </div>
          <div class="p-5">
            <!-- KPI Cards -->
            <div class="mb-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div class="rounded-xl border border-primary-100/50 bg-gradient-to-br from-primary-50 to-white p-3">
                <p class="text-[10px] font-semibold uppercase tracking-wide text-primary-500">Total Piutang</p>
                <p class="mt-1 text-lg font-extrabold text-primary-700">Rp 284 jt</p>
                <p class="text-[10px] text-slate-400">48 jamaah aktif</p>
              </div>
              <div class="rounded-xl border border-emerald-100/50 bg-gradient-to-br from-emerald-50 to-white p-3">
                <p class="text-[10px] font-semibold uppercase tracking-wide text-emerald-600">Gross Profit</p>
                <p class="mt-1 text-lg font-extrabold text-emerald-700">Rp 142 jt</p>
                <p class="text-[10px] text-emerald-600">+18% vs bulan lalu</p>
              </div>
              <div class="rounded-xl border border-amber-100/50 bg-gradient-to-br from-amber-50 to-white p-3">
                <p class="text-[10px] font-semibold uppercase tracking-wide text-amber-600">Trip Aktif</p>
                <p class="mt-1 text-lg font-extrabold text-amber-700">5 Paket</p>
                <p class="text-[10px] text-slate-400">127 jamaah terdaftar</p>
              </div>
              <div class="rounded-xl border border-rose-100/50 bg-gradient-to-br from-rose-50 to-white p-3">
                <p class="text-[10px] font-semibold uppercase tracking-wide text-rose-500">Overdue</p>
                <p class="mt-1 text-lg font-extrabold text-rose-600">3 jamaah</p>
                <p class="text-[10px] text-rose-400">Perlu follow-up</p>
              </div>
            </div>
            <!-- Recent activity -->
            <div class="grid gap-3 sm:grid-cols-2">
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="mb-3 text-[11px] font-bold text-slate-700">P&L — Umroh Feb 2026</p>
                <div class="space-y-2">
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] text-slate-500">Pendapatan</span>
                    <span class="text-[11px] font-bold text-emerald-600">Rp 580.000.000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] text-slate-500">Pengeluaran Vendor</span>
                    <span class="text-[11px] font-bold text-rose-500">Rp 437.500.000</span>
                  </div>
                  <div class="mt-1 h-px bg-slate-200"></div>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] font-bold text-slate-700">Laba Kotor</span>
                    <span class="text-[12px] font-extrabold text-primary-700">Rp 142.500.000</span>
                  </div>
                  <div class="flex items-center justify-between">
                    <span class="text-[10px] text-slate-400">Margin</span>
                    <span class="text-[10px] font-semibold text-primary-500">24.6%</span>
                  </div>
                </div>
              </div>
              <div class="rounded-xl border border-slate-100 bg-slate-50 p-4">
                <p class="mb-3 text-[11px] font-bold text-slate-700">Pipeline Jamaah Aktif</p>
                <div class="space-y-1.5">
                  {#each [["Prospek", 12, "bg-slate-300"], ["Survey", 8, "bg-blue-400"], ["DP", 24, "bg-amber-400"], ["Cicilan", 18, "bg-orange-400"], ["Lunas", 65, "bg-emerald-500"]] as [label, n, color] (label)}
                    <div class="flex items-center gap-2">
                      <span class="w-14 text-right text-[10px] text-slate-400">{label}</span>
                      <div class="flex-1 overflow-hidden rounded-full bg-slate-200" style="height:6px">
                        <div class="{color} rounded-full" style="height:6px; width:{Math.round((Number(n)/65)*100)}%"></div>
                      </div>
                      <span class="w-6 text-right text-[10px] font-bold text-slate-600">{n}</span>
                    </div>
                  {/each}
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="absolute -inset-4 -z-10 rounded-[2rem] bg-gradient-to-br from-primary-500/10 to-emerald-500/10 blur-2xl"></div>
      </div>
    </div>
  </section>

  <!-- STATS STRIP -->
  <section class="border-y border-slate-100 bg-white py-10">
    <div class="mx-auto grid max-w-5xl grid-cols-2 gap-8 px-4 text-center sm:grid-cols-4 sm:px-6 lg:px-8">
      {#each stats as item}
        <div>
          <p class="text-2xl font-extrabold text-primary-700 sm:text-3xl">{item.value}</p>
          <p class="mt-1 text-xs font-medium text-slate-500">{item.label}</p>
        </div>
      {/each}
    </div>
  </section>

  <!-- PAIN POINTS -->
  <section id="masalah" class="bg-white py-20 lg:py-28">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-14 text-center">
        <div class="mb-4 inline-flex items-center gap-2 rounded-full border border-red-100 bg-red-50 px-4 py-1.5 text-xs font-semibold text-red-600">
          <AlertCircle class="h-3.5 w-3.5" /> Masalah Nyata di Lapangan
        </div>
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
          Travel Umroh Modern Masih<br /><span class="text-red-500">Bergantung pada Excel dan Intuisi</span>
        </h2>
        <p class="mx-auto max-w-xl text-lg text-slate-500">
          Grup WhatsApp sudah cukup untuk koordinasi lapangan. Tapi untuk urusan bisnis, ini yang masih menjadi masalah sehari-hari.
        </p>
      </div>
      <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {#each painPoints as point}
          {@const PointIcon = point.icon}
          <div class="rounded-2xl border border-slate-100 bg-white p-6 shadow-sm transition-all hover:-translate-y-1 hover:shadow-md">
            <div class={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl ${point.bg}`}>
              <PointIcon class={`h-5 w-5 ${point.color}`} />
            </div>
            <h3 class="mb-2 text-sm font-bold text-slate-900">{point.title}</h3>
            <p class="text-sm leading-relaxed text-slate-500">{point.desc}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- MODULES -->
  <section id="fitur" class="relative overflow-hidden bg-slate-50 py-20 lg:py-32">
    <div class="absolute inset-0 hero-pattern opacity-50"></div>
    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-16 text-center">
        <div class="mb-5 inline-flex items-center gap-2 rounded-full border border-primary-100 bg-white px-4 py-1.5 text-xs font-semibold text-primary-700">
          <Sparkles class="h-3.5 w-3.5" /> 12 Modul Terintegrasi
        </div>
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
          Setara Jurnal + Accurate,<br /><span class="gradient-text">tapi Dirancang untuk PPIU</span>
        </h2>
        <p class="mx-auto max-w-2xl text-lg text-slate-500">
          Software akuntansi umum tidak mengerti paket reguler vs VIP, skema DP + cicilan musim haji, atau komisi jaringan sub-agen. Jamaah.in mengerti semua itu sejak hari pertama.
        </p>
      </div>
      <div class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {#each modules as mod}
          {@const ModIcon = mod.icon}
          <div class="feature-shine group relative rounded-2xl border border-white bg-white p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
            {#if mod.badge}
              <span class="absolute right-4 top-4 rounded-full bg-primary-50 px-2 py-0.5 text-[10px] font-bold text-primary-600">{mod.badge}</span>
            {/if}
            <div class={`mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${mod.color} shadow-lg ${mod.shadow} transition-transform group-hover:scale-105`}>
              <ModIcon class="h-5 w-5 text-white" />
            </div>
            <h3 class="mb-2 text-sm font-bold text-slate-900">{mod.title}</h3>
            <p class="text-xs leading-relaxed text-slate-500">{mod.desc}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- HOW IT WORKS -->
  <section class="bg-white py-20 lg:py-28">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
      <div class="mb-14 text-center">
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Alur Kerja yang Sudah Dipahami</h2>
        <p class="text-lg text-slate-500">Ikuti alur yang sama seperti yang selama ini dilakukan — hanya lebih cepat dan otomatis.</p>
      </div>
      <div class="grid gap-8 sm:grid-cols-3">
        {#each [
          { step: "01", icon: Package, color: "bg-primary-600", title: "Buat Paket & Harga", desc: "Input detail paket umroh atau haji: maskapai, hotel, kuota, harga per tipe kamar, dan komponen biaya HPP. Paket siap dipublish dalam 10 menit." },
          { step: "02", icon: ScanLine, color: "bg-emerald-600", title: "Daftarkan Jamaah", desc: "Scan KTP & paspor, data masuk otomatis ke profil jamaah. Pilih paket + tipe kamar + skema pembayaran. Invoice terbuat otomatis." },
          { step: "03", icon: TrendingUp, color: "bg-amber-500", title: "Pantau Bisnis Real-time", desc: "Lihat siapa yang belum bayar, berapa gross profit trip, pengeluaran vendor berapa. Semua di satu dashboard, tidak perlu hitung manual." }
        ] as item}
          {@const StepIcon = item.icon}
          <div class="relative">
            <div class="mb-4 flex items-center gap-3">
              <div class={`flex h-10 w-10 items-center justify-center rounded-xl ${item.color}`}>
                <StepIcon class="h-5 w-5 text-white" />
              </div>
              <span class="text-3xl font-extrabold text-slate-100">{item.step}</span>
            </div>
            <h3 class="mb-2 text-base font-bold text-slate-900">{item.title}</h3>
            <p class="text-sm leading-relaxed text-slate-500">{item.desc}</p>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- COMPARISON VS EXCEL -->
  <section class="bg-slate-50 py-20 lg:py-28">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
      <div class="mb-14 text-center">
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Jamaah.in vs Excel</h2>
        <p class="text-lg text-slate-500">Perbandingan konkret dari yang paling sering dikeluhkan owner travel.</p>
      </div>
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div class="grid grid-cols-2 border-b border-slate-100 bg-slate-50 px-6 py-3 text-xs font-bold uppercase tracking-wide">
          <div class="text-red-500">Cara Lama (Excel / Manual)</div>
          <div class="text-emerald-600">Dengan Jamaah.in</div>
        </div>
        {#each compVsExcel as row, i}
          <div class={`grid grid-cols-2 gap-4 px-6 py-4 ${i < compVsExcel.length - 1 ? "border-b border-slate-50" : ""}`}>
            <div class="flex items-start gap-2 text-sm text-slate-500">
              <X class="mt-0.5 h-4 w-4 flex-shrink-0 text-red-400" />{row.bad}
            </div>
            <div class="flex items-start gap-2 text-sm text-slate-700">
              <Check class="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />{row.good}
            </div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- COMPARISON VS ACCOUNTING SOFTWARE -->
  <section class="bg-white py-20 lg:py-24">
    <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
      <div class="mb-14 text-center">
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Jamaah.in vs Software Akuntansi Umum</h2>
        <p class="text-lg text-slate-500">Jurnal dan Accurate bagus untuk akuntansi umum — tapi tidak tahu apa itu paket haji atau komisi sub-agen.</p>
      </div>
      <div class="overflow-hidden rounded-2xl border border-slate-200 shadow-sm">
        <div class="grid grid-cols-3 border-b border-slate-100 bg-slate-800 px-4 py-3 text-xs font-bold uppercase tracking-wide text-white">
          <div class="text-slate-300">Aspek</div>
          <div class="text-center text-slate-400">Jurnal / Accurate</div>
          <div class="text-center text-emerald-400">Jamaah.in</div>
        </div>
        {#each compVsAccounting as row, i}
          <div class={`grid grid-cols-3 gap-4 px-4 py-3.5 ${i % 2 === 0 ? "bg-white" : "bg-slate-50"} ${i < compVsAccounting.length - 1 ? "border-b border-slate-100" : ""}`}>
            <div class="text-xs font-semibold text-slate-700">{row.aspect}</div>
            <div class="text-center text-xs text-slate-400">{row.accounting}</div>
            <div class="text-center text-xs font-medium text-emerald-700">{row.jamaah}</div>
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- PRICING -->
  <section id="harga" class="relative overflow-hidden bg-slate-50 py-20 lg:py-32">
    <div class="absolute left-1/2 top-1/2 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary-50/80 blur-[100px]"></div>
    <div class="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-16 text-center">
        <div class="mb-5 inline-flex items-center gap-2 rounded-full border border-primary-100 bg-white px-4 py-1.5 text-xs font-semibold text-primary-700">
          <Star class="h-3.5 w-3.5" /> Harga Terjangkau
        </div>
        <h2 class="mb-4 text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl lg:text-5xl">
          Lebih Murah dari<br /><span class="gradient-text">Satu Jam Kerja Lembur</span>
        </h2>
        <p class="mx-auto max-w-xl text-lg text-slate-500">Mulai trial 14 hari gratis tanpa kartu kredit. Upgrade kapan saja seiring bisnis berkembang.</p>
      </div>

      <div class="mx-auto grid max-w-6xl items-stretch gap-5 md:grid-cols-2 xl:grid-cols-4">
        {#each plans as plan}
          <div class={`feature-shine relative flex flex-col rounded-2xl bg-white p-7 transition-all duration-300 ${plan.featured ? "border-2 border-primary-300 shadow-xl shadow-primary-500/12 md:-translate-y-2" : "border border-slate-200 shadow-sm hover:shadow-lg"}`}>
            {#if plan.badge}
              <div class="mb-4 flex">
                <span class={`inline-flex items-center rounded-full px-3 py-1 text-[11px] font-bold text-white ${plan.featured ? "bg-gradient-to-r from-primary-600 to-primary-500" : "bg-gradient-to-r from-emerald-500 to-emerald-600"}`}>{plan.badge}</span>
              </div>
            {:else}
              <div class="mb-4 h-7"></div>
            {/if}

            <h3 class="text-base font-bold text-slate-900">{plan.name}</h3>
            <p class="mt-1 text-xs text-slate-500">{plan.note}</p>

            <div class="my-5">
              <span class="text-3xl font-extrabold text-slate-900">{plan.price}</span>
              {#if plan.period}<span class="text-sm font-medium text-slate-400"> {plan.period}</span>{/if}
            </div>

            <ul class="mb-6 flex-1 space-y-2.5">
              {#each plan.items as item}
                <li class="flex items-start gap-2 text-xs text-slate-600"><Check class="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-emerald-500" />{item}</li>
              {/each}
              {#each plan.muted as item}
                <li class="flex items-start gap-2 text-xs text-slate-300"><X class="mt-0.5 h-3.5 w-3.5 flex-shrink-0 text-slate-200" />{item}</li>
              {/each}
            </ul>

            <button
              type="button"
              onclick={onGoToRegister}
              class={`w-full rounded-xl py-3 text-sm font-semibold transition-all ${plan.featured ? "bg-gradient-to-r from-primary-600 to-primary-500 text-white shadow-lg shadow-primary-500/20 hover:-translate-y-0.5 hover:from-primary-700 hover:to-primary-600" : "border-2 border-slate-200 text-slate-700 hover:border-primary-200 hover:bg-primary-50 hover:text-primary-700"}`}
            >
              {plan.cta}
            </button>
          </div>
        {/each}
      </div>

      <p class="mt-8 text-center text-sm text-slate-400">
        Paket tahunan tersedia — Pro Rp 2.990.000/thn dan Business Rp 5.990.000/thn (hemat ~2 bulan).
        <br class="hidden sm:inline" />AI Scanner credits terpisah dari subscription.
      </p>
    </div>
  </section>

  <!-- FAQ -->
  <section id="faq" class="bg-white py-20 lg:py-28">
    <div class="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
      <div class="mb-14 text-center">
        <h2 class="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">Pertanyaan yang Sering Ditanyakan</h2>
      </div>
      <div class="space-y-3">
        {#each faqs as faq, i}
          <div class="overflow-hidden rounded-2xl border border-slate-100 bg-white transition-all hover:border-primary-100">
            <button type="button" onclick={() => (openFaq = openFaq === i ? -1 : i)} class="flex w-full items-center justify-between gap-4 px-6 py-5 text-left">
              <span class="text-sm font-semibold text-slate-900">{faq.q}</span>
              <ChevronDown class={`h-5 w-5 flex-shrink-0 text-slate-400 transition-transform ${openFaq === i ? "rotate-180" : ""}`} />
            </button>
            {#if openFaq === i}
              <div class="px-6 pb-5 text-sm leading-relaxed text-slate-500">{faq.a}</div>
            {/if}
          </div>
        {/each}
      </div>
    </div>
  </section>

  <!-- CTA -->
  <section class="relative overflow-hidden py-20 lg:py-32">
    <div class="absolute inset-0 bg-gradient-to-br from-primary-700 via-primary-800 to-slate-900"></div>
    <div class="hero-pattern absolute inset-0 opacity-10"></div>
    <div class="relative mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
      <div class="mb-6 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs font-semibold text-white backdrop-blur-sm">
        <Rocket class="h-3.5 w-3.5 text-emerald-300" /> Mulai Sekarang, Tanpa Risiko
      </div>
      <h2 class="mb-5 text-3xl font-bold leading-tight tracking-tight text-white sm:text-4xl lg:text-5xl">
        Coba Semua Fitur Pro<br />Gratis Selama 14 Hari
      </h2>
      <p class="mx-auto mb-10 max-w-xl text-lg text-primary-200">
        Daftar dalam 30 detik. Tidak perlu kartu kredit. Tidak perlu training panjang — onboarding &lt; 30 menit dan langsung bisa pakai.
      </p>
      <div class="flex flex-wrap justify-center gap-4">
        <button type="button" onclick={onGoToRegister} class="group inline-flex items-center gap-2 rounded-2xl bg-white px-8 py-4 text-sm font-semibold text-primary-700 shadow-xl transition-all hover:-translate-y-1 hover:bg-primary-50">
          Daftar Gratis Sekarang <ArrowRight class="h-5 w-5 transition-transform group-hover:translate-x-1" />
        </button>
        <button type="button" onclick={onGoToLogin} class="inline-flex items-center gap-2 rounded-2xl border border-white/20 bg-white/10 px-8 py-4 text-sm font-semibold text-white backdrop-blur-sm transition-all hover:-translate-y-1 hover:bg-white/20">
          Sudah punya akun? Masuk
        </button>
      </div>
    </div>
  </section>

  <!-- FOOTER -->
  <footer class="bg-slate-900 pb-8 pt-16 text-slate-400">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
      <div class="mb-12 grid grid-cols-2 gap-8 lg:grid-cols-4 lg:gap-16">
        <div class="col-span-2 lg:col-span-1">
          <div class="mb-4">
            <BrandLogo size="small" variant="light" />
          </div>
          <p class="mb-4 text-sm leading-relaxed">Sistem administrasi bisnis travel umroh & haji khusus untuk PPIU Indonesia.</p>
          <div class="flex gap-3">
            <a href="/" aria-label="Instagram" class="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 transition-colors hover:bg-primary-600"><Instagram class="h-4 w-4" /></a>
            <a href="/" aria-label="YouTube" class="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 transition-colors hover:bg-primary-600"><Youtube class="h-4 w-4" /></a>
            <a href="/" aria-label="WhatsApp" class="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-800 transition-colors hover:bg-primary-600"><MessageCircle class="h-4 w-4" /></a>
          </div>
        </div>

        <div>
          <h4 class="mb-4 text-sm font-bold uppercase tracking-wide text-white">Produk</h4>
          <ul class="space-y-2.5 text-sm">
            <li><a href="#fitur" class="hover:text-primary-400">Paket & Harga</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">CRM & Pipeline</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">Invoice & Pembayaran</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">Laporan Keuangan</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">AI Scanner</a></li>
          </ul>
        </div>

        <div>
          <h4 class="mb-4 text-sm font-bold uppercase tracking-wide text-white">Modul Lanjutan</h4>
          <ul class="space-y-2.5 text-sm">
            <li><a href="#fitur" class="hover:text-primary-400">Vendor & Biaya Ops</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">Komisi Agen</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">E-Kontrak Digital</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">Persediaan</a></li>
            <li><a href="#fitur" class="hover:text-primary-400">Penggajian</a></li>
          </ul>
        </div>

        <div>
          <h4 class="mb-4 text-sm font-bold uppercase tracking-wide text-white">Perusahaan</h4>
          <ul class="space-y-2.5 text-sm">
            <li><a href="/" class="hover:text-primary-400">Tentang Jamaah.in</a></li>
            <li><a href="#harga" class="hover:text-primary-400">Harga & Paket</a></li>
            <li><a href="/" class="hover:text-primary-400">Kebijakan Privasi</a></li>
            <li><a href="/" class="hover:text-primary-400">Syarat & Ketentuan</a></li>
            <li><a href="/" class="hover:text-primary-400">Hubungi Kami</a></li>
          </ul>
        </div>
      </div>

      <div class="flex flex-col items-center justify-between gap-4 border-t border-slate-800 pt-8 md:flex-row">
        <p class="text-xs text-slate-500">© 2026 Jamaah.in. All rights reserved. Dibuat untuk 2.200+ PPIU Indonesia.</p>
        <p class="text-xs text-slate-500">v2.1 — Go Microservices, Self-Hosted, Data Aman di Server Anda</p>
      </div>
    </div>
  </footer>
</div>

<style>
  .landing {
    font-family: "Plus Jakarta Sans", "Inter", system-ui, sans-serif;
    background: #f8fafc;
    color: #0f172a;
    min-height: 100vh;
    overflow-x: hidden;
  }

  .gradient-text {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 50%, #10b981 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .hero-pattern {
    background-image: radial-gradient(circle at 1px 1px, rgba(37, 99, 235, 0.06) 1px, transparent 0);
    background-size: 40px 40px;
  }

  .animated-gradient {
    background: linear-gradient(-45deg, #eff6ff, #ffffff, #ecfdf5, #ffffff);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
  }

  .glass-card {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  @keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
  }

  :global(.animate-float) {
    animation: float 6s ease-in-out infinite;
  }

  :global(.animate-float-delay) {
    animation: float 6s ease-in-out 2s infinite;
  }

  @keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-16px); }
  }

  .feature-shine {
    position: relative;
    overflow: hidden;
  }

  .feature-shine::after {
    content: "";
    position: absolute;
    top: -60%;
    left: -60%;
    width: 220%;
    height: 220%;
    background: linear-gradient(to bottom right, transparent 0%, transparent 42%, rgba(255,255,255,0.3) 50%, transparent 58%, transparent 100%);
    transform: rotate(30deg);
    opacity: 0;
    transition: all 0.6s;
  }

  .feature-shine:hover::after {
    left: 100%;
    top: 100%;
    opacity: 1;
  }
</style>

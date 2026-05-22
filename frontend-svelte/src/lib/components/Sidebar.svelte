<script>
  import {
    BarChart3,
    BookOpen,
    Briefcase,
    Building2,
    ChevronDown,
    ClipboardList,
    Crown,
    DollarSign,
    FileText,
    Home,
    LogOut,
    Menu,
    Package,
    Receipt,
    ScanLine,
    Settings,
    TrendingUp,
    Users,
    UsersRound,
    Wallet,
    X,
  } from "lucide-svelte";
  import BrandLogo from "./BrandLogo.svelte";

  let {
    currentPage = "dashboard",
    onPageChange,
    user = null,
    isPro = false,
    trialAvailable = false,
    jamaahCount = 0,
    onLogout,
    collapsed = false,
    onToggleCollapse,
  } = $props();

  let mobileMenuOpen = $state(false);

  // Which expandable section is open on mobile
  let openSection = $state("main");

  const navGroups = [
    {
      id: "main",
      label: "Utama",
      items: [
        { id: "dashboard", label: "Dashboard", icon: Home, page: "dashboard" },
        { id: "scanner", label: "AI Scanner", icon: ScanLine, page: "scanner", pulse: true },
      ],
    },
    {
      id: "ops",
      label: "Operasional",
      items: [
        { id: "packages", label: "Paket & Harga", icon: Package, page: "packages" },
        { id: "crm", label: "CRM & Jamaah", icon: UsersRound, page: "crm", isCRM: true },
        { id: "invoices", label: "Invoice & Bayar", icon: Receipt, page: "invoices" },
        { id: "documents", label: "Dokumen & Paspor", icon: ClipboardList, page: "documents" },
      ],
    },
    {
      id: "finance",
      label: "Keuangan",
      ownerOnly: true,
      items: [
        { id: "finance", label: "Laporan Keuangan", icon: TrendingUp, page: "finance" },
        { id: "vendors", label: "Vendor & Biaya", icon: Building2, page: "vendors" },
        { id: "agents", label: "Komisi Agen", icon: DollarSign, page: "agents" },
      ],
    },
    {
      id: "advanced",
      label: "Advanced",
      proOnly: true,
      items: [
        { id: "contracts", label: "E-Kontrak", icon: FileText, page: "contracts" },
        { id: "stock", label: "Persediaan", icon: Briefcase, page: "stock" },
        { id: "payroll", label: "Penggajian", icon: Wallet, page: "payroll" },
      ],
    },
    {
      id: "settings",
      label: "Pengaturan",
      items: [
        { id: "team", label: "Tim & Organisasi", icon: Users, page: "team" },
        { id: "profile", label: "Profil Saya", icon: Settings, page: "profile" },
      ],
    },
  ];

  // Legacy items that are being retired from the sidebar but still reachable
  // (rooming, manifest, analytics, itinerary, grup stay accessible via dashboard shortcuts)

  function isActive(page) {
    return currentPage === page;
  }

  function handleNavClick(pageId) {
    onPageChange?.(pageId);
    mobileMenuOpen = false;
  }

  function initial() {
    return (user?.name || "A").charAt(0).toUpperCase();
  }

  // Determine if a group should be shown based on role
  function showGroup(group) {
    if (group.ownerOnly) {
      return user?.role === "owner" || user?.is_super_admin;
    }
    return true;
  }
</script>

<!-- Mobile top bar -->
<div class="lg:hidden fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4">
  <button
    type="button"
    onclick={() => (mobileMenuOpen = true)}
    class="flex h-10 w-10 items-center justify-center rounded-xl transition-colors hover:bg-slate-100"
    aria-label="Buka menu"
  >
    <Menu class="h-6 w-6 text-slate-600" />
  </button>
  <BrandLogo size="small" />
  <button
    type="button"
    onclick={() => handleNavClick("profile")}
    class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-600 text-sm font-bold text-white shadow-lg shadow-primary-500/20"
    aria-label="Profil"
  >
    {initial()}
  </button>
</div>

{#if mobileMenuOpen}
  <button
    type="button"
    class="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
    onclick={() => (mobileMenuOpen = false)}
    aria-label="Tutup menu"
  ></button>
{/if}

<aside
  class="fixed left-0 top-0 z-50 flex h-full w-[272px] flex-col border-r border-slate-200/80 bg-white transition-transform duration-300 lg:translate-x-0
    {mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}"
>
  <div class="flex h-[72px] items-center justify-between border-b border-slate-100 px-6">
    <BrandLogo size="small" />
    <button
      type="button"
      class="flex h-9 w-9 items-center justify-center rounded-xl text-slate-500 transition-colors hover:bg-slate-100 lg:hidden"
      onclick={() => (mobileMenuOpen = false)}
      aria-label="Tutup"
    >
      <X class="h-5 w-5" />
    </button>
  </div>

  <nav class="flex-1 overflow-y-auto px-4 py-4 space-y-5">
    {#each navGroups as group}
      {#if showGroup(group)}
        <div>
          <p class="mb-1.5 px-3 text-[10px] font-bold uppercase tracking-wider text-slate-400">
            {group.label}
            {#if group.proOnly && !isPro}
              <span class="ml-1 rounded-sm bg-amber-100 px-1 py-0.5 text-[9px] font-bold text-amber-600">PRO</span>
            {/if}
          </p>
          <div class="space-y-0.5">
            {#each group.items as item}
              {@const ItemIcon = item.icon}
              <button
                type="button"
                onclick={() => handleNavClick(item.page)}
                class="sidebar-link {isActive(item.page) ? 'active' : ''}"
              >
                <ItemIcon class="h-[18px] w-[18px] flex-shrink-0" />
                <span>{item.label}</span>
                {#if item.isCRM && jamaahCount > 0}
                  <span class="ml-auto rounded-full bg-primary-100 px-2 py-0.5 text-[10px] font-bold text-primary-600">{jamaahCount}</span>
                {/if}
                {#if item.pulse}
                  <span class="ml-auto h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                {/if}
              </button>
            {/each}
          </div>
        </div>
      {/if}
    {/each}
  </nav>

  <div class="border-t border-slate-100 px-4 py-4">
    {#if !isPro}
      <div class="mb-3 rounded-2xl bg-gradient-to-br from-primary-600 to-primary-700 p-4 text-white">
        <div class="mb-2 flex items-center gap-2">
          <Crown class="h-4 w-4 text-primary-200" />
          <span class="text-xs font-bold">Upgrade ke Pro</span>
        </div>
        <p class="mb-3 text-[11px] leading-relaxed text-primary-200">
          Invoice, laporan keuangan, e-kontrak, dan semua modul bisnis.
        </p>
        <button
          type="button"
          onclick={() => handleNavClick(trialAvailable ? "trial:activate" : "profile:upgrade")}
          class="w-full rounded-xl bg-white py-2 text-[11px] font-bold text-primary-700 transition-colors hover:bg-primary-50"
        >
          {trialAvailable ? "Coba 14 Hari Gratis" : "Lihat Paket"}
        </button>
      </div>
    {/if}

    <button
      type="button"
      onclick={onLogout}
      class="flex w-full items-center gap-3 rounded-xl px-4 py-2.5 text-sm font-medium text-slate-500 transition-colors hover:bg-red-50 hover:text-red-600"
    >
      <LogOut class="h-5 w-5" />
      Keluar
    </button>
  </div>
</aside>

<div class="hidden h-0 w-[272px] flex-shrink-0 lg:block"></div>

<style>
  .sidebar-link {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    border-radius: 10px;
    padding: 9px 14px;
    color: #64748b;
    font-size: 13.5px;
    font-weight: 500;
    transition: all 0.15s;
    text-align: left;
  }

  .sidebar-link:hover {
    background: #f1f5f9;
    color: #334155;
  }

  .sidebar-link.active {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    color: #fff;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
  }
</style>

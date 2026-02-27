<!--
  Sidebar.svelte — Professional Navigation Sidebar
  
  Design: Compact, clean, efficient use of space
-->
<script>
  import {
    Home,
    Package,
    Hotel,
    LogOut,
    Crown,
    Menu,
    X,
    ChevronLeft,
    ChevronRight,
    Building2,
    ScanLine,
    CalendarDays,
    Lock,
  } from "lucide-svelte";
  import BrandLogo from "./BrandLogo.svelte";
  import NotificationBell from "./NotificationBell.svelte";

  let {
    currentPage = "dashboard",
    onPageChange,
    user = null,
    isPro = false,
    onLogout,
    collapsed = false,
    onToggleCollapse,
  } = $props();

  const menuItems = [
    { id: "dashboard", label: "Dashboard", icon: Home, proOnly: false },
    { id: "scanner", label: "Scanner", icon: ScanLine, proOnly: false },
    { id: "itinerary", label: "Jadwal", icon: CalendarDays, proOnly: true },
    { id: "inventory", label: "Inventori", icon: Package, proOnly: true },
    { id: "rooming", label: "Rooming", icon: Hotel, proOnly: true },
    { id: "team", label: "Tim", icon: Building2, proOnly: true },
  ];

  let visibleItems = $derived(menuItems);
  let mobileMenuOpen = $state(false);

  function handleNavClick(pageId) {
    onPageChange(pageId);
    mobileMenuOpen = false;
  }
</script>

<!-- Mobile Header -->
<div
  class="lg:hidden fixed top-0 left-0 right-0 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 z-40 px-3 py-2 flex items-center justify-between"
>
  <button
    type="button"
    onclick={() => (mobileMenuOpen = true)}
    class="p-1.5 hover:bg-slate-100 rounded-lg"
    aria-label="Buka menu"
  >
    <Menu class="h-5 w-5 text-slate-600" />
  </button>

  <span class="text-sm font-semibold text-slate-800">Jamaah.in</span>

  {#if user}
    <div
      class="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold"
      style="background-color: {user.avatar_color || '#10b981'}"
    >
      {user.name?.charAt(0)?.toUpperCase() || "U"}
    </div>
  {:else}
    <div class="w-7"></div>
  {/if}
</div>

<!-- Mobile Overlay -->
{#if mobileMenuOpen}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <div
    class="lg:hidden fixed inset-0 bg-black/40 z-40"
    onclick={() => (mobileMenuOpen = false)}
    role="button"
    tabindex="-1"
    aria-label="Tutup menu"
  ></div>
{/if}

<!-- Sidebar -->
<aside
  class="fixed top-0 left-0 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 z-50 transition-all duration-200
    {mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
    {collapsed ? 'lg:w-16' : 'lg:w-64'}
    w-64"
>
  <!-- Header -->
  <div
    class="h-14 flex items-center justify-between px-4 border-b border-slate-200"
  >
    {#if collapsed}
      <button
        type="button"
        onclick={onToggleCollapse}
        class="flex items-center justify-center w-full py-1 hover:bg-slate-50 rounded transition-colors"
        aria-label="Perluas sidebar"
      >
        <BrandLogo size="small" iconOnly={true} />
      </button>
    {:else}
      <BrandLogo size="small" iconOnly={false} />
      <div class="flex items-center gap-1">
        {#if !isPro}
          <button
            type="button"
            onclick={() => handleNavClick("header:upgrade")}
            class="p-1.5 text-amber-500 hover:text-amber-600 hover:bg-amber-50 rounded-lg transition-colors"
            aria-label="Upgrade ke Pro"
            title="Upgrade ke Pro"
          >
            <Crown class="h-4 w-4" />
          </button>
        {/if}
        <NotificationBell onNavigate={onPageChange} />
        <button
          type="button"
          onclick={onToggleCollapse}
          class="p-1 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded transition-colors"
          aria-label="Minimalkan sidebar"
        >
          <ChevronLeft class="h-4 w-4" />
        </button>
      </div>
    {/if}

    <button
      type="button"
      class="lg:hidden p-1.5 hover:bg-slate-100 rounded absolute right-2"
      onclick={() => (mobileMenuOpen = false)}
      aria-label="Tutup"
    >
      <X class="h-4 w-4 text-slate-500" />
    </button>
  </div>

  <!-- User Info - Compact -->
  {#if user && !collapsed}
    <button
      type="button"
      onclick={() => handleNavClick("profile")}
      class="w-full px-4 py-3 border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer text-left"
    >
      <div class="flex items-center gap-2.5">
        <div
          class="w-9 h-9 rounded-full flex items-center justify-center text-white text-sm font-bold flex-shrink-0"
          style="background-color: {user.avatar_color || '#10b981'}"
        >
          {user.name?.charAt(0)?.toUpperCase() || "U"}
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-slate-800 truncate">
            {user.name || "User"}
          </p>
          <p class="text-xs text-slate-400 truncate">{user.email}</p>
        </div>
        {#if isPro}
          <Crown class="h-3.5 w-3.5 text-amber-500 flex-shrink-0" />
        {/if}
      </div>
    </button>
  {:else if user && collapsed}
    <button
      type="button"
      onclick={() => handleNavClick("profile")}
      class="py-2 flex justify-center border-b border-slate-100 hover:bg-slate-50 transition-colors cursor-pointer w-full"
      title="Profil"
    >
      <div
        class="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold"
        style="background-color: {user.avatar_color || '#10b981'}"
        title={user.name}
      >
        {user.name?.charAt(0)?.toUpperCase() || "U"}
      </div>
    </button>
  {/if}

  <!-- Navigation -->
  <nav class="flex-1 px-3 py-3 space-y-1">
    {#each visibleItems as item}
      <button
        type="button"
        onclick={() => handleNavClick(item.id)}
        class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg transition-all text-sm
          {currentPage === item.id
          ? 'bg-emerald-50 text-emerald-700 font-medium'
          : 'text-slate-600 hover:bg-slate-50 hover:text-slate-800'}
          {collapsed ? 'lg:justify-center' : ''}"
        title={item.label}
      >
        <item.icon class="h-[18px] w-[18px] flex-shrink-0" />
        {#if !collapsed}
          <span class="flex-1 text-left text-sm">{item.label}</span>
          {#if item.proOnly && !isPro}
            <span
              class="px-1.5 py-0.5 text-[10px] font-semibold bg-slate-100 text-slate-500 rounded flex items-center gap-0.5"
              ><Lock class="h-2.5 w-2.5" /> PRO</span
            >
          {:else if item.proOnly}
            <span
              class="px-1.5 py-0.5 text-[10px] font-semibold bg-amber-100 text-amber-700 rounded"
              >PRO</span
            >
          {/if}
        {/if}
      </button>
    {/each}
  </nav>

  <!-- Pro CTA (compact) -->
  {#if !isPro && !collapsed}
    <div class="px-3 pb-3">
      <div
        class="bg-gradient-to-br from-emerald-50 to-amber-50 rounded-lg p-3 border border-emerald-100"
      >
        <div class="flex items-center gap-2 mb-2">
          <Crown class="h-4 w-4 text-amber-500" />
          <span class="text-sm font-semibold text-slate-800">Upgrade Pro</span>
        </div>
        <p class="text-xs text-slate-500 mb-2.5">Unlock Inventori & Rooming</p>
        <button
          type="button"
          onclick={() => handleNavClick("profile:upgrade")}
          class="w-full py-1.5 bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-medium rounded transition-colors"
        >
          Rp80rb/bulan
        </button>
        <p class="text-[10px] text-center text-slate-400 mt-1">
          atau coba gratis 7 hari
        </p>
      </div>
    </div>
  {/if}

  <!-- Logout -->
  <div class="p-2 border-t border-slate-100 dark:border-slate-700">
    <button
      type="button"
      onclick={onLogout}
      class="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-slate-600 hover:bg-red-50 hover:text-red-600 transition-colors text-sm {collapsed
        ? 'lg:justify-center'
        : ''}"
    >
      <LogOut class="h-[18px] w-[18px] flex-shrink-0" />
      {#if !collapsed}
        <span class="text-sm">Keluar</span>
      {/if}
    </button>
  </div>
</aside>

<!-- Spacer -->
<div
  class="lg:{collapsed
    ? 'w-16'
    : 'w-64'} h-0 flex-shrink-0 transition-all duration-200"
></div>

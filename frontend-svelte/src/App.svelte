<script>
  import { onMount } from "svelte";
  import LandingPage from "./lib/pages/LandingPage.svelte";
  import Login from "./lib/pages/Login.svelte";
  import Dashboard from "./lib/pages/Dashboard.svelte";
  import ProfilePage from "./lib/pages/ProfilePage.svelte";
  import InventoryPage from "./lib/pages/InventoryPage.svelte";
  import RoomingPage from "./lib/pages/RoomingPage.svelte";
  import TeamPage from "./lib/pages/TeamPage.svelte";
  import ScannerPage from "./lib/pages/ScannerPage.svelte";
  import ItineraryPage from "./lib/pages/ItineraryPage.svelte";
  import MutawwifManifest from "./lib/pages/MutawwifManifest.svelte";
  import PublicRegistrationPage from "./lib/pages/PublicRegistrationPage.svelte";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import ProGateScreen from "./lib/components/ProGateScreen.svelte";
  import UpgradeModal from "./lib/components/UpgradeModal.svelte";
  import Toast from "./lib/components/Toast.svelte";
  import { ApiService } from "./lib/services/api";

  // Check hash synchronously BEFORE first render to avoid flash of wrong page
  function getInitialPageAndTokens() {
    if (typeof window === "undefined") return { page: "landing", sharedToken: "", registrationToken: "" };
    const hash = window.location.hash;
    const manifestMatch = hash.match(/^#\/m\/([a-f0-9]+)$/i);
    const registrationMatch = hash.match(/^#\/reg\/([a-zA-Z0-9_-]+)$/i);
    if (manifestMatch) {
      return { page: "mutawwif", sharedToken: manifestMatch[1], registrationToken: "" };
    }
    if (registrationMatch) {
      return { page: "registration", sharedToken: "", registrationToken: registrationMatch[1] };
    }
    return { page: "landing", sharedToken: "", registrationToken: "" };
  }
  const initial = getInitialPageAndTokens();

  // Pages: 'landing' | 'login' | 'register' | 'dashboard' | 'profile' | 'inventory' | 'rooming' | 'mutawwif'
  let currentPage = $state(initial.page);
  let user = $state(null);
  let subscription = $state(null);
  let sidebarCollapsed = $state(false);
  let showGlobalUpgradeModal = $state(false);
  let sharedToken = $state(initial.sharedToken); // For /#/m/{token} public manifest
  let registrationToken = $state(initial.registrationToken); // For /#/reg/{token} public registration

  // Derived
  let isPro = $derived(
    subscription?.plan === "pro" && subscription?.status !== "expired",
  );
  let trialAvailable = $state(false);

  // Feature gate configs for Pro-only pages
  const proFeatures = {
    inventory: {
      name: "Inventory Checklist",
      desc: "Kelola stok koper, ihram, mukena, dan perlengkapan jamaah. Distribusi tercatat rapi, tidak ada yang terlewat.",
      highlights: [
        "Kelola stok semua item di satu tempat",
        "Forecast kebutuhan otomatis berdasarkan data jamaah",
        "Tracking distribusi per jamaah — siapa sudah terima",
      ],
    },
    rooming: {
      name: "Smart Auto-Rooming",
      desc: "Bagi kamar hotel secara otomatis. Gender dipisahkan, keluarga disatukan — cukup 1 klik.",
      highlights: [
        "Algoritma cerdas mengisi kamar Quad/Triple/Double",
        "Laki-laki & perempuan otomatis dipisahkan",
        "Drag & drop untuk penyesuaian manual",
      ],
    },
    team: {
      name: "Manajemen Tim",
      desc: "Kelola tim Mutawwif dan staf operasional Anda. Bagikan akses manifest digital yang aman.",
      highlights: [
        "Undang anggota tim via email",
        "Atur hak akses per role (Admin / Mutawwif)",
        "Manifest digital aman dengan PIN untuk Mutawwif",
      ],
    },
    itinerary: {
      name: "Jadwal Perjalanan",
      desc: "Atur jadwal perjalanan umrah dari hari ke hari. Jamaah dan Mutawwif bisa melihat agenda via manifest digital.",
      highlights: [
        "Buat jadwal harian lengkap dari keberangkatan sampai pulang",
        "Otomatis tampil di manifest digital Mutawwif",
        "Template jadwal untuk reuse di grup berikutnya",
      ],
    },
  };
  let groups = $state([]);

  onMount(async () => {
    // Clean up any leftover dark mode from previous versions
    document.documentElement.classList.remove("dark");
    localStorage.removeItem("darkMode");

    // If already on public page (set by getInitialPageAndTokens), skip auth flow
    if (currentPage === "mutawwif" || currentPage === "registration") {
      return;
    }

    // Listen for hash changes (e.g., user navigates to /#/m/... or /#/reg/...)
    window.addEventListener("hashchange", () => {
      const h = window.location.hash;
      const m = h.match(/^#\/m\/([a-f0-9]+)$/i);
      const r = h.match(/^#\/reg\/([a-zA-Z0-9_-]+)$/i);
      if (m) {
        sharedToken = m[1];
        currentPage = "mutawwif";
      }
      if (r) {
        registrationToken = r[1];
        currentPage = "registration";
      }
    });

    // Check for existing token — optimistic navigation
    const token = localStorage.getItem("token");
    const savedUser = localStorage.getItem("user");
    if (token && savedUser) {
      // P4: Show dashboard immediately from cached user
      try {
        user = JSON.parse(savedUser);
      } catch {
        user = { name: "User", email: "" };
      }
      currentPage = "dashboard";

      try {
        // P0: Fetch ALL data in parallel instead of sequentially
        const [me, sub, groupsData, trial] = await Promise.all([
          ApiService.getMe(),
          ApiService.getSubscriptionStatus(),
          ApiService.listGroups(),
          ApiService.getTrialStatus().catch(() => null),
        ]);
        user = me;
        localStorage.setItem("user", JSON.stringify(me));
        subscription = sub;
        groups = groupsData.groups || [];
        trialAvailable = trial?.trial_available ?? false;
      } catch {
        // Token expired or invalid
        user = null;
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        currentPage = "landing";
      }
    }

    // Handle return from Pakasir payment redirect
    const params = new URLSearchParams(window.location.search);
    if (params.get("payment") === "success" && user) {
      currentPage = "dashboard";
      // Clean the URL
      window.history.replaceState({}, "", window.location.pathname);
    }
  });

  function handleLoginSuccess(userData) {
    user = userData;
    currentPage = "dashboard";

    // Fetch subscription and groups
    loadUserData();
  }

  async function loadUserData() {
    try {
      // P0: Parallel fetch all user data
      const [sub, groupsData, trial] = await Promise.all([
        ApiService.getSubscriptionStatus(),
        ApiService.listGroups(),
        ApiService.getTrialStatus().catch(() => null),
      ]);
      subscription = sub;
      groups = groupsData.groups || [];
      trialAvailable = trial?.trial_available ?? false;
    } catch (e) {
      console.error("Failed to load user data:", e);
    }
  }

  function handleLogout() {
    user = null;
    subscription = null;
    groups = [];
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    currentPage = "landing";
  }

  function handlePageChange(page) {
    if (page === "profile:upgrade" || page === "header:upgrade" || page === "trial:activate") {
      // Trigger the global upgrade modal immediately without navigating anywhere
      showGlobalUpgradeModal = true;
      // If we are on landing, login, etc., we probably still want to stay there
      // or we can let the user upgrade from within the dashboard context.
    } else {
      currentPage = page;
    }

    // Refresh data when navigating to certain pages
    if (page === "inventory" || page === "rooming") {
      loadUserData();
    }
  }

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
  }

  // Authenticated layout with sidebar
  let showSidebar = $derived(
    currentPage === "dashboard" ||
      currentPage === "scanner" ||
      currentPage === "profile" ||
      currentPage === "inventory" ||
      currentPage === "rooming" ||
      currentPage === "team" ||
      currentPage === "itinerary",
  );
</script>

<main class="min-h-screen flex flex-col">
  {#if currentPage === "landing"}
    <LandingPage
      onGoToLogin={() => (currentPage = "login")}
      onGoToRegister={() => (currentPage = "register")}
    />
  {:else if currentPage === "login" || currentPage === "register"}
    <Login
      initialMode={currentPage}
      onLoginSuccess={handleLoginSuccess}
      onBack={() => (currentPage = "landing")}
    />
  {:else if showSidebar}
    <!-- Layout with Sidebar -->
    <div class="flex min-h-screen">
      <Sidebar
        {currentPage}
        onPageChange={handlePageChange}
        {user}
        {isPro}
        {trialAvailable}
        onLogout={handleLogout}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      <!-- Main Content Area -->
      <div class="flex-1 lg:ml-0 pt-16 lg:pt-0">
        {#if currentPage === "dashboard"}
          <Dashboard
            {user}
            {subscription}
            onLogout={handleLogout}
            onSubscriptionChange={loadUserData}
            onNavigate={handlePageChange}
          />
        {:else if currentPage === "scanner"}
          <ScannerPage
            {user}
            {subscription}
            onLogout={handleLogout}
            onSubscriptionChange={loadUserData}
          />
        {:else if currentPage === "profile"}
          <ProfilePage
            onLogout={handleLogout}
            {user}
            {subscription}
            {trialAvailable}
            {groups}
            onUpgradeRequest={() => handlePageChange("header:upgrade")}
          />
        {:else if currentPage === "inventory"}
          {#if isPro}
            <InventoryPage
              isOpen={true}
              onClose={() => (currentPage = "dashboard")}
              {groups}
              {isPro}
            />
          {:else}
            <ProGateScreen
              featureName={proFeatures.inventory.name}
              featureDescription={proFeatures.inventory.desc}
              highlights={proFeatures.inventory.highlights}
              {trialAvailable}
              onUpgrade={() => handlePageChange("profile:upgrade")}
              onTrial={() => handlePageChange("profile:upgrade")}
            />
          {/if}
        {:else if currentPage === "rooming"}
          {#if isPro}
            <RoomingPage
              isOpen={true}
              onClose={() => (currentPage = "dashboard")}
              {groups}
              {isPro}
            />
          {:else}
            <ProGateScreen
              featureName={proFeatures.rooming.name}
              featureDescription={proFeatures.rooming.desc}
              highlights={proFeatures.rooming.highlights}
              {trialAvailable}
              onUpgrade={() => handlePageChange("profile:upgrade")}
              onTrial={() => handlePageChange("profile:upgrade")}
            />
          {/if}
        {:else if currentPage === "team"}
          {#if isPro}
            <TeamPage {isPro} />
          {:else}
            <ProGateScreen
              featureName={proFeatures.team.name}
              featureDescription={proFeatures.team.desc}
              highlights={proFeatures.team.highlights}
              {trialAvailable}
              onUpgrade={() => handlePageChange("profile:upgrade")}
              onTrial={() => handlePageChange("profile:upgrade")}
            />
          {/if}
        {:else if currentPage === "itinerary"}
          {#if isPro}
            <ItineraryPage {groups} {isPro} />
          {:else}
            <ProGateScreen
              featureName={proFeatures.itinerary.name}
              featureDescription={proFeatures.itinerary.desc}
              highlights={proFeatures.itinerary.highlights}
              {trialAvailable}
              onUpgrade={() => handlePageChange("profile:upgrade")}
              onTrial={() => handlePageChange("profile:upgrade")}
            />
          {/if}
        {/if}
      </div>
    </div>
  {:else if currentPage === "profile"}
    <!-- Fallback profile without sidebar -->
    <ProfilePage
      onLogout={handleLogout}
      {user}
      {subscription}
      {trialAvailable}
      {groups}
      onUpgradeRequest={() => handlePageChange("header:upgrade")}
    />
  {:else if currentPage === "mutawwif"}
    <!-- Public Mutawwif Manifest (no auth, no sidebar) -->
    <MutawwifManifest token={sharedToken} />
  {:else if currentPage === "registration"}
    <!-- Public Self-Service Registration (no auth, no sidebar) -->
    <PublicRegistrationPage token={registrationToken} />
  {/if}

  <!-- Global Upgrade Modal -->
  <UpgradeModal
    show={showGlobalUpgradeModal}
    onClose={() => (showGlobalUpgradeModal = false)}
    onSuccess={async (newSub) => {
      subscription = newSub;
      showGlobalUpgradeModal = false;
      await loadUserData();
    }}
  />
</main>
<Toast />

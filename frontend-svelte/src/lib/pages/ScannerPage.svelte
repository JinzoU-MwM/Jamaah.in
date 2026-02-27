<script>
  import { onMount, onDestroy } from "svelte";
  import {
    LogOut,
    Crown,
    X,
    Loader2,
    CheckCircle,
    ExternalLink,
  } from "lucide-svelte";
  import TableResult from "../components/TableResult.svelte";
  import FileUpload from "../components/FileUpload.svelte";
  import SubscriptionBanner from "../components/SubscriptionBanner.svelte";
  import GroupSelector from "../components/GroupSelector.svelte";
  import { ApiService } from "../services/api";

  let {
    onLogout,
    user = null,
    subscription = null,
    onSubscriptionChange = null,
  } = $props();

  // State
  let files = $state([]);
  let isProcessing = $state(false);
  let errorMessage = $state("");
  let progress = $state(null);
  // subscription comes from props, but we may need local state for it
  let localSubscription = $state(null);

  // Use prop if provided, otherwise use local state
  $effect(() => {
    if (subscription) {
      localSubscription = subscription;
    }
  });

  // Preview Modal State
  let showModal = $state(false);
  let previewData = $state([]);
  let isGenerating = $state(false);
  let validationWarnings = $state([]);
  let fileResults = $state([]);

  // Track failed files for retry
  let failedFileNames = $state([]);

  // Group State
  let selectedGroup = $state(null);
  let isSavingToGroup = $state(false);
  let groupSaveSuccess = $state("");

  // Upgrade modal
  let showUpgradeModal = $state(false);
  let paymentLoading = $state(false);
  let paymentOrderId = $state("");
  let paymentStatus = $state(""); // pending | paid | error
  let paymentError = $state("");
  let paymentPollInterval = null;
  let selectedPlan = $state("monthly"); // monthly | annual

  async function startPayment() {
    paymentLoading = true;
    paymentError = "";
    try {
      const result = await ApiService.createPaymentOrder(selectedPlan);
      paymentOrderId = result.order_id;
      paymentStatus = "pending";
      window.open(result.payment_url, "_blank");
      // Start polling for payment status
      paymentPollInterval = setInterval(async () => {
        try {
          const status = await ApiService.checkPaymentStatus(paymentOrderId);
          if (status.status === "paid") {
            paymentStatus = "paid";
            clearInterval(paymentPollInterval);
            localSubscription = await ApiService.getSubscriptionStatus();
          }
        } catch (e) {
          /* keep polling */
        }
      }, 5000);
    } catch (err) {
      paymentError = err.message;
      paymentStatus = "error";
    } finally {
      paymentLoading = false;
    }
  }

  function closeUpgradeModal() {
    showUpgradeModal = false;
    if (paymentPollInterval) clearInterval(paymentPollInterval);
    paymentStatus = "";
    paymentOrderId = "";
    paymentError = "";
  }

  onDestroy(() => {
    if (paymentPollInterval) clearInterval(paymentPollInterval);
  });

  // Fetch subscription status if not passed
  onMount(async () => {
    if (!localSubscription) {
      try {
        localSubscription = await ApiService.getSubscriptionStatus();
      } catch (e) {
        console.error("Failed to fetch subscription:", e);
      }
    }
  });

  function generateSessionId() {
    return Math.random().toString(36).substring(2, 10);
  }

  async function processDocuments(filesToProcess = null) {
    const uploadFiles = filesToProcess || files;
    if (uploadFiles.length === 0) return;

    isProcessing = true;
    errorMessage = "";
    failedFileNames = [];
    groupSaveSuccess = "";
    progress = {
      current: 0,
      total: uploadFiles.length,
      status: "starting",
      current_file: "",
      completed_files: [],
      failed_files: [],
    };

    const sessionId = generateSessionId();

    let eventSource = null;
    try {
      eventSource = ApiService.streamProgress(sessionId, (data) => {
        progress = { ...data };
      });
    } catch (e) {
      console.warn("SSE connection failed:", e);
    }

    try {
      const result = await ApiService.uploadDocuments(uploadFiles, sessionId);
      if (eventSource) eventSource.close();

      previewData = result.data;
      validationWarnings = result.validation_warnings || [];
      fileResults = result.file_results || [];
      failedFileNames = (result.file_results || [])
        .filter((fr) => fr.status === "failed")
        .map((fr) => fr.filename);
      showModal = true;

      // Refresh subscription (usage count changed)
      try {
        localSubscription = await ApiService.getSubscriptionStatus();
      } catch {}
    } catch (err) {
      if (eventSource) eventSource.close();
      errorMessage = err.message;
    } finally {
      isProcessing = false;
      progress = null;
    }
  }

  function retryFailed() {
    const retryFiles = files.filter((f) => failedFileNames.includes(f.name));
    if (retryFiles.length > 0) processDocuments(retryFiles);
  }

  async function generateExcel() {
    isGenerating = true;
    errorMessage = "";
    try {
      const blob = await ApiService.generateExcel(previewData);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = selectedGroup
        ? `${selectedGroup.name.replace(/\s+/g, "_")}.xlsx`
        : "jamaah_data.xlsx";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      showModal = false;
      files = [];
      previewData = [];
      validationWarnings = [];
      fileResults = [];
      failedFileNames = [];
    } catch (err) {
      errorMessage = err.message;
      showModal = false;
    } finally {
      isGenerating = false;
    }
  }

  async function saveToGroup() {
    if (!selectedGroup || previewData.length === 0) return;
    isSavingToGroup = true;
    errorMessage = "";
    try {
      await ApiService.addGroupMembers(selectedGroup.id, previewData);
      groupSaveSuccess = `${previewData.length} data berhasil disimpan ke grup "${selectedGroup.name}"`;
      // Update the group's member count in the selector
      selectedGroup = {
        ...selectedGroup,
        member_count: (selectedGroup.member_count || 0) + previewData.length,
      };
      showModal = false;
      files = [];
      previewData = [];
      validationWarnings = [];
      fileResults = [];
      failedFileNames = [];
      // Auto-dismiss success after 5 seconds
      setTimeout(() => (groupSaveSuccess = ""), 5000);
    } catch (err) {
      errorMessage = err.message;
    } finally {
      isSavingToGroup = false;
    }
  }

  async function viewGroupData(group) {
    errorMessage = "";
    try {
      const fullGroup = await ApiService.getGroup(group.id);
      previewData = fullGroup.members || [];
      validationWarnings = [];
      fileResults = [];
      showModal = true;
    } catch (err) {
      errorMessage = err.message;
    }
  }

  function closeModal() {
    showModal = false;
  }

  let isBlocked = $derived(localSubscription && !localSubscription.allowed);
</script>

<div class="bg-slate-50 min-h-screen lg:ml-0">
  <!-- Mobile Navbar (simplified - sidebar handles desktop nav) -->
  <nav
    class="border-b border-slate-200 bg-white/80 backdrop-blur-sm px-3 sm:px-6 py-3 sm:py-4 flex justify-between items-center sticky top-0 z-10 lg:hidden"
  >
    <div class="text-sm font-semibold text-slate-800">Dashboard</div>
    <div class="text-xs text-slate-400">OCR Ekstrak Data</div>
  </nav>

  <!-- Welcome Header -->
  <div
    class="bg-gradient-to-br from-emerald-600 via-emerald-500 to-teal-500 text-white"
  >
    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-lg sm:text-2xl font-bold mb-1">
            Selamat datang{user?.full_name ? `, ${user.full_name}` : ""} 👋
          </h1>
          <p class="text-emerald-100 text-sm sm:text-base">
            Upload dan ekstrak data jamaah dengan AI
          </p>
        </div>
        {#if localSubscription?.plan === "pro"}
          <div
            class="hidden sm:flex items-center gap-2 bg-white/15 backdrop-blur-sm px-3 py-1.5 rounded-full"
          >
            <Crown class="h-4 w-4 text-yellow-300" />
            <span class="text-sm font-medium">Pro</span>
          </div>
        {/if}
      </div>
    </div>
  </div>

  <!-- Subscription Banner -->
  <SubscriptionBanner
    subscription={localSubscription}
    onUpgrade={() => (showUpgradeModal = true)}
  />

  <!-- Main Content -->
  {#if isBlocked}
    <div class="max-w-5xl mx-auto px-4 sm:px-6 py-10 sm:py-16 text-center">
      <div
        class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 sm:p-12"
      >
        <div class="text-5xl sm:text-6xl mb-4">🔒</div>
        <h2 class="text-lg sm:text-xl font-bold text-slate-800 mb-2">
          Akses Terbatas
        </h2>
        <p class="text-slate-500 mb-6 text-sm sm:text-base">
          Batas penggunaan gratis telah tercapai. Upgrade ke Pro untuk
          melanjutkan.
        </p>
        <button
          onclick={() => (showUpgradeModal = true)}
          class="px-6 py-3 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2 mx-auto"
        >
          <Crown class="h-5 w-5" />
          Upgrade ke Pro — Rp99.000/bulan
        </button>
      </div>
    </div>
  {:else}
    <!-- Group Selector -->
    <div class="max-w-5xl mx-auto px-4 sm:px-6 mt-4 sm:mt-6">
      <GroupSelector
        bind:selectedGroup
        onGroupSelect={(g) => (selectedGroup = g)}
        onViewGroup={viewGroupData}
        isPro={localSubscription?.plan === "pro" &&
          localSubscription?.status === "active"}
      />
    </div>

    <!-- Success Banner -->
    {#if groupSaveSuccess}
      <div class="max-w-5xl mx-auto px-4 sm:px-6 mb-4">
        <div
          class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 flex items-center gap-3"
        >
          <CheckCircle class="h-5 w-5 text-emerald-500 flex-shrink-0" />
          <span class="text-sm text-emerald-700">{groupSaveSuccess}</span>
        </div>
      </div>
    {/if}

    <FileUpload
      bind:files
      {isProcessing}
      {errorMessage}
      onProcess={() => processDocuments()}
      {progress}
    />
  {/if}

  <!-- Retry Banner -->
  {#if failedFileNames.length > 0 && !isProcessing && !showModal}
    <div class="max-w-5xl mx-auto px-4 sm:px-6 mt-4">
      <div
        class="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between"
      >
        <div class="flex items-center gap-2">
          <span class="text-red-500 text-lg">⚠️</span>
          <span class="text-sm text-red-700">
            <strong>{failedFileNames.length}</strong> file gagal: {failedFileNames.join(
              ", ",
            )}
          </span>
        </div>
        <button
          onclick={retryFailed}
          class="px-4 py-1.5 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors"
        >
          🔄 Coba Lagi
        </button>
      </div>
    </div>
  {/if}
</div>

<!-- Preview Modal -->
<TableResult
  isOpen={showModal}
  bind:data={previewData}
  {isGenerating}
  onClose={closeModal}
  onSave={generateExcel}
  onSaveToGroup={selectedGroup ? saveToGroup : null}
  {isSavingToGroup}
  groupName={selectedGroup?.name || ""}
  onUpgrade={() => {
    showModal = false;
    showUpgradeModal = true;
  }}
  readOnly={localSubscription?.plan !== "pro"}
  {validationWarnings}
  {fileResults}
/>

<!-- Upgrade Modal -->
{#if showUpgradeModal}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
  <div
    class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    onclick={closeUpgradeModal}
    role="button"
    tabindex="-1"
    aria-label="Tutup modal"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
      onclick={(e) => e.stopPropagation()}
      role="dialog"
      aria-modal="true"
      aria-labelledby="upgrade-title"
      tabindex="-1"
    >
      <div class="flex justify-between items-center mb-4">
        <div class="flex items-center gap-2">
          <Crown class="h-5 w-5 text-emerald-500" />
          <h3 class="font-bold text-lg text-slate-800">Upgrade ke Pro</h3>
        </div>
        <button
          onclick={closeUpgradeModal}
          class="text-slate-400 hover:text-slate-600"
          aria-label="Close"
        >
          <X class="h-5 w-5" />
        </button>
      </div>

      {#if paymentStatus === "paid"}
        <div class="text-center py-6">
          <div
            class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4"
          >
            <CheckCircle class="h-8 w-8 text-emerald-500" />
          </div>
          <h4 class="text-lg font-bold text-slate-800 mb-1">
            Pembayaran Berhasil!
          </h4>
          <p class="text-sm text-slate-500">
            Langganan Pro aktif selama 30 hari.
          </p>
          <button
            onclick={closeUpgradeModal}
            class="mt-4 w-full bg-emerald-500 hover:bg-emerald-600 text-white font-semibold py-3 rounded-xl transition-all"
          >
            Mulai Menggunakan Pro
          </button>
        </div>
      {:else}
        <!-- Plan Toggle -->
        <div class="flex bg-slate-100 rounded-xl p-1 mb-4">
          <button
            type="button"
            onclick={() => (selectedPlan = "monthly")}
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all {selectedPlan ===
            'monthly'
              ? 'bg-white shadow text-slate-800'
              : 'text-slate-500 hover:text-slate-700'}">Bulanan</button
          >
          <button
            type="button"
            onclick={() => (selectedPlan = "annual")}
            class="flex-1 py-2 text-sm font-medium rounded-lg transition-all relative {selectedPlan ===
            'annual'
              ? 'bg-white shadow text-slate-800'
              : 'text-slate-500 hover:text-slate-700'}"
          >
            Tahunan
            <span
              class="absolute -top-2 -right-1 text-[10px] bg-emerald-500 text-white px-1.5 py-0.5 rounded-full font-bold"
              >HEMAT</span
            >
          </button>
        </div>

        <div
          class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-4"
        >
          {#if selectedPlan === "annual"}
            <p class="text-2xl font-bold text-emerald-700">
              Rp 990.000<span class="text-sm font-normal text-emerald-500">
                / tahun</span
              >
            </p>
            <p class="text-sm text-emerald-600 mt-1">
              Hemat Rp 198.000 — setara Rp 82.500/bulan
            </p>
          {:else}
            <p class="text-2xl font-bold text-emerald-700">
              Rp 99.000<span class="text-sm font-normal text-emerald-500">
                / bulan</span
              >
            </p>
            <p class="text-sm text-emerald-600 mt-1">
              Unlimited scan dokumen, prioritas support
            </p>
          {/if}
        </div>

        <div class="space-y-2 mb-5">
          <div class="flex items-center gap-2 text-sm text-slate-600">
            <CheckCircle class="h-4 w-4 text-emerald-500 flex-shrink-0" /> Unlimited
            scan dokumen
          </div>
          <div class="flex items-center gap-2 text-sm text-slate-600">
            <CheckCircle class="h-4 w-4 text-emerald-500 flex-shrink-0" /> Unlimited
            grup jamaah
          </div>
          <div class="flex items-center gap-2 text-sm text-slate-600">
            <CheckCircle class="h-4 w-4 text-emerald-500 flex-shrink-0" /> Export
            Excel
          </div>
          <div class="flex items-center gap-2 text-sm text-slate-600">
            <CheckCircle class="h-4 w-4 text-emerald-500 flex-shrink-0" /> Prioritas
            support
          </div>
        </div>

        {#if paymentError}
          <div
            class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
          >
            {paymentError}
          </div>
        {/if}

        {#if paymentStatus === "pending"}
          <div
            class="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4 text-center"
          >
            <Loader2 class="h-5 w-5 animate-spin text-amber-500 mx-auto mb-2" />
            <p class="text-sm font-medium text-amber-700">
              Menunggu pembayaran...
            </p>
            <p class="text-xs text-amber-500 mt-1">
              Selesaikan pembayaran di tab yang terbuka
            </p>
          </div>
          <button
            onclick={async () => {
              try {
                const s = await ApiService.checkPaymentStatus(paymentOrderId);
                if (s.status === "paid") {
                  paymentStatus = "paid";
                  clearInterval(paymentPollInterval);
                  localSubscription = await ApiService.getSubscriptionStatus();
                }
              } catch (e) {}
            }}
            class="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
          >
            Cek Status Pembayaran
          </button>
        {:else}
          <button
            onclick={startPayment}
            disabled={paymentLoading}
            class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
          >
            {#if paymentLoading}
              <Loader2 class="h-5 w-5 animate-spin" /> Memproses...
            {:else}
              <ExternalLink class="h-5 w-5" /> Bayar Sekarang
            {/if}
          </button>
        {/if}

        <p class="text-xs text-slate-400 text-center mt-3">
          Pembayaran diproses oleh Pakasir (QRIS / VA / PayPal)
        </p>
      {/if}
    </div>
  </div>
{/if}

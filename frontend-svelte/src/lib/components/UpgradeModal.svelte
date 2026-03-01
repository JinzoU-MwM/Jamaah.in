<script>
    import { onMount, onDestroy } from "svelte";
    import { Crown, CheckCircle, Loader2 } from "lucide-svelte";
    import { ApiService } from "../services/api";

    let { show = false, onClose, onSuccess } = $props();

    // Upgrade
    let selectedPlan = $state("monthly"); // monthly | annual
    let paymentLoading = $state(false);
    let paymentOrderId = $state("");
    let paymentStatus = $state("");
    let paymentError = $state("");
    let paymentPollInterval = null;

    // Pro Trial
    let trialStatus = $state(null);
    let showPhoneModal = $state(false);
    let phoneNumber = $state("");
    let phoneOtp = $state("");
    let phoneOtpSent = $state(false);
    let phoneLoading = $state(false);
    let phoneError = $state("");

    $effect(() => {
        if (show && !trialStatus) {
            loadTrialStatus();
        }
    });

    async function loadTrialStatus() {
        try {
            trialStatus = await ApiService.getTrialStatus();
        } catch (e) {
            console.error("Failed to load trial status:", e);
        }
    }

    async function sendPhoneOtp() {
        phoneLoading = true;
        phoneError = "";
        try {
            await ApiService.sendPhoneOtp(phoneNumber);
            phoneOtpSent = true;
        } catch (err) {
            phoneError = err.message;
        } finally {
            phoneLoading = false;
        }
    }

    async function verifyPhoneAndActivateTrial() {
        phoneLoading = true;
        phoneError = "";
        try {
            await ApiService.verifyPhone(phoneNumber, phoneOtp);
            await ApiService.activateProTrial();
            showPhoneModal = false;
            if (onSuccess) {
                const sub = await ApiService.getSubscriptionStatus();
                onSuccess(sub);
            }
            trialStatus = { can_activate: false, trial_used: true };
            onClose();
        } catch (err) {
            phoneError = err.message;
        } finally {
            phoneLoading = false;
        }
    }

    async function activateTrial() {
        if (!trialStatus) await loadTrialStatus();
        if (trialStatus?.phone_verified) {
            // Phone already verified, activate directly
            phoneLoading = true;
            try {
                await ApiService.activateProTrial();
                if (onSuccess) {
                    const sub = await ApiService.getSubscriptionStatus();
                    onSuccess(sub);
                }
                trialStatus = { can_activate: false, trial_used: true };
                onClose();
            } catch (err) {
                paymentError = err.message;
            } finally {
                phoneLoading = false;
            }
        } else {
            // Need to verify phone first
            showPhoneModal = true;
        }
    }

    async function startPayment(planType = "monthly") {
        paymentLoading = true;
        paymentError = "";
        try {
            const result = await ApiService.createPaymentOrder(planType);
            paymentOrderId = result.order_id;
            paymentStatus = "pending";
            window.open(result.payment_url, "_blank");
            paymentPollInterval = setInterval(async () => {
                try {
                    const st =
                        await ApiService.checkPaymentStatus(paymentOrderId);
                    if (st.status === "paid") {
                        paymentStatus = "paid";
                        clearInterval(paymentPollInterval);
                        if (onSuccess) {
                            const sub =
                                await ApiService.getSubscriptionStatus();
                            onSuccess(sub);
                        }
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
        if (paymentPollInterval) clearInterval(paymentPollInterval);
        paymentStatus = "";
        paymentOrderId = "";
        paymentError = "";
        onClose();
    }

    onDestroy(() => {
        if (paymentPollInterval) clearInterval(paymentPollInterval);
    });
</script>

{#if show}
    <!-- Upgrade Modal -->
    {#if !showPhoneModal}
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
            class="modal-overlay"
            onclick={closeUpgradeModal}
            onkeydown={(e) => {
                if (e.key === "Escape") closeUpgradeModal();
            }}
            role="dialog"
            aria-modal="true"
            tabindex="-1"
        >
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
                class="modal-content"
                onclick={(e) => e.stopPropagation()}
                onkeydown={() => {}}
            >
                <div class="modal-header">
                    <h3 class="modal-title">
                        <Crown class="h-5 w-5 text-emerald-500" />
                        Upgrade ke Pro
                    </h3>
                    <button onclick={closeUpgradeModal} class="modal-close"
                        >✕</button
                    >
                </div>

                <div class="modal-body">
                    {#if paymentStatus === "paid"}
                        <div style="text-align: center; padding: 24px 0;">
                            <div
                                style="width: 64px; height: 64px; background: #d1fae5; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;"
                            >
                                <CheckCircle class="h-8 w-8 text-emerald-500" />
                            </div>
                            <h4
                                style="font-size: 18px; font-weight: 700; color: #1e293b; margin-bottom: 4px;"
                            >
                                Pembayaran Berhasil!
                            </h4>
                            <p style="font-size: 14px; color: #64748b;">
                                Langganan Pro aktif selama 30 hari.
                            </p>
                            <button
                                onclick={closeUpgradeModal}
                                class="wa-confirm-btn"
                                style="margin-top: 16px; background: #10b981;"
                            >
                                Mulai Menggunakan Pro
                            </button>
                        </div>
                    {:else}
                        <!-- Plan Toggle -->
                        <div
                            style="display: flex; background: #f1f5f9; border-radius: 12px; padding: 4px; margin-bottom: 16px;"
                        >
                            <button
                                type="button"
                                onclick={() => (selectedPlan = "monthly")}
                                style="flex: 1; padding: 8px 12px; font-size: 13px; font-weight: 500; border-radius: 8px; transition: all 0.2s; {selectedPlan ===
                                'monthly'
                                    ? 'background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: #1e293b;'
                                    : 'color: #64748b;'}">Bulanan</button
                            >
                            <button
                                type="button"
                                onclick={() => (selectedPlan = "annual")}
                                style="flex: 1; padding: 8px 12px; font-size: 13px; font-weight: 500; border-radius: 8px; transition: all 0.2s; position: relative; {selectedPlan ===
                                'annual'
                                    ? 'background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); color: #1e293b;'
                                    : 'color: #64748b;'}"
                            >
                                Tahunan
                                <span
                                    style="position: absolute; top: -8px; right: -4px; font-size: 10px; background: #10b981; color: white; padding: 2px 6px; border-radius: 999px; font-weight: 700;"
                                    >HEMAT</span
                                >
                            </button>
                        </div>

                        <div class="price-box">
                            {#if selectedPlan === "annual"}
                                <p class="price-amount">Rp 800.000</p>
                                <p class="price-period">per tahun</p>
                                <p class="price-alt">
                                    Hemat Rp 160.000 (Rp 66.700/bulan)
                                </p>
                            {:else}
                                <p class="price-amount">Rp 80.000</p>
                                <p class="price-period">per bulan</p>
                                <p class="price-alt">
                                    atau Rp 800.000/tahun (hemat 17%)
                                </p>
                            {/if}
                        </div>

                        <ul class="feature-list">
                            <li>
                                <CheckCircle class="h-4 w-4 text-emerald-500" />
                                Unlimited scan dokumen
                            </li>
                            <li>
                                <CheckCircle class="h-4 w-4 text-emerald-500" />
                                Unlimited grup jamaah
                            </li>
                            <li>
                                <CheckCircle class="h-4 w-4 text-emerald-500" />
                                Export Excel
                            </li>
                            <li>
                                <CheckCircle class="h-4 w-4 text-emerald-500" />
                                Prioritas support
                            </li>
                        </ul>

                        {#if paymentError}
                            <div
                                style="background: #fef2f2; color: #dc2626; padding: 12px; border-radius: 8px; margin-bottom: 16px; text-align: center; font-size: 14px; border: 1px solid #fecaca;"
                            >
                                {paymentError}
                            </div>
                        {/if}

                        {#if paymentStatus === "pending"}
                            <div
                                style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 12px; margin-bottom: 16px; text-align: center;"
                            >
                                <Loader2
                                    class="h-5 w-5 animate-spin text-amber-500"
                                    style="margin: 0 auto 8px;"
                                />
                                <p
                                    style="font-size: 14px; font-weight: 600; color: #b45309;"
                                >
                                    Menunggu pembayaran...
                                </p>
                                <p
                                    style="font-size: 12px; color: #d97706; margin-top: 4px;"
                                >
                                    Selesaikan pembayaran di tab yang terbuka
                                </p>
                            </div>
                            <button
                                onclick={async () => {
                                    try {
                                        const s =
                                            await ApiService.checkPaymentStatus(
                                                paymentOrderId,
                                            );
                                        if (s.status === "paid") {
                                            paymentStatus = "paid";
                                            clearInterval(paymentPollInterval);
                                            if (onSuccess) {
                                                const sub =
                                                    await ApiService.getSubscriptionStatus();
                                                onSuccess(sub);
                                            }
                                        }
                                    } catch (e) {}
                                }}
                                class="wa-confirm-btn"
                                style="background: #f59e0b;"
                            >
                                Cek Status Pembayaran
                            </button>
                        {:else}
                            <!-- Pro Trial Button -->
                            {#if trialStatus?.trial_available}
                                <button
                                    onclick={activateTrial}
                                    disabled={phoneLoading}
                                    class="wa-confirm-btn"
                                    style="background: #8b5cf6; margin-bottom: 12px;"
                                >
                                    {#if phoneLoading}
                                        <Loader2 class="h-4 w-4 animate-spin" />
                                        Memproses...
                                    {:else}
                                        🎁 Coba Pro 7 Hari GRATIS
                                    {/if}
                                </button>
                                <p
                                    style="font-size: 12px; color: #6b7280; text-align: center; margin-bottom: 12px;"
                                >
                                    Tanpa kartu kredit, batalkan kapan saja
                                </p>
                            {/if}
                            <button
                                onclick={() => startPayment(selectedPlan)}
                                disabled={paymentLoading}
                                class="wa-confirm-btn"
                            >
                                {#if paymentLoading}
                                    <Loader2 class="h-4 w-4 animate-spin" />
                                    Memproses...
                                {:else}
                                    {selectedPlan === "annual"
                                        ? "Bayar Rp 800.000/tahun"
                                        : "Bayar Rp 80.000/bulan"}
                                {/if}
                            </button>
                        {/if}

                        <p
                            style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 12px;"
                        >
                            Pembayaran diproses oleh Pakasir (QRIS / VA /
                            PayPal)
                        </p>
                    {/if}
                </div>
            </div>
        </div>
    {/if}

    <!-- Phone Verification Modal for Pro Trial -->
    {#if showPhoneModal}
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
            class="modal-overlay"
            onclick={() => {
                showPhoneModal = false;
                phoneOtpSent = false;
                phoneError = "";
            }}
            onkeydown={(e) => {
                if (e.key === "Escape") {
                    showPhoneModal = false;
                    phoneOtpSent = false;
                    phoneError = "";
                }
            }}
            role="dialog"
            aria-modal="true"
            tabindex="-1"
        >
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div
                class="modal-content"
                onclick={(e) => e.stopPropagation()}
                onkeydown={() => {}}
            >
                <div class="modal-header">
                    <h3 class="modal-title">
                        <Crown class="h-5 w-5 text-purple-500" />
                        Verifikasi WhatsApp
                    </h3>
                    <button
                        onclick={() => {
                            showPhoneModal = false;
                            phoneOtpSent = false;
                            phoneError = "";
                        }}
                        class="modal-close">✕</button
                    >
                </div>

                <div class="modal-body">
                    <p
                        style="font-size: 14px; color: #64748b; margin-bottom: 16px;"
                    >
                        Verifikasi nomor WhatsApp Anda untuk mengaktifkan Pro
                        Trial 7 hari gratis.
                    </p>

                    {#if !phoneOtpSent}
                        <div style="margin-bottom: 16px;">
                            <label
                                for="phone-number"
                                style="font-size: 13px; font-weight: 500; color: #374151; display: block; margin-bottom: 6px;"
                            >
                                Nomor WhatsApp
                            </label>
                            <input
                                id="phone-number"
                                type="tel"
                                bind:value={phoneNumber}
                                placeholder="08xxxxxxxxxx"
                                style="width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px;"
                            />
                        </div>
                    {:else}
                        <div style="margin-bottom: 16px;">
                            <label
                                for="phone-otp"
                                style="font-size: 13px; font-weight: 500; color: #374151; display: block; margin-bottom: 6px;"
                            >
                                Kode OTP (dikirim ke WhatsApp)
                            </label>
                            <input
                                id="phone-otp"
                                type="text"
                                bind:value={phoneOtp}
                                placeholder="123456"
                                maxlength="6"
                                style="width: 100%; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 14px; text-align: center; letter-spacing: 4px;"
                            />
                        </div>
                    {/if}

                    {#if phoneError}
                        <div
                            style="background: #fef2f2; color: #dc2626; padding: 10px; border-radius: 8px; margin-bottom: 16px; text-align: center; font-size: 13px;"
                        >
                            {phoneError}
                        </div>
                    {/if}

                    {#if !phoneOtpSent}
                        <button
                            onclick={sendPhoneOtp}
                            disabled={phoneLoading || !phoneNumber}
                            class="wa-confirm-btn"
                            style="background: #25d366;"
                        >
                            {#if phoneLoading}
                                <Loader2 class="h-4 w-4 animate-spin" />
                                Mengirim...
                            {:else}
                                Kirim Kode OTP
                            {/if}
                        </button>
                    {:else}
                        <button
                            onclick={verifyPhoneAndActivateTrial}
                            disabled={phoneLoading || phoneOtp.length < 6}
                            class="wa-confirm-btn"
                            style="background: #8b5cf6;"
                        >
                            {#if phoneLoading}
                                <Loader2 class="h-4 w-4 animate-spin" />
                                Memverifikasi...
                            {:else}
                                Verifikasi & Aktifkan Pro Trial
                            {/if}
                        </button>
                    {/if}
                </div>
            </div>
        </div>
    {/if}
{/if}

<style>
    /* ---- Modals ---- */
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999; /* Ensure high z-index for global display */
        padding: 1rem;
    }
    .modal-content {
        background: #fff;
        border-radius: 1rem;
        width: 100%;
        max-width: 24rem;
        overflow: hidden;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    }
    :global(.dark) .modal-content {
        background: #1e293b;
    }
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid #f1f5f9;
    }
    :global(.dark) .modal-header {
        border-color: #334155;
    }
    .modal-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
    }
    :global(.dark) .modal-title {
        color: #f1f5f9;
    }
    .modal-close {
        background: none;
        border: none;
        color: #94a3b8;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0.25rem;
    }
    .modal-body {
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    /* ---- Upgrade Modal ---- */
    .price-box {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #d1fae5, #cffafe);
        border-radius: 0.75rem;
    }
    :global(.dark) .price-box {
        background: linear-gradient(135deg, #064e3b, #083344);
    }
    .price-amount {
        font-size: 1.75rem;
        font-weight: 700;
        color: #059669;
    }
    :global(.dark) .price-amount {
        color: #6ee7b7;
    }
    .price-period {
        font-size: 0.8rem;
        color: #64748b;
    }
    .price-alt {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    .feature-list {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    .feature-list li {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.85rem;
        color: #1e293b;
    }
    :global(.dark) .feature-list li {
        color: #e2e8f0;
    }
    .wa-confirm-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.75rem;
        background: #22c55e;
        color: white;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 0.75rem;
        text-decoration: none;
        border: none;
        cursor: pointer;
        transition: background 0.2s;
    }
    .wa-confirm-btn:hover {
        background: #16a34a;
    }
    .wa-confirm-btn:disabled {
        opacity: 0.6;
        cursor: not-allowed;
    }
</style>

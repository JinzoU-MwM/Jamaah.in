<!--
  ProGateScreen.svelte — Beautiful upsell landing page for Pro-only features.
  Shown to Free users when they click a Pro-only menu item in the sidebar.
-->
<script>
    import { Crown, Lock, Check, Sparkles, Loader2 } from "lucide-svelte";

    let {
        featureName = "Fitur Pro",
        featureDescription = "Fitur ini tersedia khusus untuk pengguna Pro.",
        featureIcon = null,
        highlights = [],
        onUpgrade,
        onTrial,
        trialAvailable = false,
        trialLoading = false,
    } = $props();
</script>

<div class="gate-container">
    <div class="gate-card">
        <!-- Lock icon -->
        <div class="gate-lock">
            <div class="gate-lock-ring">
                <Lock class="h-8 w-8 text-slate-400" />
            </div>
        </div>

        <!-- Feature name -->
        <div class="gate-badge">
            <Crown class="h-3.5 w-3.5" />
            <span>Fitur PRO</span>
        </div>

        <h1 class="gate-title">{featureName}</h1>
        <p class="gate-desc">{featureDescription}</p>

        <!-- Highlights -->
        {#if highlights.length > 0}
            <div class="gate-highlights">
                {#each highlights as item}
                    <div class="gate-highlight-item">
                        <div class="gate-check">
                            <Check class="h-3.5 w-3.5 text-emerald-600" />
                        </div>
                        <span>{item}</span>
                    </div>
                {/each}
            </div>
        {/if}

        <!-- CTAs -->
        <div class="gate-actions">
            {#if trialAvailable}
                <button
                    type="button"
                    onclick={onTrial}
                    disabled={trialLoading}
                    class="gate-btn-trial"
                >
                    {#if trialLoading}
                        <Loader2 class="h-4 w-4 animate-spin" />
                        Memproses...
                    {:else}
                        <Sparkles class="h-4 w-4" />
                        Coba GRATIS 7 Hari
                    {/if}
                </button>
                <p class="gate-trial-note">
                    Tanpa kartu kredit · Batalkan kapan saja
                </p>
            {/if}

            <button type="button" onclick={onUpgrade} class="gate-btn-upgrade">
                <Crown class="h-4 w-4" />
                Upgrade ke Pro — Rp 80.000/bulan
            </button>
        </div>
    </div>
</div>

<style>
    .gate-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 80vh;
        padding: 2rem;
        background: linear-gradient(
            135deg,
            #f0fdf4 0%,
            #ecfeff 50%,
            #f0f9ff 100%
        );
    }

    .gate-card {
        max-width: 480px;
        width: 100%;
        background: white;
        border-radius: 1.25rem;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow:
            0 4px 6px -1px rgba(0, 0, 0, 0.04),
            0 20px 40px -8px rgba(0, 0, 0, 0.06);
        border: 1px solid #e2e8f0;
    }

    .gate-lock {
        display: flex;
        justify-content: center;
        margin-bottom: 1.25rem;
    }

    .gate-lock-ring {
        width: 64px;
        height: 64px;
        border-radius: 50%;
        background: linear-gradient(135deg, #f1f5f9, #e2e8f0);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }

    .gate-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.375rem;
        background: linear-gradient(135deg, #fef3c7, #fde68a);
        color: #92400e;
        font-size: 0.6875rem;
        font-weight: 700;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        margin-bottom: 1rem;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .gate-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }

    .gate-desc {
        font-size: 0.9375rem;
        color: #64748b;
        line-height: 1.6;
        margin-bottom: 1.5rem;
        max-width: 380px;
        margin-left: auto;
        margin-right: auto;
    }

    .gate-highlights {
        display: flex;
        flex-direction: column;
        gap: 0.625rem;
        text-align: left;
        margin-bottom: 1.75rem;
        padding: 1rem 1.25rem;
        background: #f8fafc;
        border-radius: 0.75rem;
        border: 1px solid #f1f5f9;
    }

    .gate-highlight-item {
        display: flex;
        align-items: center;
        gap: 0.625rem;
        font-size: 0.8125rem;
        color: #334155;
        line-height: 1.5;
    }

    .gate-check {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: #ecfdf5;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .gate-actions {
        display: flex;
        flex-direction: column;
        gap: 0.625rem;
        align-items: center;
    }

    .gate-btn-trial {
        width: 100%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 0.9375rem;
        font-weight: 700;
        color: white;
        background: linear-gradient(135deg, #8b5cf6, #6d28d9);
        border: none;
        border-radius: 0.625rem;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
    }

    .gate-btn-trial:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
    }

    .gate-btn-trial:disabled {
        opacity: 0.7;
        cursor: not-allowed;
        transform: none;
    }

    .gate-trial-note {
        font-size: 0.6875rem;
        color: #94a3b8;
        margin-bottom: 0.25rem;
    }

    .gate-btn-upgrade {
        width: 100%;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-size: 0.875rem;
        font-weight: 600;
        color: #059669;
        background: white;
        border: 2px solid #a7f3d0;
        border-radius: 0.625rem;
        cursor: pointer;
        transition: all 0.2s;
    }

    .gate-btn-upgrade:hover {
        background: #ecfdf5;
        border-color: #6ee7b7;
        transform: translateY(-1px);
    }
</style>

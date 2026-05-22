<script>
    import {
        AlertTriangle,
        Crown,
        Clock,
        Zap,
        ChevronRight,
    } from "lucide-svelte";

    let { subscription = null, onUpgrade } = $props();

    // Derive states
    let isFree = $derived(subscription?.plan === "free");
    let isExpired = $derived(subscription?.status === "expired");
    let isTrial = $derived(subscription?.status === "trial");
    let usagePercent = $derived(
        subscription?.usage_limit
            ? Math.min(
                  100,
                  Math.round(
                      (subscription.usage_count / subscription.usage_limit) *
                          100,
                  ),
              )
            : 0,
    );
    let remaining = $derived(
        subscription?.usage_limit
            ? Math.max(0, subscription.usage_limit - subscription.usage_count)
            : null,
    );
    let trialEndsFormatted = $derived(() => {
        if (!subscription?.trial_ends) return "";
        const d = new Date(subscription.trial_ends);
        return d.toLocaleDateString("id-ID", {
            day: "numeric",
            month: "long",
            year: "numeric",
        });
    });
    let isBlocked = $derived(!subscription?.allowed);
</script>

{#if subscription && isFree}
    <div class="w-full">
        <!-- Blocked: Usage limit or trial expired -->
        {#if isBlocked}
            <div
                class="rounded-3xl border border-red-100 bg-white p-5 shadow-sm"
            >
                <div class="flex items-start gap-3">
                    <div class="bg-red-100 rounded-lg p-2 shrink-0">
                        <AlertTriangle class="h-5 w-5 text-red-500" />
                    </div>
                    <div class="flex-1">
                        <p class="font-semibold text-red-800 text-sm">
                            {subscription.message}
                        </p>
                        <p class="text-xs text-red-600 mt-1">
                            Upgrade ke Pro untuk akses unlimited scan dokumen.
                        </p>
                    </div>
                    <button
                        onclick={onUpgrade}
                        class="flex shrink-0 items-center gap-1 rounded-xl bg-gradient-to-r from-primary-600 to-primary-500 px-4 py-2 text-sm font-semibold text-white shadow-lg shadow-primary-500/20 transition-all hover:-translate-y-0.5"
                    >
                        <Crown class="h-4 w-4" />
                        Upgrade Pro
                        <ChevronRight class="h-4 w-4" />
                    </button>
                </div>
            </div>

            <!-- Trial active -->
        {:else if isTrial}
            <div
                class="rounded-3xl border border-primary-100 bg-white p-4 shadow-sm"
            >
                <div class="flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <div class="bg-blue-100 rounded-lg p-2">
                            <Clock class="h-4 w-4 text-blue-500" />
                        </div>
                        <div>
                            <p class="text-sm font-medium text-blue-800">
                                Trial Gratis - Berakhir {trialEndsFormatted()}
                            </p>
                            <p class="text-xs text-blue-600">
                                {remaining} scan tersisa dari {subscription.usage_limit}
                            </p>
                        </div>
                    </div>
                    <!-- Usage Bar -->
                    <div class="flex items-center gap-3">
                        <div
                            class="w-32 h-2 bg-blue-100 rounded-full overflow-hidden"
                        >
                            <div
                                class="h-full rounded-full transition-all duration-500 {usagePercent >
                                80
                                    ? 'bg-red-400'
                                    : usagePercent > 50
                                      ? 'bg-amber-400'
                                      : 'bg-blue-400'}"
                                style="width: {usagePercent}%"
                            ></div>
                        </div>
                        <span class="text-xs text-blue-600 font-mono"
                            >{subscription.usage_count}/{subscription.usage_limit}</span
                        >
                    </div>
                </div>
            </div>

            <!-- Free (trial expired but still has uses) -->
        {:else if isExpired && remaining > 0}
            <div
                class="rounded-3xl border border-amber-100 bg-white p-4 shadow-sm"
            >
                <div class="flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <div class="bg-amber-100 rounded-lg p-2">
                            <Zap class="h-4 w-4 text-amber-500" />
                        </div>
                        <div>
                            <p class="text-sm font-medium text-amber-800">
                                Trial berakhir - {remaining} scan tersisa
                            </p>
                            <p class="text-xs text-amber-600">
                                Upgrade ke Pro untuk akses unlimited
                            </p>
                        </div>
                    </div>
                    <button
                        onclick={onUpgrade}
                        class="px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white text-xs font-semibold rounded-lg transition-all flex items-center gap-1"
                    >
                        <Crown class="h-3.5 w-3.5" />
                        Upgrade
                    </button>
                </div>
            </div>
        {/if}
    </div>
{/if}

{#if subscription && subscription.plan === "pro"}
    <div class="w-full">
        <div
            class="rounded-3xl border border-primary-100 bg-white p-4 shadow-sm"
        >
            <div class="flex items-center gap-3">
                <div class="rounded-2xl bg-primary-50 p-2">
                    <Crown class="h-4 w-4 text-primary-600" />
                </div>
                <div>
                    <p class="text-sm font-semibold text-slate-900">
                        Pro Plan - Unlimited Scan
                    </p>
                    <p class="text-xs text-slate-500">
                        Total {subscription.usage_count} dokumen di-scan
                    </p>
                </div>
            </div>
        </div>
    </div>
{/if}

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
    <div class="max-w-5xl mx-auto px-6 mt-4">
        <!-- Blocked: Usage limit or trial expired -->
        {#if isBlocked}
            <div
                class="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-xl p-5"
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
                        class="px-4 py-2 bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white text-sm font-semibold rounded-lg transition-all shadow-md hover:shadow-lg flex items-center gap-1 shrink-0"
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
                class="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4"
            >
                <div class="flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <div class="bg-blue-100 rounded-lg p-2">
                            <Clock class="h-4 w-4 text-blue-500" />
                        </div>
                        <div>
                            <p class="text-sm font-medium text-blue-800">
                                Trial Gratis · Berakhir {trialEndsFormatted()}
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
                class="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-4"
            >
                <div class="flex items-center justify-between flex-wrap gap-3">
                    <div class="flex items-center gap-3">
                        <div class="bg-amber-100 rounded-lg p-2">
                            <Zap class="h-4 w-4 text-amber-500" />
                        </div>
                        <div>
                            <p class="text-sm font-medium text-amber-800">
                                Trial berakhir · {remaining} scan tersisa
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
    <div class="max-w-5xl mx-auto px-6 mt-4">
        <div
            class="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-4"
        >
            <div class="flex items-center gap-3">
                <div class="bg-emerald-100 rounded-lg p-2">
                    <Crown class="h-4 w-4 text-emerald-500" />
                </div>
                <div>
                    <p class="text-sm font-medium text-emerald-800">
                        Pro Plan · Unlimited Scan
                    </p>
                    <p class="text-xs text-emerald-600">
                        Total {subscription.usage_count} dokumen di-scan
                    </p>
                </div>
            </div>
        </div>
    </div>
{/if}

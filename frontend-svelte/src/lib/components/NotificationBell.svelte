<!--
  NotificationBell.svelte — Bell icon with badge count + dropdown panel
-->
<script>
    import { onMount } from "svelte";
    import { Bell, AlertCircle, AlertTriangle, Info, X } from "lucide-svelte";
    import { ApiService } from "../services/api";

    let { onNavigate = null } = $props();

    let notifications = $state([]);
    let count = $state(0);
    let showPanel = $state(false);
    let isLoading = $state(false);

    async function loadNotifications() {
        isLoading = true;
        try {
            const res = await ApiService.getNotifications();
            notifications = res.notifications || [];
            count = res.count || 0;
        } catch {
            notifications = [];
            count = 0;
        } finally {
            isLoading = false;
        }
    }

    onMount(() => {
        loadNotifications();
        // Refresh every 5 minutes
        const interval = setInterval(loadNotifications, 5 * 60 * 1000);
        return () => clearInterval(interval);
    });

    function getSeverityStyle(severity) {
        if (severity === "error")
            return "bg-red-50 border-red-200 text-red-700";
        if (severity === "warning")
            return "bg-amber-50 border-amber-200 text-amber-700";
        return "bg-blue-50 border-blue-200 text-blue-700";
    }

    function getSeverityIcon(severity) {
        if (severity === "error") return AlertCircle;
        if (severity === "warning") return AlertTriangle;
        return Info;
    }
</script>

<div class="relative">
    <button
        type="button"
        onclick={() => (showPanel = !showPanel)}
        class="relative p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        aria-label="Notifikasi"
    >
        <Bell class="w-5 h-5" />
        {#if count > 0}
            <span
                class="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center min-w-[18px] px-1"
            >
                {count > 99 ? "99+" : count}
            </span>
        {/if}
    </button>

    {#if showPanel}
        <!-- Backdrop -->
        <div
            class="fixed inset-0 z-40"
            onclick={() => (showPanel = false)}
            onkeydown={(e) => e.key === "Escape" && (showPanel = false)}
            role="button"
            tabindex="-1"
            aria-label="Tutup panel notifikasi"
        ></div>

        <!-- Panel -->
        <div
            class="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl shadow-2xl border border-slate-200 z-50 max-h-96 overflow-hidden flex flex-col"
        >
            <div
                class="flex items-center justify-between px-4 py-3 border-b border-slate-100"
            >
                <h3 class="text-sm font-semibold text-slate-800">Notifikasi</h3>
                <button
                    type="button"
                    onclick={() => (showPanel = false)}
                    class="p-1 hover:bg-slate-100 rounded"
                >
                    <X class="w-3.5 h-3.5 text-slate-400" />
                </button>
            </div>

            <div class="flex-1 overflow-y-auto">
                {#if notifications.length === 0}
                    <div class="py-10 text-center text-slate-400 text-sm">
                        <Bell class="w-8 h-8 mx-auto mb-2 text-slate-300" />
                        Tidak ada notifikasi
                    </div>
                {:else}
                    {#each notifications as n}
                        {@const Icon = getSeverityIcon(n.severity)}
                        <div
                            class="px-4 py-3 border-b border-slate-50 hover:bg-slate-50 cursor-pointer transition-colors"
                            onclick={() => {
                                if (n.group_id && onNavigate)
                                    onNavigate("scanner");
                                showPanel = false;
                            }}
                            onkeydown={(e) => {
                                if (e.key === "Enter" || e.key === " ") {
                                    if (n.group_id && onNavigate)
                                        onNavigate("scanner");
                                    showPanel = false;
                                }
                            }}
                            role="button"
                            tabindex="0"
                        >
                            <div class="flex gap-2.5">
                                <div class="flex-shrink-0 mt-0.5">
                                    <div
                                        class="w-7 h-7 rounded-lg flex items-center justify-center {getSeverityStyle(
                                            n.severity,
                                        )} border"
                                    >
                                        <Icon class="w-3.5 h-3.5" />
                                    </div>
                                </div>
                                <div class="flex-1 min-w-0">
                                    <p
                                        class="text-xs font-semibold text-slate-700"
                                    >
                                        {n.title}
                                    </p>
                                    <p
                                        class="text-xs text-slate-500 mt-0.5 leading-relaxed"
                                    >
                                        {n.message}
                                    </p>
                                </div>
                            </div>
                        </div>
                    {/each}
                {/if}
            </div>

            {#if count > 0}
                <div class="px-4 py-2 border-t border-slate-100 bg-slate-50">
                    <button
                        type="button"
                        onclick={loadNotifications}
                        class="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
                    >
                        🔄 Muat ulang
                    </button>
                </div>
            {/if}
        </div>
    {/if}
</div>

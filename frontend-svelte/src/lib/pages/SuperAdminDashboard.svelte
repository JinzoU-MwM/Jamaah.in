<script>
    import { onMount } from 'svelte';
    import { SuperAdminApi } from '../services/superAdminApi.js';
    import { ApiService } from '../services/api.js';
    import StatsCards from '../components/super-admin/StatsCards.svelte';
    import Charts from '../components/super-admin/Charts.svelte';
    import UserManagement from '../components/super-admin/UserManagement.svelte';
    import TicketList from '../components/super-admin/TicketList.svelte';
    import TicketDetail from '../components/super-admin/TicketDetail.svelte';

    let stats = {
        total_users: 0,
        active_users: 0,
        pro_users: 0,
        free_users: 0,
        total_tickets: 0,
        open_tickets: 0,
        resolved_tickets: 0,
        total_revenue: 0,
    };

    let activeTab = 'stats'; // 'stats', 'users', 'tickets'
    /** @type {any | null} */
    let selectedTicket = null;
    let unreadTicketCount = 0;
    let unreadMessageCount = 0;
    let lastUnreadMessageCount = 0;

    let loading = true;
    let error = null;
    let chartsLoading = false;
    let chartsError = null;
    let aiCacheLoading = false;
    let aiCacheError = null;
    let aiCacheRecentLoading = false;
    let aiCacheRecentError = null;
    let aiCachePurgeLoading = false;
    let aiCacheExportLoading = false;
    let aiCacheDeletingKey = null;
    let showExpiredOnly = false;

    let aiCacheStats = { total: 0, active: 0, expired: 0 };
    let aiCacheRecent = [];
    let aiCacheRecentTotal = 0;
    let aiCacheRecentLimit = 10;
    let chartsData = {
        user_activity: [],
        revenue_monthly: [],
    };

    onMount(() => {
        loadStats();
        loadCharts();
        loadAICacheStats();
        loadAICacheRecent();
        loadUnreadCount();

        const interval = setInterval(() => {
            loadUnreadCount();
        }, 15000);

        return () => clearInterval(interval);
    });

    async function loadStats({ background = false } = {}) {
        try {
            if (!background) {
                loading = true;
                error = null;
            }
            stats = await SuperAdminApi.getStats();
        } catch (err) {
            if (!background) {
                error = err.message;
            }
            console.error('Failed to load stats:', err);
        } finally {
            if (!background) {
                loading = false;
            }
        }
    }

    async function loadAICacheStats() {
        try {
            aiCacheLoading = true;
            aiCacheError = null;
            aiCacheStats = await SuperAdminApi.getAICacheStats();
        } catch (err) {
            aiCacheError = err.message;
        } finally {
            aiCacheLoading = false;
        }
    }

    async function loadCharts() {
        try {
            chartsLoading = true;
            chartsError = null;
            chartsData = await SuperAdminApi.getCharts();
        } catch (err) {
            chartsError = err.message;
        } finally {
            chartsLoading = false;
        }
    }

    async function loadAICacheRecent() {
        try {
            aiCacheRecentLoading = true;
            aiCacheRecentError = null;
            const res = await SuperAdminApi.getAICacheRecent({
                limit: aiCacheRecentLimit,
                offset: 0,
                expiredOnly: showExpiredOnly,
            });
            aiCacheRecent = res?.items || [];
            aiCacheRecentTotal = res?.total || 0;
        } catch (err) {
            aiCacheRecentError = err.message;
        } finally {
            aiCacheRecentLoading = false;
        }
    }

    async function purgeExpiredAICache() {
        try {
            aiCachePurgeLoading = true;
            await SuperAdminApi.purgeExpiredAICache();
            await Promise.all([loadAICacheStats(), loadAICacheRecent()]);
        } catch (err) {
            aiCacheRecentError = err.message;
        } finally {
            aiCachePurgeLoading = false;
        }
    }

    async function exportAICacheCsv() {
        try {
            aiCacheExportLoading = true;
            const blob = await SuperAdminApi.exportAICacheRecentCsv({
                expiredOnly: showExpiredOnly,
                limit: 5000,
            });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const suffix = showExpiredOnly ? 'expired' : 'all';
            a.href = url;
            a.download = `ai-cache-recent-${suffix}.csv`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (err) {
            aiCacheRecentError = err.message;
        } finally {
            aiCacheExportLoading = false;
        }
    }

    async function deleteAICacheRow(cacheKey) {
        if (!cacheKey) return;
        const confirmed = window.confirm(`Delete cache key ${cacheKey.slice(0, 16)}...?`);
        if (!confirmed) return;

        try {
            aiCacheDeletingKey = cacheKey;
            await SuperAdminApi.deleteAICacheKey(cacheKey);
            await Promise.all([loadAICacheStats(), loadAICacheRecent()]);
        } catch (err) {
            aiCacheRecentError = err.message;
        } finally {
            aiCacheDeletingKey = null;
        }
    }

    async function loadUnreadCount() {
        try {
            const res = await SuperAdminApi.getUnreadTicketCount();
            unreadTicketCount = res?.unread_tickets || 0;
            unreadMessageCount = res?.unread_messages || 0;

            if (
                unreadMessageCount > lastUnreadMessageCount &&
                typeof window !== 'undefined' &&
                'Notification' in window
            ) {
                if (Notification.permission === 'granted') {
                    new Notification('Pesan Support Baru', {
                        body: `Ada ${unreadMessageCount} pesan user yang belum dibaca.`,
                    });
                } else if (Notification.permission !== 'denied') {
                    Notification.requestPermission();
                }
            }

            lastUnreadMessageCount = unreadMessageCount;
        } catch {
            // Silent fail: unread polling should not break dashboard UX
        }
    }

    function selectTab(tab) {
        activeTab = tab;
    }

    function openTicket(ticket) {
        selectedTicket = ticket;
        loadUnreadCount();
    }

    function closeTicketDetail() {
        selectedTicket = null;
        loadStats({ background: true }); // Refresh summary without full-page spinner
        loadUnreadCount();
    }

    async function handleLogout() {
        try {
            await ApiService.logout();
        } catch {
            // no-op
        }
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/';
    }
</script>

<div class="min-h-screen bg-slate-50/70">
    <!-- Header -->
    <header class="sticky top-0 z-20 border-b border-slate-200/80 bg-white/80 backdrop-blur-xl">
        <div class="px-4 sm:px-6 lg:px-8">
            <div class="flex h-[72px] items-center justify-between">
                <div class="flex items-center">
                    <h1 class="text-xl font-extrabold text-slate-900">Jamaah.in</h1>
                    <span class="ml-3 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
                        SUPER ADMIN
                    </span>
                </div>
                <button onclick={handleLogout}
                    class="rounded-xl px-4 py-2 text-sm font-semibold text-slate-600 transition hover:bg-slate-100 hover:text-slate-900">
                    Logout
                </button>
            </div>
        </div>
    </header>

    {#if error}
        <div class="px-4 py-8 lg:px-8">
            <div class="rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-red-700">
                {error}
                <button onclick={() => loadStats()} class="ml-4 underline hover:no-underline">Retry</button>
            </div>
        </div>
    {:else if loading}
        <div class="flex justify-center px-4 py-8 lg:px-8">
            <div class="text-slate-500">Loading...</div>
        </div>
    {:else}
        <!-- Tabs -->
        <div class="border-b border-slate-200 bg-white">
            <div class="px-4 lg:px-8">
                <nav class="flex space-x-8">
                    <button
                        onclick={() => selectTab('stats')}
                        class:active={activeTab === 'stats'}
                        class:inactive={activeTab !== 'stats'}
                        class="py-4 px-1 border-b-2 font-medium text-sm transition-colors">
                        Dashboard
                    </button>
                    <button
                        onclick={() => selectTab('users')}
                        class:active={activeTab === 'users'}
                        class:inactive={activeTab !== 'users'}
                        class="py-4 px-1 border-b-2 font-medium text-sm transition-colors">
                        Users
                    </button>
                    <button
                        onclick={() => selectTab('tickets')}
                        class:active={activeTab === 'tickets'}
                        class:inactive={activeTab !== 'tickets'}
                        class="py-4 px-1 border-b-2 font-medium text-sm transition-colors">
                        Tickets
                        {#if unreadTicketCount > 0}
                            <span class="ml-2 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 text-[10px] font-bold text-white bg-red-500 rounded-full">
                                {unreadTicketCount > 99 ? '99+' : unreadTicketCount}
                            </span>
                        {/if}
                    </button>
                </nav>
            </div>
        </div>

        <!-- Content -->
        <div class="px-4 py-8 lg:px-8">
            {#if activeTab === 'stats'}
                <div class="space-y-8">
                    <StatsCards {stats} />
                    <Charts {stats} chartData={chartsData} loading={chartsLoading} error={chartsError} />

                    <section class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                        <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                            <h3 class="text-lg font-bold text-slate-900">AI Cache Ops</h3>
                            <div class="flex items-center gap-2">
                                <label class="flex items-center gap-2 text-sm text-slate-600">
                                    <input
                                        type="checkbox"
                                        bind:checked={showExpiredOnly}
                                        onchange={loadAICacheRecent}
                                    class="rounded border-slate-300 text-primary-600 focus:ring-primary-500"
                                    />
                                    Expired only
                                </label>
                                <button
                                    onclick={loadAICacheRecent}
                                    class="rounded-xl border border-slate-200 px-3 py-1.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                                    Refresh
                                </button>
                                <button
                                    onclick={exportAICacheCsv}
                                    disabled={aiCacheExportLoading}
                                    class="rounded-xl border border-primary-200 px-3 py-1.5 text-sm font-semibold text-primary-700 hover:bg-primary-50 disabled:opacity-60">
                                    {aiCacheExportLoading ? 'Exporting...' : 'Export CSV'}
                                </button>
                                <button
                                    onclick={purgeExpiredAICache}
                                    disabled={aiCachePurgeLoading}
                                    class="rounded-xl bg-red-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60">
                                    {aiCachePurgeLoading ? 'Purging...' : 'Purge Expired'}
                                </button>
                            </div>
                        </div>

                        {#if aiCacheError}
                            <div class="mb-3 text-sm text-red-600">{aiCacheError}</div>
                        {/if}

                        <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
                            <div class="rounded-2xl border border-slate-100 bg-slate-50 p-3">
                                <p class="text-xs text-slate-500">Total</p>
                                <p class="text-xl font-bold text-slate-900">{aiCacheLoading ? '...' : aiCacheStats.total}</p>
                            </div>
                            <div class="rounded-2xl border border-primary-100 bg-primary-50 p-3">
                                <p class="text-xs text-primary-700">Active</p>
                                <p class="text-xl font-bold text-primary-800">{aiCacheLoading ? '...' : aiCacheStats.active}</p>
                            </div>
                            <div class="rounded-lg bg-amber-50 border border-amber-200 p-3">
                                <p class="text-xs text-amber-700">Expired</p>
                                <p class="text-xl font-semibold text-amber-800">{aiCacheLoading ? '...' : aiCacheStats.expired}</p>
                            </div>
                        </div>

                        {#if aiCacheRecentError}
                            <div class="mb-2 text-sm text-red-600">{aiCacheRecentError}</div>
                        {/if}

                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead class="border-b border-slate-200 text-left text-slate-500">
                                    <tr>
                                        <th class="py-2 pr-3">Task</th>
                                        <th class="py-2 pr-3">Model</th>
                                        <th class="py-2 pr-3">Hits</th>
                                        <th class="py-2 pr-3">Expired</th>
                                        <th class="py-2 pr-3">Key</th>
                                        <th class="py-2 pr-3">Action</th>
                                    </tr>
                                </thead>
                                <tbody class="text-slate-800">
                                    {#if aiCacheRecentLoading}
                                        <tr><td class="py-3 text-slate-500" colspan="6">Loading recent cache rows...</td></tr>
                                    {:else if aiCacheRecent.length === 0}
                                        <tr><td class="py-3 text-slate-500" colspan="6">No cache rows found.</td></tr>
                                    {:else}
                                        {#each aiCacheRecent as row}
                                            <tr class="border-b border-slate-100">
                                                <td class="py-2 pr-3">{row.task_type}</td>
                                                <td class="py-2 pr-3">{row.model}</td>
                                                <td class="py-2 pr-3">{row.hits}</td>
                                                <td class="py-2 pr-3">
                                                    <span class={row.is_expired ? 'text-red-600' : 'text-primary-600'}>
                                                        {row.is_expired ? 'yes' : 'no'}
                                                    </span>
                                                </td>
                                                <td class="py-2 pr-3 font-mono text-xs text-slate-600">{row.cache_key.slice(0, 16)}...</td>
                                                <td class="py-2 pr-3">
                                                    <button
                                                        onclick={() => deleteAICacheRow(row.cache_key)}
                                                        disabled={aiCacheDeletingKey === row.cache_key}
                                                        class="rounded-lg border border-red-200 px-2 py-1 text-xs font-semibold text-red-700 hover:bg-red-50 disabled:opacity-60">
                                                        {aiCacheDeletingKey === row.cache_key ? 'Deleting...' : 'Delete'}
                                                    </button>
                                                </td>
                                            </tr>
                                        {/each}
                                    {/if}
                                </tbody>
                            </table>
                        </div>
                        <div class="mt-2 text-xs text-slate-500">Showing {aiCacheRecent.length} of {aiCacheRecentTotal} rows.</div>
                    </section>
                </div>
            {:else if activeTab === 'users'}
                <UserManagement onUpdate={loadStats} />
            {:else if activeTab === 'tickets'}
                {#if selectedTicket}
                    <div>
                        <button onclick={closeTicketDetail}
                            class="mb-4 flex items-center text-slate-600 transition hover:text-slate-900">
                            <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            Back to Tickets
                        </button>
                        <TicketDetail {selectedTicket} onClose={closeTicketDetail} />
                    </div>
                {:else}
                    <TicketList onSelect={openTicket} onRefresh={() => loadStats({ background: true })} />
                {/if}
            {/if}
        </div>
    {/if}
</div>

<style>
    .active {
        border-color: #2563eb;
        color: #2563eb;
    }
    .inactive {
        border-color: transparent;
        color: #6b7280;
    }
    .inactive:hover {
        color: #374151;
    }
</style>

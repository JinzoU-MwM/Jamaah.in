<script>
    import { onMount } from 'svelte';
    import { SuperAdminApi } from '../services/superAdminApi.js';
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

    onMount(() => {
        loadStats();
        loadUnreadCount();

        const interval = setInterval(() => {
            loadUnreadCount();
        }, 15000);

        return () => clearInterval(interval);
    });

    async function loadStats() {
        try {
            loading = true;
            error = null;
            stats = await SuperAdminApi.getStats();
        } catch (err) {
            error = err.message;
            console.error('Failed to load stats:', err);
        } finally {
            loading = false;
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
        loadStats(); // Refresh stats
        loadUnreadCount();
    }
</script>

<div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold text-emerald-600">JAMAAH.IN</h1>
                    <span class="ml-2 px-3 py-1 bg-amber-100 text-amber-800 text-xs font-semibold rounded-full">
                        SUPER ADMIN
                    </span>
                </div>
                <button onclick={() => { localStorage.removeItem('token'); window.location.href = '/'; }}
                    class="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition">
                    Logout
                </button>
            </div>
        </div>
    </header>

    {#if error}
        <div class="max-w-7xl mx-auto px-4 py-8">
            <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                {error}
                <button onclick={loadStats} class="ml-4 underline hover:no-underline">Retry</button>
            </div>
        </div>
    {:else if loading}
        <div class="max-w-7xl mx-auto px-4 py-8 flex justify-center">
            <div class="text-gray-500">Loading...</div>
        </div>
    {:else}
        <!-- Tabs -->
        <div class="bg-white border-b border-gray-200">
            <div class="max-w-7xl mx-auto px-4">
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
        <div class="max-w-7xl mx-auto px-4 py-8">
            {#if activeTab === 'stats'}
                <div class="space-y-8">
                    <StatsCards {stats} />
                    <Charts {stats} />
                </div>
            {:else if activeTab === 'users'}
                <UserManagement onUpdate={loadStats} />
            {:else if activeTab === 'tickets'}
                {#if selectedTicket}
                    <div>
                        <button onclick={closeTicketDetail}
                            class="mb-4 flex items-center text-gray-600 hover:text-gray-900 transition">
                            <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
                            </svg>
                            Back to Tickets
                        </button>
                        <TicketDetail {selectedTicket} onClose={closeTicketDetail} />
                    </div>
                {:else}
                    <TicketList onSelect={openTicket} onRefresh={loadStats} />
                {/if}
            {/if}
        </div>
    {/if}
</div>

<style>
    .active {
        border-color: #059669;
        color: #059669;
    }
    .inactive {
        border-color: transparent;
        color: #6b7280;
    }
    .inactive:hover {
        color: #374151;
    }
</style>

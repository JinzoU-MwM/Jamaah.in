<script>
    import { onMount } from 'svelte';
    import { SuperAdminApi } from '../../services/superAdminApi.js';

    export let onSelect = () => {};
    export let onRefresh = () => {};

    let tickets = [];
    let loading = false;
    let error = null;

    // Filters
    let statusFilter = 'all'; // 'all', 'open', 'in_progress', 'resolved', 'closed'
    let priorityFilter = 'all'; // 'all', 'low', 'medium', 'high', 'urgent'
    let page = 1;
    const limit = 20;

    onMount(() => {
        loadTickets();
    });

    async function loadTickets() {
        try {
            loading = true;
            error = null;
            const filters = {
                skip: (page - 1) * limit,
                limit,
            };
            if (statusFilter !== 'all') filters.status = statusFilter;
            if (priorityFilter !== 'all') filters.priority = priorityFilter;
            tickets = await SuperAdminApi.listTickets(filters);
        } catch (err) {
            error = err.message;
            console.error('Failed to load tickets:', err);
        } finally {
            loading = false;
        }
    }

    function selectTicket(ticket) {
        onSelect(ticket);
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    function getStatusBadge(status) {
        const badges = {
            open: '<span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded">Open</span>',
            in_progress: '<span class="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-semibold rounded">In Progress</span>',
            resolved: '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs font-semibold rounded">Resolved</span>',
            closed: '<span class="px-2 py-1 bg-gray-100 text-gray-800 text-xs font-semibold rounded">Closed</span>',
        };
        return badges[status] || badges.open;
    }

    function getPriorityBadge(priority) {
        const badges = {
            low: '<span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Low</span>',
            medium: '<span class="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Medium</span>',
            high: '<span class="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded">High</span>',
            urgent: '<span class="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">Urgent</span>',
        };
        return badges[priority] || badges.medium;
    }

    $: filteredTickets = tickets.filter(ticket => {
        if (statusFilter !== 'all' && ticket.status !== statusFilter) return false;
        if (priorityFilter !== 'all' && ticket.priority !== priorityFilter) return false;
        return true;
    });
</script>

<div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 class="text-xl font-semibold text-gray-900">Support Tickets</h2>
            <div class="flex flex-col sm:flex-row gap-3">
                <!-- Status Filter -->
                <select
                    bind:value={statusFilter}
                    class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                    <option value="all">All Status</option>
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                </select>

                <!-- Priority Filter -->
                <select
                    bind:value={priorityFilter}
                    class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                    <option value="all">All Priorities</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                </select>
            </div>
        </div>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto">
        {#if loading}
            <div class="p-8 text-center text-gray-500">Loading...</div>
        {:else if error}
            <div class="p-8 text-center text-red-500">{error}</div>
        {:else if filteredTickets.length === 0}
            <div class="p-8 text-center text-gray-500">No tickets found</div>
        {:else}
            <table class="w-full">
                <thead class="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Subject</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Priority</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Activity</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Messages</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    {#each filteredTickets as ticket}
                        <tr
                            class="hover:bg-gray-50 cursor-pointer transition-colors"
                            on:click={() => selectTicket(ticket)}
                        >
                            <td class="px-6 py-4">
                                <div class="font-medium text-gray-900">{ticket.subject}</div>
                            </td>
                            <td class="px-6 py-4">
                                <div class="text-sm">
                                    <div class="font-medium text-gray-700">{ticket.user_name}</div>
                                    <div class="text-gray-500">{ticket.user_email}</div>
                                </div>
                            </td>
                            <td class="px-6 py-4">
                                {@html getStatusBadge(ticket.status)}
                            </td>
                            <td class="px-6 py-4">
                                {@html getPriorityBadge(ticket.priority)}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                {formatDate(ticket.last_message_at)}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                {ticket.message_count}
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        {/if}
    </div>

    <!-- Pagination -->
    <div class="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <div class="text-sm text-gray-500">
            Showing {Math.min(filteredTickets.length, limit * page)} of {filteredTickets.length} tickets
        </div>
        <div class="flex space-x-2">
            <button
                on:click={() => page > 1 && (page -= 1, loadTickets())}
                disabled={page === 1}
                class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
                Previous
            </button>
            <button
                on:click={() => filteredTickets.length === limit * page && (page += 1, loadTickets())}
                disabled={filteredTickets.length < limit * page}
                class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
                Next
            </button>
        </div>
    </div>
</div>

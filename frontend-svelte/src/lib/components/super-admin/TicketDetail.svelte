<script>
    import { onMount } from 'svelte';
    import { SuperAdminApi } from '../../services/superAdminApi.js';

    export let selectedTicket = null;
    export let onClose = () => {};

    let ticketDetail = null;
    let loading = false;
    let error = null;

    let replyContent = '';
    let newStatus = 'open';

    onMount(async () => {
        if (selectedTicket) {
            await loadTicketDetail(selectedTicket.id);
        }
    });

    async function loadTicketDetail(ticketId) {
        try {
            loading = true;
            error = null;
            ticketDetail = await SuperAdminApi.getTicketDetail(ticketId);
            newStatus = ticketDetail.status;
        } catch (err) {
            error = err.message;
            console.error('Failed to load ticket:', err);
        } finally {
            loading = false;
        }
    }

    async function sendReply() {
        if (!replyContent.trim()) return;
        try {
            await SuperAdminApi.replyToTicket(ticketDetail.id, replyContent);
            replyContent = '';
            await loadTicketDetail(ticketDetail.id);
        } catch (err) {
            alert('Failed to send reply: ' + err.message);
        }
    }

    async function updateTicketStatus() {
        try {
            await SuperAdminApi.updateTicketStatus(ticketDetail.id, newStatus);
            await loadTicketDetail(ticketDetail.id);
        } catch (err) {
            alert('Failed to update status: ' + err.message);
        }
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
            open: '<span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-semibold rounded-full">Open</span>',
            in_progress: '<span class="px-3 py-1 bg-yellow-100 text-yellow-800 text-sm font-semibold rounded-full">In Progress</span>',
            resolved: '<span class="px-3 py-1 bg-green-100 text-green-800 text-sm font-semibold rounded-full">Resolved</span>',
            closed: '<span class="px-3 py-1 bg-gray-100 text-gray-800 text-sm font-semibold rounded-full">Closed</span>',
        };
        return badges[status] || badges.open;
    }

    function getPriorityBadge(priority) {
        const badges = {
            low: '<span class="px-3 py-1 bg-gray-100 text-gray-700 text-sm rounded-full">Low</span>',
            medium: '<span class="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">Medium</span>',
            high: '<span class="px-3 py-1 bg-orange-100 text-orange-800 text-sm rounded-full">High</span>',
            urgent: '<span class="px-3 py-1 bg-red-100 text-red-800 text-sm font-semibold rounded-full">Urgent</span>',
        };
        return badges[priority] || badges.medium;
    }
</script>

<div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
        <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div class="flex-1">
                <h2 class="text-xl font-semibold text-gray-900 mb-2">{ticketDetail?.subject || selectedTicket?.subject}</h2>
                <div class="flex flex-wrap items-center gap-3 text-sm">
                    <span class="text-gray-500">
                        <span class="font-medium text-gray-700">{ticketDetail?.user_name || selectedTicket?.user_name}</span>
                        ({ticketDetail?.user_email || selectedTicket?.user_email})
                    </span>
                    {#if ticketDetail}
                        {@html getStatusBadge(ticketDetail.status)}
                        {@html getPriorityBadge(ticketDetail.priority)}
                    {/if}
                </div>
            </div>
            <div class="flex flex-col gap-2">
                <!-- Status Change -->
                <div class="flex items-center gap-2">
                    <select
                        bind:value={newStatus}
                        class="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                    >
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                    </select>
                    <button
                        on:click={updateTicketStatus}
                        disabled={loading || newStatus === ticketDetail?.status}
                        class="px-4 py-2 bg-emerald-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-emerald-700 transition-colors text-sm font-medium"
                    >
                        Update Status
                    </button>
                </div>
                <!-- Close -->
                <button
                    on:click={onClose}
                    class="text-gray-500 hover:text-gray-700 transition-colors text-sm"
                >
                    Close
                </button>
            </div>
        </div>
    </div>

    <!-- Messages -->
    <div class="p-6 border-b border-gray-200">
        {#if loading}
            <div class="text-center text-gray-500">Loading...</div>
        {:else if ticketDetail?.messages}
            <div class="space-y-4 max-h-96 overflow-y-auto">
                {#each ticketDetail.messages as message}
                    <div class="flex {message.sender_type === 'admin' ? 'justify-end' : 'justify-start'}">
                        <div class="max-w-2xl">
                            <div class="text-xs text-gray-500 mb-1">
                                {message.sender_type === 'admin' ? 'Admin (You)' : ticketDetail.user_name}
                                • {formatDate(message.created_at)}
                            </div>
                            <div
                                class="px-4 py-3 rounded-lg {message.sender_type === 'admin' ? 'bg-emerald-100 text-gray-900' : 'bg-gray-100 text-gray-900'}"
                            >
                                {message.content}
                            </div>
                        </div>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <!-- Reply Form -->
    <div class="p-6">
        <label class="block text-sm font-medium text-gray-700 mb-2">Your Reply</label>
        <textarea
            bind:value={replyContent}
            rows="3"
            placeholder="Type your reply..."
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
        ></textarea>
        <div class="flex justify-end mt-3">
            <button
                on:click={sendReply}
                disabled={!replyContent.trim() || loading}
                class="px-6 py-2 bg-emerald-600 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-emerald-700 transition-colors font-medium"
            >
                Send Reply
            </button>
        </div>
    </div>
</div>

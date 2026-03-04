<script>
    import { onMount } from 'svelte';
    import { ApiService } from '../../services/api.js';

    export let onUpdate = () => {};

    let users = [];
    let loading = false;
    let error = null;

    // Filters
    let search = '';
    let statusFilter = 'all'; // 'all', 'active', 'inactive'
    let page = 1;
    const limit = 20;

    let showUserModal = false;
    let selectedUser = null;

    onMount(() => {
        loadUsers();
    });

    async function loadUsers() {
        try {
            loading = true;
            error = null;
            // Use the existing admin endpoint
            const params = new URLSearchParams({
                skip: String((page - 1) * limit),
                limit: String(limit)
            });
            if (search) params.append('search', search);
            const result = await fetch(`/api/admin/users?${params}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            if (!result.ok) throw new Error('Failed to load users');
            const data = await result.json();
            users = data.users || [];
        } catch (err) {
            error = err.message;
            console.error('Failed to load users:', err);
        } finally {
            loading = false;
        }
    }

    function openUserModal(user) {
        selectedUser = user;
        showUserModal = true;
    }

    function closeUserModal() {
        showUserModal = false;
        selectedUser = null;
    }

    async function toggleUserStatus(user) {
        try {
            const endpoint = user.is_active ? '/admin/users' : '/admin/users';
            const result = await fetch(`/api${endpoint}/${user.id}/active`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_active: !user.is_active })
            });
            if (!result.ok) throw new Error('Failed to update user');
            await loadUsers();
            onUpdate();
        } catch (err) {
            alert(err.message);
        }
    }

    async function setAdminStatus(user, isAdmin) {
        try {
            const result = await fetch(`/api/admin/users/${user.id}/admin`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ is_admin: isAdmin })
            });
            if (!result.ok) throw new Error('Failed to update admin status');
            await loadUsers();
            onUpdate();
        } catch (err) {
            alert(err.message);
        }
    }

    function formatDate(dateStr) {
        return new Date(dateStr).toLocaleDateString('id-ID', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
    }

    function getPlanBadge(plan) {
        if (!plan) return '<span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Unknown</span>';
        if (plan === 'pro') {
            return '<span class="px-2 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded">PRO</span>';
        }
        return '<span class="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">Free</span>';
    }

    function getStatusBadge(isActive, isAdmin) {
        if (isAdmin) {
            return '<span class="px-2 py-1 bg-purple-100 text-purple-800 text-xs font-semibold rounded">Admin</span>';
        }
        if (isActive) {
            return '<span class="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Active</span>';
        }
        return '<span class="px-2 py-1 bg-red-100 text-red-800 text-xs rounded">Inactive</span>';
    }

    $: filteredUsers = users.filter(user => {
        if (statusFilter === 'active' && !user.is_active) return false;
        if (statusFilter === 'inactive' && user.is_active) return false;
        if (search) {
            const searchLower = search.toLowerCase();
            return user.email.toLowerCase().includes(searchLower) ||
                   user.name.toLowerCase().includes(searchLower);
        }
        return true;
    });
</script>

<div class="bg-white rounded-xl shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="p-6 border-b border-gray-200">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <h2 class="text-xl font-semibold text-gray-900">User Management</h2>
            <div class="flex flex-col sm:flex-row gap-3">
                <!-- Search -->
                <div class="relative">
                    <input
                        type="text"
                        bind:value={search}
                        placeholder="Search by email or name..."
                        class="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent w-full sm:w-64"
                    />
                    <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                </div>

                <!-- Filter -->
                <select
                    bind:value={statusFilter}
                    class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                    <option value="all">All Users</option>
                    <option value="active">Active Only</option>
                    <option value="inactive">Inactive Only</option>
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
        {:else if filteredUsers.length === 0}
            <div class="p-8 text-center text-gray-500">No users found</div>
        {:else}
            <table class="w-full">
                <thead class="bg-gray-50 border-b border-gray-200">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Plan</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Usage</th>
                        <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-gray-200">
                    {#each filteredUsers as user}
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4">
                                <div>
                                    <div class="font-medium text-gray-900">{user.name}</div>
                                    <div class="text-sm text-gray-500">{user.email}</div>
                                </div>
                            </td>
                            <td class="px-6 py-4">
                                {@html getPlanBadge(user.plan)}
                            </td>
                            <td class="px-6 py-4">
                                {@html getStatusBadge(user.is_active, user.is_admin)}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                {formatDate(user.created_at)}
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-500">
                                {user.usage_count || 0}
                            </td>
                            <td class="px-6 py-4 text-right">
                                <div class="flex items-center justify-end space-x-2">
                                    <button
                                        on:click={() => setAdminStatus(user, !user.is_admin)}
                                        class="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                                        title="{user.is_admin ? 'Remove Admin' : 'Make Admin'}"
                                    >
                                        {#if user.is_admin}
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 12H4" />
                                            </svg>
                                        {:else}
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                                            </svg>
                                        {/if}
                                    </button>
                                    <button
                                        on:click={() => toggleUserStatus(user)}
                                        class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                                        title="{user.is_active ? 'Deactivate' : 'Activate'}"
                                    >
                                        {#if user.is_active}
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 0118.364 5.636m0 9a9 9 0 01-12.728 0m12.728 12.728a9 9 0 01-12.728 0" />
                                            </svg>
                                        {:else}
                                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                            </svg>
                                        {/if}
                                    </button>
                                </div>
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
            Showing {Math.min(filteredUsers.length, limit * page)} of {filteredUsers.length} users
        </div>
        <div class="flex space-x-2">
            <button
                on:click={() => page > 1 && (page -= 1, loadUsers())}
                disabled={page === 1}
                class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
                Previous
            </button>
            <button
                on:click={() => filteredUsers.length === limit * page && (page += 1, loadUsers())}
                disabled={filteredUsers.length < limit * page}
                class="px-4 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
            >
                Next
            </button>
        </div>
    </div>
</div>

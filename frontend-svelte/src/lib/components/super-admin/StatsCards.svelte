<script>
    export let stats = {
        total_users: 0,
        active_users: 0,
        pro_users: 0,
        free_users: 0,
        total_tickets: 0,
        open_tickets: 0,
        resolved_tickets: 0,
        total_revenue: 0,
    };

    function formatRevenue(value) {
        if (value >= 1000000) {
            return `Rp ${(value / 1000000).toFixed(1)}M`;
        } else if (value >= 1000) {
            return `Rp ${(value / 1000).toFixed(0)}K`;
        }
        return `Rp ${value}`;
    }
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
    <!-- Total Users -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Total Users</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{stats.total_users.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-blue-100 rounded-lg">
                <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 8 0 0 18 0zM12 4.354a4 4 0 100 8 0 0-18 0zm0 14.354a4 4 0 110 8 0 0 18 0zM12 18.708a4 4 0 100 8 0 0-18 0z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Active Users -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Active Users</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{stats.active_users.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-green-100 rounded-lg">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Revenue -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Total Revenue</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{formatRevenue(stats.total_revenue)}</p>
            </div>
            <div class="p-3 bg-emerald-100 rounded-lg">
                <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Total Tickets -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Total Tickets</p>
                <p class="text-3xl font-bold text-gray-900 mt-2">{stats.total_tickets.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-purple-100 rounded-lg">
                <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Pro Users -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Pro Users</p>
                <p class="text-3xl font-bold text-emerald-600 mt-2">{stats.pro_users.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-emerald-100 rounded-lg">
                <svg class="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001-.946C4.92 12.11 4 8.645 4 8c0-2.21 1.791-4 4-4s4-1.791 4-4c-.645 0-1.11.084-1.889.303-.322-.808-.747-1.54-1.27-1.587M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v2.341C7.67 8.165 6 8.988 6 10c0 .846.275 1.629.737 2.225l-1.336 2.224A3.997 3.997 0 011 20a4 4 0 014-4 4 4 0 01-4-4 3.987 3.987 0 01-1.664-1.225l-1.336-2.224A3.995 3.995 0 0114 10c0-.846.275-1.629.737-2.225V3a2 2 0 10-4 0v2.341A6.002 6.002 0 006 10z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Free Users -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Free Users</p>
                <p class="text-3xl font-bold text-gray-600 mt-2">{stats.free_users.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-gray-100 rounded-lg">
                <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Open Tickets -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Open Tickets</p>
                <p class="text-3xl font-bold text-amber-600 mt-2">{stats.open_tickets.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-amber-100 rounded-lg">
                <svg class="w-6 h-6 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
        </div>
    </div>

    <!-- Resolved Tickets -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div class="flex items-center justify-between">
            <div>
                <p class="text-sm font-medium text-gray-500">Resolved Tickets</p>
                <p class="text-3xl font-bold text-green-600 mt-2">{stats.resolved_tickets.toLocaleString()}</p>
            </div>
            <div class="p-3 bg-green-100 rounded-lg">
                <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
            </div>
        </div>
    </div>
</div>

<script>
    export let stats = {
        total_users: 0,
        active_users: 0,
        pro_users: 0,
        free_users: 0,
    };

    // Sample data - in production, this would come from API
    let userActivityData = [12, 19, 8, 15, 22, 18, 25, 14, 20, 17, 23, 16, 21, 13, 19, 24, 15, 22, 18, 26, 20, 14, 25, 17, 23, 21, 19, 16, 24];
    let revenueData = [1500000, 2100000, 1800000, 2500000, 2200000, 2800000, 3100000, 2900000, 3500000, 3200000, 3800000, 3400000];
    let months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    function formatCurrency(value) {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(0) + 'K';
        }
        return value;
    }
</script>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- User Activity Chart -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">User Activity (30 Days)</h3>
        <div class="h-64">
            <svg viewBox="0 0 400 150" class="w-full h-full">
                <!-- Grid lines -->
                <line x1="40" y1="10" x2="400" y2="10" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="50" x2="400" y2="50" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="90" x2="400" y2="90" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="130" x2="400" y2="130" stroke="#e5e7eb" stroke-width="1" />

                <!-- Y-axis labels -->
                <text x="10" y="14" font-size="10" fill="#9ca3af">30</text>
                <text x="10" y="54" font-size="10" fill="#9ca3af">20</text>
                <text x="10" y="94" font-size="10" fill="#9ca3af">10</text>
                <text x="10" y="134" font-size="10" fill="#9ca3af">0</text>

                <!-- X-axis labels -->
                {#each months.slice(0, 6) as month, i}
                    <text x={40 + (i * 60)} y="145" font-size="9" fill="#9ca3af">{month}</text>
                {/each}

                <!-- Area fill -->
                <polygon
                    points="40,130 100,70 160,90 220,60 280,80 340,50 340,130"
                    fill="#10b981"
                    fill-opacity="0.1"
                />

                <!-- Line -->
                <polyline
                    points="40,130 100,70 160,90 220,60 280,80 340,50"
                    fill="none"
                    stroke="#10b981"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                />

                <!-- Data points -->
                {#each userActivityData.slice(0, 6) as value, i}
                    <circle cx={40 + (i * 60)} cy={130 - (value * 4)} r="4" fill="#10b981" />
                {/each}
            </svg>
        </div>
    </div>

    <!-- Revenue Growth Chart -->
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Revenue Growth (Monthly)</h3>
        <div class="h-64">
            <svg viewBox="0 0 400 150" class="w-full h-full">
                <!-- Grid lines -->
                <line x1="40" y1="10" x2="400" y2="10" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="50" x2="400" y2="50" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="90" x2="400" y2="90" stroke="#e5e7eb" stroke-width="1" />
                <line x1="40" y1="130" x2="400" y2="130" stroke="#e5e7eb" stroke-width="1" />

                <!-- Y-axis labels -->
                <text x="10" y="14" font-size="9" fill="#9ca3af">{formatCurrency(4000000)}</text>
                <text x="10" y="54" font-size="9" fill="#9ca3af">{formatCurrency(3000000)}</text>
                <text x="10" y="94" font-size="9" fill="#9ca3af">{formatCurrency(2000000)}</text>
                <text x="10" y="134" font-size="9" fill="#9ca3af">{formatCurrency(1000000)}</text>

                <!-- X-axis labels -->
                {#each months as month, i}
                    <text x={40 + (i * 30)} y="145" font-size="8" fill="#9ca3af">{month}</text>
                {/each}

                <!-- Bars -->
                {#each revenueData as value, i}
                    <rect
                        x={42 + (i * 30)}
                        y={130 - (value / 4000000 * 120)}
                        width="26"
                        height={value / 4000000 * 120}
                        fill="url(#barGradient)"
                        rx="2"
                    />
                {/each}

                <!-- Gradient definition -->
                <defs>
                    <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stop-color="#10b981" />
                        <stop offset="100%" stop-color="#059669" />
                    </linearGradient>
                </defs>
            </svg>
        </div>
    </div>
</div>

<!-- Legend -->
<div class="mt-4 flex justify-center space-x-8">
    <div class="flex items-center">
        <div class="w-4 h-4 bg-emerald-500 rounded mr-2"></div>
        <span class="text-sm text-gray-600">Users</span>
    </div>
    <div class="flex items-center">
        <div class="w-4 h-4 bg-gradient-to-b from-emerald-500 to-emerald-600 rounded mr-2" style="background: linear-gradient(to bottom, #10b981, #059669)"></div>
        <span class="text-sm text-gray-600">Revenue (Rp)</span>
    </div>
</div>

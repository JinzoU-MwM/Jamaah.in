<script>
    export let stats = {
        total_users: 0,
        active_users: 0,
        pro_users: 0,
        free_users: 0,
    };
    export let chartData = {
        user_activity: [],
        revenue_monthly: [],
    };
    export let loading = false;
    export let error = null;

    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

    const userChartLeft = 40;
    const userChartRight = 380;
    const chartTop = 10;
    const chartBottom = 130;
    const chartHeight = chartBottom - chartTop;

    $: userSeries = (chartData?.user_activity || []).slice(-30);
    $: userValues = userSeries.map((item) => Number(item.count || 0));
    $: userDates = userSeries.map((item) => item.date);
    $: userMaxRaw = Math.max(1, ...userValues);
    $: userMax = Math.max(5, Math.ceil(userMaxRaw / 5) * 5);
    $: userStep = userValues.length > 1
        ? (userChartRight - userChartLeft) / (userValues.length - 1)
        : 0;
    $: userPoints = userValues
        .map((value, i) => {
            const x = userChartLeft + (i * userStep);
            const y = chartBottom - ((value / userMax) * chartHeight);
            return `${x},${y}`;
        })
        .join(' ');
    $: userAreaPoints = userPoints
        ? `${userChartLeft},${chartBottom} ${userPoints} ${userChartRight},${chartBottom}`
        : '';
    $: userTickIndices = userDates.length > 0
        ? [0, 6, 12, 18, 24, userDates.length - 1]
        : [];

    $: revenueSeries = (chartData?.revenue_monthly || []).slice(-12);
    $: revenueValues = revenueSeries.map((item) => Number(item.amount || 0));
    $: revenueMonths = revenueSeries.map((item) => item.month);
    $: revenueMaxRaw = Math.max(1, ...revenueValues);
    $: revenueMax = Math.ceil(revenueMaxRaw / 100000) * 100000;
    $: revenueLeft = 40;
    $: revenueRight = 390;
    $: revenueSlot = revenueValues.length > 0 ? (revenueRight - revenueLeft) / revenueValues.length : 0;
    $: revenueBarWidth = Math.max(12, revenueSlot * 0.72);

    function formatCurrency(value) {
        if (value >= 1000000) {
            return (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return (value / 1000).toFixed(0) + 'K';
        }
        return value;
    }

    function formatDayLabel(isoDate) {
        if (!isoDate) return '';
        const d = new Date(`${isoDate}T00:00:00Z`);
        return d.toLocaleDateString('id-ID', { day: 'numeric', month: 'short' });
    }

    function formatMonthLabel(monthKey) {
        if (!monthKey || monthKey.length < 7) return '';
        const monthNum = Number(monthKey.slice(5, 7));
        return monthNames[Math.max(0, Math.min(11, monthNum - 1))];
    }
</script>

<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">User Activity (30 Days)</h3>
        <div class="h-64">
            {#if loading}
                <div class="h-full flex items-center justify-center text-gray-500 text-sm">Loading chart...</div>
            {:else}
                <svg viewBox="0 0 400 150" class="w-full h-full">
                    <line x1="40" y1="10" x2="400" y2="10" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="50" x2="400" y2="50" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="90" x2="400" y2="90" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="130" x2="400" y2="130" stroke="#e5e7eb" stroke-width="1" />

                    <text x="10" y="14" font-size="10" fill="#9ca3af">{userMax}</text>
                    <text x="10" y="54" font-size="10" fill="#9ca3af">{Math.round(userMax * 0.67)}</text>
                    <text x="10" y="94" font-size="10" fill="#9ca3af">{Math.round(userMax * 0.33)}</text>
                    <text x="10" y="134" font-size="10" fill="#9ca3af">0</text>

                    {#each userTickIndices as idx}
                        <text x={userChartLeft + (idx * userStep)} y="145" font-size="8" fill="#9ca3af">{formatDayLabel(userDates[idx])}</text>
                    {/each}

                    <polygon
                        points={userAreaPoints}
                        fill="#10b981"
                        fill-opacity="0.1"
                    />

                    <polyline
                        points={userPoints}
                        fill="none"
                        stroke="#10b981"
                        stroke-width="2"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                    />

                    {#each userValues as value, i}
                        <circle
                            cx={userChartLeft + (i * userStep)}
                            cy={chartBottom - ((value / userMax) * chartHeight)}
                            r="2"
                            fill="#10b981"
                        />
                    {/each}
                </svg>
            {/if}
        </div>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">Revenue Growth (Monthly)</h3>
        <div class="h-64">
            {#if loading}
                <div class="h-full flex items-center justify-center text-gray-500 text-sm">Loading chart...</div>
            {:else}
                <svg viewBox="0 0 400 150" class="w-full h-full">
                    <line x1="40" y1="10" x2="400" y2="10" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="50" x2="400" y2="50" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="90" x2="400" y2="90" stroke="#e5e7eb" stroke-width="1" />
                    <line x1="40" y1="130" x2="400" y2="130" stroke="#e5e7eb" stroke-width="1" />

                    <text x="10" y="14" font-size="9" fill="#9ca3af">{formatCurrency(revenueMax)}</text>
                    <text x="10" y="54" font-size="9" fill="#9ca3af">{formatCurrency(Math.round(revenueMax * 0.67))}</text>
                    <text x="10" y="94" font-size="9" fill="#9ca3af">{formatCurrency(Math.round(revenueMax * 0.33))}</text>
                    <text x="10" y="134" font-size="9" fill="#9ca3af">0</text>

                    {#each revenueMonths as month, i}
                        <text x={revenueLeft + (i * revenueSlot) + (revenueSlot / 2)} y="145" font-size="8" fill="#9ca3af" text-anchor="middle">{formatMonthLabel(month)}</text>
                    {/each}

                    {#each revenueValues as value, i}
                        <rect
                            x={revenueLeft + (i * revenueSlot) + ((revenueSlot - revenueBarWidth) / 2)}
                            y={chartBottom - ((value / revenueMax) * chartHeight)}
                            width={revenueBarWidth}
                            height={(value / revenueMax) * chartHeight}
                            fill="url(#barGradient)"
                            rx="2"
                        />
                    {/each}

                    <defs>
                        <linearGradient id="barGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" stop-color="#10b981" />
                            <stop offset="100%" stop-color="#059669" />
                        </linearGradient>
                    </defs>
                </svg>
            {/if}
        </div>
    </div>
</div>

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

{#if error}
    <div class="mt-3 text-center text-xs text-red-600">
        {error}
    </div>
{/if}

<div class="mt-3 text-center text-xs text-gray-500">
    Total users: {stats.total_users} | Pro: {stats.pro_users} | Free: {stats.free_users}
</div>

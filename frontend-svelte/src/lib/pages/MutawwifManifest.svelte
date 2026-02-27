<script>
    import { onMount } from "svelte";
    import { ApiService } from "../services/api.js";

    let { token = "" } = $props();

    // --- State ---
    let phase = $state("pin"); // "pin" | "loading" | "data" | "error"
    let pin = $state("");
    let pinError = $state("");
    let manifest = $state(null);
    let searchQuery = $state("");
    let errorMessage = $state("");
    let isOffline = $state(false);

    // Attendance checklist — persisted to localStorage
    let checkedIds = $state(new Set());

    onMount(() => {
        // Load saved attendance from localStorage
        try {
            const saved = localStorage.getItem(`mutawwif_${token}`);
            if (saved) {
                checkedIds = new Set(JSON.parse(saved));
            }
        } catch {}

        // Listen for online/offline events
        const goOnline = () => {
            isOffline = false;
        };
        const goOffline = () => {
            isOffline = true;
        };
        window.addEventListener("online", goOnline);
        window.addEventListener("offline", goOffline);
        isOffline = !navigator.onLine;

        return () => {
            window.removeEventListener("online", goOnline);
            window.removeEventListener("offline", goOffline);
        };
    });

    // Cache manifest data to localStorage
    function cacheManifest(data) {
        try {
            localStorage.setItem(
                `manifest_cache_${token}`,
                JSON.stringify(data),
            );
        } catch {}
    }

    function getCachedManifest() {
        try {
            const cached = localStorage.getItem(`manifest_cache_${token}`);
            return cached ? JSON.parse(cached) : null;
        } catch {
            return null;
        }
    }

    function saveChecklist() {
        try {
            localStorage.setItem(
                `mutawwif_${token}`,
                JSON.stringify([...checkedIds]),
            );
        } catch {}
    }

    function toggleCheck(id) {
        if (checkedIds.has(id)) {
            checkedIds.delete(id);
        } else {
            checkedIds.add(id);
        }
        checkedIds = new Set(checkedIds); // trigger reactivity
        saveChecklist();
    }

    async function submitPin() {
        if (pin.length < 4 || !/^\d+$/.test(pin)) {
            pinError = "Masukkan PIN 4-6 digit";
            return;
        }
        phase = "loading";
        pinError = "";
        try {
            const data = await ApiService.getSharedManifest(token, pin);
            manifest = data;
            cacheManifest(data);
            isOffline = false;
            phase = "data";
        } catch (e) {
            // Try cached data when offline
            const cached = getCachedManifest();
            if (cached) {
                manifest = cached;
                isOffline = true;
                phase = "data";
            } else {
                pinError = e.message || "PIN salah atau link kedaluwarsa";
                phase = "pin";
            }
        }
    }

    function handlePinKeydown(e) {
        if (e.key === "Enter") submitPin();
    }

    // Filtered members by search
    let filteredMembers = $derived(
        manifest?.members
            ? manifest.members.filter((m) =>
                  m.nama.toLowerCase().includes(searchQuery.toLowerCase()),
              )
            : [],
    );

    let checkedCount = $derived(
        manifest?.members
            ? manifest.members.filter((m) => checkedIds.has(m.id)).length
            : 0,
    );

    function formatPhone(phone) {
        if (!phone) return "";
        let cleaned = phone.replace(/[^0-9+]/g, "");
        if (cleaned.startsWith("0")) {
            cleaned = "62" + cleaned.slice(1);
        }
        return cleaned;
    }

    function getGenderLabel(title) {
        if (!title) return "";
        const t = title.toLowerCase();
        if (t === "mr" || t === "tuan") return "♂";
        if (t === "mrs" || t === "ms" || t === "nyonya" || t === "nona")
            return "♀";
        return "";
    }

    function getGenderColor(title) {
        if (!title) return "bg-slate-100 text-slate-500";
        const t = title.toLowerCase();
        if (t === "mr" || t === "tuan") return "bg-blue-100 text-blue-700";
        return "bg-pink-100 text-pink-700";
    }
</script>

<!-- Full-screen mobile-first layout — NO sidebar, NO admin nav -->
<div
    class="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-emerald-50"
>
    {#if phase === "pin"}
        <!-- PIN Entry Screen -->
        <div class="min-h-screen flex items-center justify-center px-4">
            <div class="w-full max-w-sm">
                <!-- Logo / Header -->
                <div class="text-center mb-8">
                    <div
                        class="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-200"
                    >
                        <svg
                            class="w-8 h-8 text-white"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                            ></path>
                        </svg>
                    </div>
                    <h1 class="text-2xl font-bold text-slate-800">
                        Manifest Jamaah
                    </h1>
                    <p class="text-sm text-slate-500 mt-1">
                        Masukkan PIN untuk melihat data
                    </p>
                </div>

                <!-- PIN Input -->
                <div
                    class="bg-white rounded-2xl shadow-lg p-6 border border-slate-100"
                >
                    <label
                        for="manifest-pin"
                        class="block text-sm font-medium text-slate-600 mb-2 text-center"
                        >PIN Akses</label
                    >
                    <input
                        id="manifest-pin"
                        type="text"
                        inputmode="numeric"
                        maxlength="6"
                        bind:value={pin}
                        onkeydown={handlePinKeydown}
                        placeholder="• • • •"
                        class="w-full px-4 py-4 border-2 border-slate-200 rounded-xl text-center text-3xl font-mono tracking-[0.6em] focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all"
                        autocomplete="off"
                    />

                    {#if pinError}
                        <div
                            class="mt-3 text-center text-sm text-red-500 bg-red-50 p-2 rounded-lg"
                        >
                            {pinError}
                        </div>
                    {/if}

                    <button
                        onclick={submitPin}
                        disabled={pin.length < 4}
                        class="w-full mt-4 bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold py-3.5 rounded-xl transition-all shadow-md shadow-emerald-200 active:transform active:scale-[0.98]"
                    >
                        Buka Manifest
                    </button>
                </div>

                <p class="text-xs text-slate-400 text-center mt-4">
                    Powered by <span class="font-semibold text-emerald-600"
                        >Jamaah.in</span
                    >
                </p>
            </div>
        </div>
    {:else if phase === "loading"}
        <!-- Loading -->
        <div class="min-h-screen flex items-center justify-center">
            <div class="text-center">
                <div
                    class="w-12 h-12 border-4 border-emerald-200 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"
                ></div>
                <p class="text-slate-500">Memuat manifest...</p>
            </div>
        </div>
    {:else if phase === "data" && manifest}
        <!-- Data View -->

        <!-- Sticky Header -->
        <div
            class="sticky top-0 z-30 bg-white/90 backdrop-blur-lg border-b border-slate-200 shadow-sm"
        >
            <div class="max-w-lg mx-auto px-4 py-3">
                <div class="flex items-center justify-between mb-2">
                    <div>
                        <h1
                            class="text-lg font-bold text-slate-800 leading-tight"
                        >
                            {manifest.group_name}
                        </h1>
                        <p class="text-xs text-slate-500">
                            {manifest.total_members} jamaah · {checkedCount} hadir
                            ✓
                        </p>
                    </div>
                    <div class="flex items-center gap-1">
                        {#if isOffline}
                            <span
                                class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-700"
                            >
                                📡 Offline
                            </span>
                        {/if}
                        <span
                            class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-100 text-emerald-700"
                        >
                            {checkedCount}/{manifest.total_members}
                        </span>
                    </div>
                </div>

                <!-- Search Bar -->
                <div class="relative">
                    <svg
                        class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                        ></path>
                    </svg>
                    <input
                        type="text"
                        bind:value={searchQuery}
                        placeholder="Cari nama jamaah..."
                        class="w-full pl-9 pr-4 py-2.5 bg-slate-100 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all"
                    />
                    {#if searchQuery}
                        <button
                            onclick={() => (searchQuery = "")}
                            class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                            aria-label="Clear search"
                        >
                            ✕
                        </button>
                    {/if}
                </div>
            </div>
        </div>

        <!-- Member Cards -->
        <div class="max-w-lg mx-auto px-4 py-4 pb-24 space-y-3">
            {#if filteredMembers.length === 0}
                <div class="text-center py-12 text-slate-400">
                    <p class="text-lg">🔍</p>
                    <p class="text-sm mt-1">
                        Tidak ditemukan jamaah dengan nama "{searchQuery}"
                    </p>
                </div>
            {/if}

            {#each filteredMembers as member, idx (member.id)}
                <div
                    class="bg-white rounded-xl border transition-all shadow-sm
                        {checkedIds.has(member.id)
                        ? 'border-emerald-300 bg-emerald-50/50'
                        : 'border-slate-200'}"
                >
                    <div class="p-4">
                        <!-- Top Row: Number + Name + Gender -->
                        <div class="flex items-start gap-3">
                            <!-- Name + Info -->
                            <div class="flex-1 min-w-0">
                                <div class="flex items-center gap-2 mb-1">
                                    <span
                                        class="text-xs font-medium text-slate-400"
                                        >#{idx + 1}</span
                                    >
                                    <span
                                        class="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium {getGenderColor(
                                            member.title,
                                        )}"
                                    >
                                        {getGenderLabel(member.title)}
                                        {member.title || "-"}
                                    </span>
                                </div>
                                <h3
                                    class="font-semibold text-slate-800 text-sm leading-snug truncate {checkedIds.has(
                                        member.id,
                                    )
                                        ? 'line-through text-slate-500'
                                        : ''}"
                                >
                                    {member.nama || "Tidak ada nama"}
                                </h3>
                            </div>

                            <!-- Status Badge (top-right) -->
                            {#if checkedIds.has(member.id)}
                                <span
                                    class="flex-shrink-0 inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-700"
                                >
                                    ✓ Hadir
                                </span>
                            {/if}
                        </div>

                        <!-- Details Grid -->
                        <div
                            class="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs"
                        >
                            <div>
                                <span class="text-slate-400">Paspor</span>
                                <p class="font-mono font-medium text-slate-700">
                                    {member.no_paspor || "-"}
                                </p>
                            </div>
                            <div>
                                <span class="text-slate-400">Kamar</span>
                                <p class="font-medium text-slate-700">
                                    {member.room_number || "-"}
                                </p>
                            </div>
                            <div>
                                <span class="text-slate-400">Ukuran Baju</span>
                                <p class="font-medium text-slate-700">
                                    {member.baju_size || "-"}
                                </p>
                            </div>
                            <div>
                                <span class="text-slate-400">Perlengkapan</span>
                                <p
                                    class="font-medium {member.is_equipment_received
                                        ? 'text-emerald-600'
                                        : 'text-amber-600'}"
                                >
                                    {member.is_equipment_received
                                        ? "✓ Sudah"
                                        : "✗ Belum"}
                                </p>
                            </div>
                        </div>

                        <!-- Action Buttons Row -->
                        <div class="mt-3 flex items-center gap-2">
                            <!-- Attendance Button — PROMINENT -->
                            <button
                                onclick={() => toggleCheck(member.id)}
                                class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold transition-all active:transform active:scale-[0.97]
                                    {checkedIds.has(member.id)
                                    ? 'bg-emerald-500 text-white shadow-md shadow-emerald-200 hover:bg-emerald-600'
                                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200 border border-slate-200'}"
                            >
                                {#if checkedIds.has(member.id)}
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="3"
                                            d="M5 13l4 4L19 7"
                                        ></path>
                                    </svg>
                                    Hadir
                                {:else}
                                    <svg
                                        class="w-4 h-4"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                    >
                                        <path
                                            stroke-linecap="round"
                                            stroke-linejoin="round"
                                            stroke-width="2"
                                            d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                                        ></path>
                                    </svg>
                                    Tandai Hadir
                                {/if}
                            </button>

                            <!-- WhatsApp Button -->
                            {#if member.no_hp}
                                <a
                                    href="https://wa.me/{formatPhone(
                                        member.no_hp,
                                    )}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    class="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-2.5 bg-green-500 hover:bg-green-600 text-white text-xs font-medium rounded-lg transition-all shadow-sm active:transform active:scale-95"
                                >
                                    <svg
                                        class="w-3.5 h-3.5"
                                        viewBox="0 0 24 24"
                                        fill="currentColor"
                                    >
                                        <path
                                            d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"
                                        />
                                        <path
                                            d="M12 0C5.373 0 0 5.373 0 12c0 2.127.555 4.126 1.528 5.869L.063 23.573a.5.5 0 00.612.612l5.704-1.465A11.953 11.953 0 0012 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 22c-1.94 0-3.765-.56-5.309-1.528l-.372-.22-3.858.99.99-3.858-.22-.372A9.961 9.961 0 012 12C2 6.486 6.486 2 12 2s10 4.486 10 10-4.486 10-10 10z"
                                        />
                                    </svg>
                                    WA
                                </a>
                            {/if}
                        </div>
                    </div>
                </div>
            {/each}
        </div>

        <!-- Floating Stats Bar -->
        <div
            class="fixed bottom-0 left-0 right-0 bg-white/95 backdrop-blur-lg border-t border-slate-200 shadow-lg z-30"
        >
            <div
                class="max-w-lg mx-auto px-4 py-3 flex items-center justify-between"
            >
                <div class="text-xs text-slate-500">
                    <span class="font-medium text-emerald-600"
                        >{checkedCount}</span
                    >
                    / {manifest.total_members} hadir
                </div>
                <div class="flex-1 mx-3">
                    <div class="w-full bg-slate-200 rounded-full h-2">
                        <div
                            class="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                            style="width: {manifest.total_members > 0
                                ? (checkedCount / manifest.total_members) * 100
                                : 0}%"
                        ></div>
                    </div>
                </div>
                <span class="text-xs font-medium text-emerald-600">
                    {manifest.total_members > 0
                        ? Math.round(
                              (checkedCount / manifest.total_members) * 100,
                          )
                        : 0}%
                </span>
            </div>
        </div>
    {/if}
</div>

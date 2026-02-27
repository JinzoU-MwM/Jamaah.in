<script>
    import { onMount } from "svelte";
    import {
        FolderPlus,
        FolderOpen,
        Users,
        Trash2,
        Plus,
        Loader2,
        ChevronRight,
        Eye,
        Share2,
        Link,
        Copy,
        CheckCircle,
        X,
        MessageCircle,
    } from "lucide-svelte";
    import { ApiService } from "../services/api.js";
    import WhatsAppBlast from "./WhatsAppBlast.svelte";

    let {
        selectedGroup = $bindable(null),
        onGroupSelect = () => {},
        onViewGroup = () => {},
        isPro = false,
    } = $props();

    let groups = $state([]);
    let loading = $state(true);
    let creating = $state(false);
    let newGroupName = $state("");
    let showCreateInput = $state(false);
    let deleteConfirm = $state(null);
    let error = $state("");

    // --- Share / Mutawwif ---
    let shareModal = $state(false);
    let shareGroup = $state(null);
    let sharePin = $state("");
    let shareExpiry = $state(30);
    let shareLoading = $state(false);
    let shareResult = $state(null);
    let shareError = $state("");
    let copied = $state(false);

    // --- WhatsApp Blast ---
    let waBlastOpen = $state(false);
    let waBlastGroup = $state(null);

    function openWaBlast(group) {
        waBlastGroup = group;
        waBlastOpen = true;
    }

    onMount(async () => {
        await loadGroups();
    });

    async function loadGroups() {
        loading = true;
        error = "";
        try {
            const result = await ApiService.listGroups();
            groups = result.groups || [];
        } catch (e) {
            error = e.message;
        } finally {
            loading = false;
        }
    }

    async function createGroup() {
        if (!newGroupName.trim()) return;
        creating = true;
        error = "";
        try {
            const group = await ApiService.createGroup(newGroupName.trim());
            groups = [group, ...groups];
            newGroupName = "";
            showCreateInput = false;
            selectGroup(group);
        } catch (e) {
            error = e.message;
        } finally {
            creating = false;
        }
    }

    async function deleteGroup(groupId) {
        try {
            await ApiService.deleteGroup(groupId);
            groups = groups.filter((g) => g.id !== groupId);
            if (selectedGroup?.id === groupId) {
                selectedGroup = null;
                onGroupSelect(null);
            }
            deleteConfirm = null;
        } catch (e) {
            error = e.message;
        }
    }

    function selectGroup(group) {
        selectedGroup = group;
        onGroupSelect(group);
    }

    function handleKeydown(e) {
        if (e.key === "Enter") createGroup();
        if (e.key === "Escape") {
            showCreateInput = false;
            newGroupName = "";
        }
    }

    function formatDate(iso) {
        if (!iso) return "";
        const d = new Date(iso);
        return d.toLocaleDateString("id-ID", {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    }

    // --- Share functions ---
    function openShareModal(group) {
        shareGroup = group;
        sharePin = "";
        shareExpiry = 30;
        shareResult = null;
        shareError = "";
        shareModal = true;
    }

    function closeShareModal() {
        shareModal = false;
        shareGroup = null;
        shareResult = null;
        shareError = "";
        copied = false;
    }

    async function handleShare() {
        if (!sharePin || sharePin.length < 4 || !/^\d+$/.test(sharePin)) {
            shareError = "PIN harus 4-6 digit angka";
            return;
        }
        shareLoading = true;
        shareError = "";
        try {
            const result = await ApiService.shareGroup(
                shareGroup.id,
                sharePin,
                shareExpiry,
            );
            shareResult = result;
        } catch (e) {
            shareError = e.message;
        } finally {
            shareLoading = false;
        }
    }

    async function copyUrl() {
        if (!shareResult?.shared_url) return;
        try {
            await navigator.clipboard.writeText(shareResult.shared_url);
            copied = true;
            setTimeout(() => (copied = false), 2000);
        } catch {
            // Fallback
            const input = document.createElement("input");
            input.value = shareResult.shared_url;
            document.body.appendChild(input);
            input.select();
            document.execCommand("copy");
            document.body.removeChild(input);
            copied = true;
            setTimeout(() => (copied = false), 2000);
        }
    }
</script>

<div class="mb-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
        <div class="flex items-center gap-2">
            <FolderOpen class="h-5 w-5 text-emerald-600" />
            <h3 class="font-semibold text-slate-800">Grup Jamaah</h3>
            <span class="text-sm text-slate-400">({groups.length})</span>
        </div>
        <button
            onclick={() => (showCreateInput = !showCreateInput)}
            class="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors"
        >
            <Plus class="h-4 w-4" />
            <span class="hidden sm:inline">Buat Grup</span>
        </button>
    </div>

    <!-- Create Input -->
    {#if showCreateInput}
        <div class="mb-4 flex gap-2">
            <input
                type="text"
                bind:value={newGroupName}
                onkeydown={handleKeydown}
                placeholder="Nama grup (mis: UMROH 12 Februari)"
                class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent"
            />
            <button
                onclick={createGroup}
                disabled={creating || !newGroupName.trim()}
                class="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 disabled:bg-slate-300 text-white text-sm font-medium rounded-xl transition-colors flex items-center gap-2"
            >
                {#if creating}
                    <Loader2 class="h-4 w-4 animate-spin" />
                {:else}
                    <FolderPlus class="h-4 w-4" />
                {/if}
                Buat
            </button>
        </div>
    {/if}

    <!-- Error -->
    {#if error}
        <div class="mb-3 text-sm text-red-600 bg-red-50 px-3 py-2 rounded-lg">
            {error}
        </div>
    {/if}

    <!-- Loading -->
    {#if loading}
        <div class="flex items-center justify-center py-8 text-slate-400">
            <Loader2 class="h-5 w-5 animate-spin mr-2" />
            Memuat grup...
        </div>
    {:else if groups.length === 0}
        <!-- Empty State -->
        <div
            class="text-center py-8 bg-slate-50 rounded-xl border border-dashed border-slate-200"
        >
            <FolderOpen class="h-10 w-10 text-slate-300 mx-auto mb-3" />
            <p class="text-sm text-slate-500 mb-1">Belum ada grup</p>
            <p class="text-xs text-slate-400">
                Buat grup untuk mengelompokkan data jamaah
            </p>
        </div>
    {:else}
        <!-- Group Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {#each groups as group (group.id)}
                <!-- svelte-ignore a11y_no_static_element_interactions -->
                <div
                    onclick={() => selectGroup(group)}
                    onkeydown={(e) => {
                        if (e.key === "Enter") selectGroup(group);
                    }}
                    role="button"
                    tabindex="0"
                    class="text-left p-4 rounded-xl border-2 transition-all cursor-pointer
            {selectedGroup?.id === group.id
                        ? 'border-emerald-400 bg-emerald-50 shadow-md shadow-emerald-100'
                        : 'border-slate-200 bg-white hover:border-slate-300 hover:shadow-sm'}"
                >
                    <div class="flex items-start justify-between mb-2">
                        <h4
                            class="font-semibold text-sm truncate pr-2
              {selectedGroup?.id === group.id
                                ? 'text-emerald-700'
                                : 'text-slate-700'}"
                        >
                            {group.name}
                        </h4>

                        <div class="flex items-center gap-1 flex-shrink-0">
                            <!-- View group data -->
                            {#if group.member_count > 0}
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        onViewGroup(group);
                                    }}
                                    class="p-1 text-slate-400 hover:text-emerald-500 rounded transition-colors"
                                    title="Lihat data"
                                >
                                    <Eye class="h-3.5 w-3.5" />
                                </button>
                            {/if}

                            <!-- Share to Mutawwif -->
                            {#if isPro && group.member_count > 0}
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        openShareModal(group);
                                    }}
                                    class="p-1 text-slate-400 hover:text-blue-500 rounded transition-colors"
                                    title="Bagikan ke Mutawwif"
                                >
                                    <Share2 class="h-3.5 w-3.5" />
                                </button>
                            {/if}

                            <!-- WhatsApp Blast -->
                            {#if group.member_count > 0}
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        openWaBlast(group);
                                    }}
                                    class="p-1 text-slate-400 hover:text-green-500 rounded transition-colors"
                                    title="WhatsApp Blast"
                                >
                                    <MessageCircle class="h-3.5 w-3.5" />
                                </button>
                            {/if}

                            <!-- Delete -->
                            {#if deleteConfirm === group.id}
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        deleteGroup(group.id);
                                    }}
                                    class="px-2 py-0.5 text-xs bg-red-500 text-white rounded-md hover:bg-red-600"
                                >
                                    Hapus
                                </button>
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        deleteConfirm = null;
                                    }}
                                    class="px-2 py-0.5 text-xs bg-slate-200 text-slate-600 rounded-md hover:bg-slate-300"
                                >
                                    Batal
                                </button>
                            {:else}
                                <button
                                    onclick={(e) => {
                                        e.stopPropagation();
                                        deleteConfirm = group.id;
                                    }}
                                    class="p-1 text-slate-300 hover:text-red-400 rounded transition-colors"
                                    title="Hapus grup"
                                >
                                    <Trash2 class="h-3.5 w-3.5" />
                                </button>
                            {/if}
                        </div>
                    </div>

                    <div class="flex items-center justify-between">
                        <div
                            class="flex items-center gap-1 text-xs text-slate-400"
                        >
                            <Users class="h-3 w-3" />
                            <span>{group.member_count} jamaah</span>
                        </div>
                        <span class="text-xs text-slate-400"
                            >{formatDate(group.updated_at)}</span
                        >
                    </div>

                    {#if selectedGroup?.id === group.id}
                        <div
                            class="mt-2 pt-2 border-t border-emerald-200 flex items-center gap-1 text-xs text-emerald-600 font-medium"
                        >
                            <ChevronRight class="h-3 w-3" />
                            Upload ke grup ini
                        </div>
                    {/if}
                </div>
            {/each}
        </div>
    {/if}
</div>

<!-- Share to Mutawwif Modal -->
{#if shareModal && shareGroup}
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onclick={closeShareModal}
        onkeydown={(e) => {
            if (e.key === "Escape") closeShareModal();
        }}
        role="button"
        tabindex="-1"
        aria-label="Tutup modal"
    >
        <div
            class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6"
            onclick={(e) => e.stopPropagation()}
            onkeydown={(e) => {
                if (e.key === "Escape") closeShareModal();
            }}
            role="dialog"
            aria-modal="true"
            tabindex="-1"
        >
            <!-- Header -->
            <div class="flex justify-between items-center mb-4">
                <div class="flex items-center gap-2">
                    <Share2 class="h-5 w-5 text-blue-500" />
                    <h3 class="font-bold text-lg text-slate-800">
                        Bagikan ke Mutawwif
                    </h3>
                </div>
                <button
                    onclick={closeShareModal}
                    class="text-slate-400 hover:text-slate-600"
                    aria-label="Close"
                >
                    <X class="h-5 w-5" />
                </button>
            </div>

            <p class="text-sm text-slate-500 mb-4">
                Buat link aman untuk Mutawwif melihat manifest grup
                <strong class="text-slate-700">{shareGroup.name}</strong>
                di HP mereka.
            </p>

            {#if !shareResult}
                <!-- PIN Input -->
                <div class="mb-4">
                    <label
                        for="share-pin"
                        class="block text-sm font-medium text-slate-700 mb-1"
                        >PIN Akses (4-6 digit)</label
                    >
                    <input
                        id="share-pin"
                        type="text"
                        inputmode="numeric"
                        maxlength="6"
                        bind:value={sharePin}
                        placeholder="Contoh: 1234"
                        class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-center text-2xl font-mono tracking-[0.5em] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                </div>

                <!-- Expiry -->
                <div class="mb-5">
                    <label
                        for="share-expiry"
                        class="block text-sm font-medium text-slate-700 mb-1"
                        >Masa Berlaku</label
                    >
                    <select
                        id="share-expiry"
                        bind:value={shareExpiry}
                        class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                        <option value={7}>7 hari</option>
                        <option value={14}>14 hari</option>
                        <option value={30}>30 hari</option>
                        <option value={60}>60 hari</option>
                        <option value={90}>90 hari</option>
                    </select>
                </div>

                {#if shareError}
                    <div
                        class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
                    >
                        {shareError}
                    </div>
                {/if}

                <button
                    onclick={handleShare}
                    disabled={shareLoading || !sharePin}
                    class="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-blue-300 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
                >
                    {#if shareLoading}
                        <Loader2 class="h-5 w-5 animate-spin" />
                        Membuat link...
                    {:else}
                        <Link class="h-5 w-5" />
                        Buat Link Manifest
                    {/if}
                </button>
            {:else}
                <!-- Success: Show URL -->
                <div
                    class="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-4"
                >
                    <div class="flex items-center gap-2 mb-2">
                        <CheckCircle class="h-5 w-5 text-emerald-500" />
                        <span class="text-sm font-medium text-emerald-700"
                            >Link berhasil dibuat!</span
                        >
                    </div>
                    <div
                        class="bg-white rounded-lg p-3 border border-emerald-100"
                    >
                        <p class="text-xs text-slate-400 mb-1">
                            URL untuk Mutawwif:
                        </p>
                        <p class="text-sm font-mono text-slate-700 break-all">
                            {shareResult.shared_url}
                        </p>
                    </div>
                    <div class="mt-2 text-xs text-emerald-600">
                        PIN: <strong class="font-mono">{shareResult.pin}</strong
                        >
                        · Berlaku hingga: {formatDate(shareResult.expires_at)}
                    </div>
                </div>

                <div class="flex gap-2">
                    <button
                        onclick={copyUrl}
                        class="flex-1 bg-blue-500 hover:bg-blue-600 text-white font-semibold py-3 rounded-xl transition-all flex items-center justify-center gap-2"
                    >
                        {#if copied}
                            <CheckCircle class="h-5 w-5" />
                            Tersalin!
                        {:else}
                            <Copy class="h-5 w-5" />
                            Salin URL
                        {/if}
                    </button>
                    <button
                        onclick={closeShareModal}
                        class="px-4 py-3 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-xl transition-all"
                    >
                        Tutup
                    </button>
                </div>
            {/if}
        </div>
    </div>
{/if}

<!-- WhatsApp Blast Modal -->
<WhatsAppBlast
    isOpen={waBlastOpen}
    onClose={() => {
        waBlastOpen = false;
        waBlastGroup = null;
    }}
    group={waBlastGroup}
/>

<!--
  TeamPage.svelte — Team / Organization Management (Pro Feature)
  Create org, invite members by email, manage roles.
-->
<script>
    import { onMount } from "svelte";
    import {
        Users,
        UserPlus,
        Shield,
        Crown,
        Eye,
        Trash2,
        Loader2,
        X,
        Building2,
        Mail,
        Copy,
        CheckCircle,
        AlertCircle,
    } from "lucide-svelte";
    import { ApiService } from "../services/api.js";

    let { isPro = false } = $props();

    // State
    let team = $state(null);
    let isLoading = $state(true);
    let error = $state("");

    // Create org
    let showCreate = $state(false);
    let orgName = $state("");
    let isCreating = $state(false);

    // Invite
    let showInvite = $state(false);
    let inviteEmail = $state("");
    let inviteRole = $state("viewer");
    let isInviting = $state(false);
    let inviteSuccess = $state(null);
    let copied = $state(false);

    // Join
    let showJoin = $state(false);
    let joinToken = $state("");
    let isJoining = $state(false);

    const roleLabels = { owner: "Owner", admin: "Admin", viewer: "Viewer" };
    const roleColors = {
        owner: "text-amber-600 bg-amber-50",
        admin: "text-blue-600 bg-blue-50",
        viewer: "text-slate-600 bg-slate-50",
    };

    onMount(loadTeam);

    async function loadTeam() {
        isLoading = true;
        error = "";
        try {
            team = await ApiService.getTeam();
        } catch (e) {
            error = e.message;
        } finally {
            isLoading = false;
        }
    }

    async function createOrg() {
        if (!orgName.trim()) return;
        isCreating = true;
        error = "";
        try {
            await ApiService.createOrganization(orgName.trim());
            orgName = "";
            showCreate = false;
            await loadTeam();
        } catch (e) {
            error = e.message;
        } finally {
            isCreating = false;
        }
    }

    async function inviteMember() {
        if (!inviteEmail.trim()) return;
        isInviting = true;
        error = "";
        inviteSuccess = null;
        try {
            const result = await ApiService.inviteTeamMember(
                inviteEmail.trim(),
                inviteRole,
            );
            inviteSuccess = result;
            inviteEmail = "";
            await loadTeam();
        } catch (e) {
            error = e.message;
        } finally {
            isInviting = false;
        }
    }

    async function joinOrg() {
        if (!joinToken.trim()) return;
        isJoining = true;
        error = "";
        try {
            await ApiService.joinTeam(joinToken.trim());
            joinToken = "";
            showJoin = false;
            await loadTeam();
        } catch (e) {
            error = e.message;
        } finally {
            isJoining = false;
        }
    }

    async function updateRole(memberId, newRole) {
        try {
            await ApiService.updateTeamMemberRole(memberId, newRole);
            await loadTeam();
        } catch (e) {
            error = e.message;
        }
    }

    async function removeMember(memberId) {
        if (!confirm("Hapus anggota dari tim?")) return;
        try {
            await ApiService.removeTeamMember(memberId);
            await loadTeam();
        } catch (e) {
            error = e.message;
        }
    }

    async function cancelInvite(inviteId) {
        try {
            await ApiService.cancelTeamInvite(inviteId);
            await loadTeam();
        } catch (e) {
            error = e.message;
        }
    }

    async function copyToken(token) {
        try {
            await navigator.clipboard.writeText(token);
            copied = true;
            setTimeout(() => (copied = false), 2000);
        } catch {
            /* ignore */
        }
    }

    let hasOrg = $derived(!!team?.organization);
    let myRole = $derived(team?.my_role || "viewer");
    let canManage = $derived(myRole === "owner" || myRole === "admin");
</script>

<div class="max-w-3xl mx-auto px-4 sm:px-6 py-6 sm:py-10">
    <!-- Header -->
    <div class="flex items-center gap-3 mb-6">
        <div
            class="w-10 h-10 bg-violet-100 dark:bg-violet-900/30 rounded-xl flex items-center justify-center"
        >
            <Building2 class="w-5 h-5 text-violet-600" />
        </div>
        <div>
            <h1 class="text-xl font-bold text-slate-800 dark:text-slate-100">
                Tim
            </h1>
            <p class="text-sm text-slate-500">
                Kelola organisasi & anggota tim
            </p>
        </div>
    </div>

    <!-- Error -->
    {#if error}
        <div
            class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl mb-4 flex items-center gap-2 text-sm"
        >
            <AlertCircle class="w-4 h-4 flex-shrink-0" />
            {error}
            <button onclick={() => (error = "")} class="ml-auto"
                ><X class="w-4 h-4" /></button
            >
        </div>
    {/if}

    {#if isLoading}
        <div class="flex items-center justify-center py-16 text-slate-400">
            <Loader2 class="w-6 h-6 animate-spin mr-2" /> Memuat...
        </div>
    {:else if !hasOrg}
        <!-- No Organization Yet -->
        <div
            class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-8 text-center"
        >
            <Users class="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h2
                class="text-lg font-semibold text-slate-700 dark:text-slate-200 mb-2"
            >
                Belum ada organisasi
            </h2>
            <p class="text-sm text-slate-500 mb-6">
                Buat organisasi untuk mengundang anggota tim dan berbagi data
                grup.
            </p>

            <div class="flex flex-col sm:flex-row gap-3 justify-center">
                {#if !showCreate}
                    <button
                        type="button"
                        onclick={() => (showCreate = true)}
                        class="px-5 py-2.5 bg-violet-500 hover:bg-violet-600 text-white font-medium rounded-xl flex items-center gap-2 justify-center transition-colors"
                    >
                        <Building2 class="w-4 h-4" /> Buat Organisasi
                    </button>
                {/if}

                {#if !showJoin}
                    <button
                        type="button"
                        onclick={() => (showJoin = true)}
                        class="px-5 py-2.5 border border-slate-200 dark:border-slate-600 text-slate-600 dark:text-slate-300 font-medium rounded-xl flex items-center gap-2 justify-center hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                    >
                        <UserPlus class="w-4 h-4" /> Gabung Tim
                    </button>
                {/if}
            </div>

            {#if showCreate}
                <div class="mt-6 max-w-sm mx-auto">
                    <input
                        type="text"
                        bind:value={orgName}
                        placeholder="Nama organisasi (mis: PT Travel Umroh)"
                        class="w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl text-sm mb-3 bg-white dark:bg-slate-700 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-violet-400"
                        onkeydown={(e) => {
                            if (e.key === "Enter") createOrg();
                        }}
                    />
                    <div class="flex gap-2">
                        <button
                            onclick={createOrg}
                            disabled={isCreating || !orgName.trim()}
                            class="flex-1 px-4 py-2 bg-violet-500 hover:bg-violet-600 disabled:bg-violet-300 text-white text-sm font-medium rounded-xl flex items-center gap-2 justify-center"
                        >
                            {#if isCreating}<Loader2
                                    class="w-4 h-4 animate-spin"
                                />{/if} Buat
                        </button>
                        <button
                            onclick={() => (showCreate = false)}
                            class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-sm rounded-xl"
                            >Batal</button
                        >
                    </div>
                </div>
            {/if}

            {#if showJoin}
                <div class="mt-6 max-w-sm mx-auto">
                    <input
                        type="text"
                        bind:value={joinToken}
                        placeholder="Masukkan kode undangan"
                        class="w-full px-4 py-2.5 border border-slate-200 dark:border-slate-600 rounded-xl text-sm mb-3 bg-white dark:bg-slate-700 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-violet-400 font-mono"
                        onkeydown={(e) => {
                            if (e.key === "Enter") joinOrg();
                        }}
                    />
                    <div class="flex gap-2">
                        <button
                            onclick={joinOrg}
                            disabled={isJoining || !joinToken.trim()}
                            class="flex-1 px-4 py-2 bg-violet-500 hover:bg-violet-600 disabled:bg-violet-300 text-white text-sm font-medium rounded-xl flex items-center gap-2 justify-center"
                        >
                            {#if isJoining}<Loader2
                                    class="w-4 h-4 animate-spin"
                                />{/if} Gabung
                        </button>
                        <button
                            onclick={() => (showJoin = false)}
                            class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 text-sm rounded-xl"
                            >Batal</button
                        >
                    </div>
                </div>
            {/if}
        </div>
    {:else}
        <!-- Has Organization -->
        <div class="space-y-6">
            <!-- Org Card -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5"
            >
                <div class="flex items-center justify-between">
                    <div>
                        <h2
                            class="text-lg font-bold text-slate-800 dark:text-slate-100"
                        >
                            {team.organization.name}
                        </h2>
                        <p class="text-sm text-slate-500">
                            {team.members.length} anggota · Role Anda:
                            <span class="font-medium capitalize">{myRole}</span>
                        </p>
                    </div>
                    <div
                        class="px-3 py-1 rounded-full text-xs font-medium {roleColors[
                            myRole
                        ]}"
                    >
                        {#if myRole === "owner"}<Crown
                                class="w-3 h-3 inline mr-1"
                            />{:else if myRole === "admin"}<Shield
                                class="w-3 h-3 inline mr-1"
                            />{:else}<Eye class="w-3 h-3 inline mr-1" />{/if}
                        {roleLabels[myRole]}
                    </div>
                </div>
            </div>

            <!-- Members -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700"
            >
                <div
                    class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700"
                >
                    <h3
                        class="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2"
                    >
                        <Users class="w-4 h-4" /> Anggota ({team.members
                            .length})
                    </h3>
                    {#if canManage}
                        <button
                            type="button"
                            onclick={() => {
                                showInvite = !showInvite;
                                inviteSuccess = null;
                            }}
                            class="px-3 py-1.5 bg-violet-500 hover:bg-violet-600 text-white text-xs font-medium rounded-lg flex items-center gap-1.5"
                        >
                            <UserPlus class="w-3 h-3" /> Undang
                        </button>
                    {/if}
                </div>

                <!-- Invite Form -->
                {#if showInvite && canManage}
                    <div
                        class="px-5 py-4 border-b border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900"
                    >
                        {#if inviteSuccess}
                            <div
                                class="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-700 rounded-xl p-4"
                            >
                                <div class="flex items-center gap-2 mb-2">
                                    <CheckCircle
                                        class="w-4 h-4 text-emerald-500"
                                    />
                                    <span
                                        class="text-sm font-medium text-emerald-700 dark:text-emerald-300"
                                        >Undangan berhasil dibuat!</span
                                    >
                                </div>
                                <p class="text-xs text-slate-500 mb-2">
                                    Bagikan kode ini ke {inviteSuccess.email}:
                                </p>
                                <div class="flex items-center gap-2">
                                    <code
                                        class="flex-1 text-sm bg-white dark:bg-slate-800 px-3 py-2 rounded-lg font-mono border border-slate-200 dark:border-slate-600 break-all"
                                        >{inviteSuccess.token}</code
                                    >
                                    <button
                                        onclick={() =>
                                            copyToken(inviteSuccess.token)}
                                        class="px-3 py-2 bg-violet-500 hover:bg-violet-600 text-white text-xs rounded-lg flex items-center gap-1"
                                    >
                                        {#if copied}<CheckCircle
                                                class="w-3 h-3"
                                            /> Tersalin{:else}<Copy
                                                class="w-3 h-3"
                                            /> Salin{/if}
                                    </button>
                                </div>
                            </div>
                        {:else}
                            <div class="flex flex-col sm:flex-row gap-2">
                                <input
                                    type="email"
                                    bind:value={inviteEmail}
                                    placeholder="Email anggota baru"
                                    class="flex-1 px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-violet-400"
                                />
                                <select
                                    bind:value={inviteRole}
                                    class="px-3 py-2 border border-slate-200 dark:border-slate-600 rounded-lg text-sm bg-white dark:bg-slate-700 dark:text-slate-100"
                                >
                                    <option value="viewer">Viewer</option>
                                    <option value="admin">Admin</option>
                                </select>
                                <button
                                    onclick={inviteMember}
                                    disabled={isInviting || !inviteEmail.trim()}
                                    class="px-4 py-2 bg-violet-500 hover:bg-violet-600 disabled:bg-violet-300 text-white text-sm font-medium rounded-lg flex items-center gap-1.5"
                                >
                                    {#if isInviting}<Loader2
                                            class="w-3 h-3 animate-spin"
                                        />{/if}
                                    <Mail class="w-3 h-3" /> Kirim
                                </button>
                            </div>
                        {/if}
                    </div>
                {/if}

                <!-- Member List -->
                <div class="divide-y divide-slate-100 dark:divide-slate-700">
                    {#each team.members as member}
                        <div
                            class="flex items-center justify-between px-5 py-3"
                        >
                            <div class="flex items-center gap-3 min-w-0">
                                <div
                                    class="w-8 h-8 rounded-full bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center text-violet-600 text-sm font-bold flex-shrink-0"
                                >
                                    {(member.name || "?")[0].toUpperCase()}
                                </div>
                                <div class="min-w-0">
                                    <p
                                        class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate"
                                    >
                                        {member.name}
                                    </p>
                                    <p class="text-xs text-slate-400 truncate">
                                        {member.email}
                                    </p>
                                </div>
                            </div>
                            <div class="flex items-center gap-2">
                                {#if canManage && member.role !== "owner" && myRole === "owner"}
                                    <select
                                        value={member.role}
                                        onchange={(e) =>
                                            updateRole(
                                                member.id,
                                                /** @type {HTMLSelectElement} */ (
                                                    e.target
                                                ).value,
                                            )}
                                        class="text-xs px-2 py-1 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 dark:text-slate-200"
                                    >
                                        <option value="admin">Admin</option>
                                        <option value="viewer">Viewer</option>
                                    </select>
                                    <button
                                        onclick={() => removeMember(member.id)}
                                        class="p-1 text-slate-400 hover:text-red-500"
                                        title="Hapus"
                                    >
                                        <Trash2 class="w-3.5 h-3.5" />
                                    </button>
                                {:else}
                                    <span
                                        class="px-2 py-1 rounded-full text-xs font-medium {roleColors[
                                            member.role
                                        ]}"
                                    >
                                        {roleLabels[member.role]}
                                    </span>
                                {/if}
                            </div>
                        </div>
                    {/each}
                </div>
            </div>

            <!-- Pending Invites -->
            {#if team.invites?.length > 0}
                <div
                    class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700"
                >
                    <div
                        class="px-5 py-4 border-b border-slate-100 dark:border-slate-700"
                    >
                        <h3
                            class="font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2"
                        >
                            <Mail class="w-4 h-4" /> Undangan Pending ({team
                                .invites.length})
                        </h3>
                    </div>
                    <div
                        class="divide-y divide-slate-100 dark:divide-slate-700"
                    >
                        {#each team.invites as inv}
                            <div
                                class="flex items-center justify-between px-5 py-3"
                            >
                                <div>
                                    <p
                                        class="text-sm text-slate-700 dark:text-slate-200"
                                    >
                                        {inv.email}
                                    </p>
                                    <p class="text-xs text-slate-400">
                                        Role: {roleLabels[inv.role]} · Expires: {new Date(
                                            inv.expires_at,
                                        ).toLocaleDateString("id-ID")}
                                    </p>
                                </div>
                                {#if canManage}
                                    <button
                                        onclick={() => cancelInvite(inv.id)}
                                        class="text-xs text-red-500 hover:text-red-600 px-2 py-1"
                                    >
                                        Batalkan
                                    </button>
                                {/if}
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>

<script>
    import { onMount, onDestroy } from "svelte";
    import {
        User,
        Crown,
        Shield,
        Lock,
        Save,
        CheckCircle,
        AlertCircle,
        Clock,
        Zap,
        Copy,
        ChevronRight,
        Trash2,
        Activity,
        Bell,
        Moon,
        Sun,
        MessageCircle,
        FolderOpen,
        BarChart3,
        Loader2,
    } from "lucide-svelte";
    import { ApiService } from "../services/api";

    let {
        onLogout,
        onUpgradeRequest,
        user = null,
        subscription: initialSubscription = null,
        trialAvailable: initialTrialAvailable = false,
        groups: initialGroups = [],
    } = $props();

    // Simple header for sidebar layout
    $effect(() => {
        document.title = "Profil - Jamaah.in";
    });

    // Profile state
    let profile = $state(null);
    let subscription = $state(null);
    let trialStatus = $state(null);
    let loading = $state(true);
    let groupCount = $state(0);

    // Sync initial props to state (silences state_referenced_locally warning)
    $effect.pre(() => {
        subscription ??= initialSubscription;
        if (initialTrialAvailable && !trialStatus) {
            trialStatus = { can_activate: true };
        }
        if (initialGroups?.length && !groupCount) {
            groupCount = initialGroups.length;
        }
    });

    // Edit profile
    let editName = $state("");
    let savingProfile = $state(false);
    let profileMsg = $state({ type: "", text: "" });

    // Avatar color
    let selectedColor = $state("emerald");
    const avatarColors = [
        { name: "emerald", bg: "bg-emerald-500", ring: "ring-emerald-300" },
        { name: "blue", bg: "bg-blue-500", ring: "ring-blue-300" },
        { name: "purple", bg: "bg-purple-500", ring: "ring-purple-300" },
        { name: "rose", bg: "bg-rose-500", ring: "ring-rose-300" },
        { name: "amber", bg: "bg-amber-500", ring: "ring-amber-300" },
        { name: "cyan", bg: "bg-cyan-500", ring: "ring-cyan-300" },
        { name: "indigo", bg: "bg-indigo-500", ring: "ring-indigo-300" },
        { name: "slate", bg: "bg-slate-500", ring: "ring-slate-300" },
    ];

    // Change password
    let currentPassword = $state("");
    let newPassword = $state("");
    let confirmPassword = $state("");
    let savingPassword = $state(false);
    let passwordMsg = $state({ type: "", text: "" });

    // Notification prefs
    let notifyUsageLimit = $state(true);
    let notifyExpiry = $state(true);
    let savingNotifs = $state(false);
    let notifMsg = $state({ type: "", text: "" });

    // Dark mode
    let darkMode = $state(false);

    // Activity log
    let activities = $state([]);
    let loadingActivity = $state(true);

    // Delete account
    let showDeleteModal = $state(false);
    let deletePassword = $state("");
    let deleting = $state(false);
    let deleteError = $state("");

    // (Local upgrade modal logic removed, now using global UpgradeModal)

    onMount(async () => {
        // Load dark mode from localStorage
        darkMode = localStorage.getItem("darkMode") === "true";
        applyDarkMode();

        try {
            // Only fetch profile details + activity in parallel
            // subscription/trial/groups already passed as props
            const [me, actData] = await Promise.all([
                ApiService.getMe(),
                ApiService.getActivity().catch(() => ({ activities: [] })),
            ]);
            profile = me;
            editName = me.name;
            selectedColor = me.avatar_color || "emerald";
            notifyUsageLimit =
                me.notify_usage_limit !== undefined
                    ? me.notify_usage_limit
                    : true;
            notifyExpiry =
                me.notify_expiry !== undefined ? me.notify_expiry : true;
            activities = actData.activities || [];

            // Refresh subscription/trial from cache (fast, cached by api.js)
            if (!subscription) {
                subscription = await ApiService.getSubscriptionStatus();
            }
            if (!trialStatus) {
                try {
                    trialStatus = await ApiService.getTrialStatus();
                } catch {}
            }
        } catch (e) {
            console.error("Failed to load profile:", e);
        } finally {
            loading = false;
            loadingActivity = false;
        }

        // Load groups count if not passed
        if (!groupCount) {
            try {
                const groupData = await ApiService.listGroups();
                groupCount = groupData.groups?.length || 0;
            } catch {}
        }
    });

    function applyDarkMode() {
        if (darkMode) {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }
    }

    function toggleDarkMode() {
        darkMode = !darkMode;
        localStorage.setItem("darkMode", darkMode.toString());
        applyDarkMode();
    }

    async function saveProfile() {
        if (!editName.trim()) return;
        savingProfile = true;
        profileMsg = { type: "", text: "" };
        try {
            await ApiService.updateProfile({ name: editName.trim() });
            profile.name = editName.trim();
            const stored = JSON.parse(localStorage.getItem("user") || "{}");
            stored.name = editName.trim();
            localStorage.setItem("user", JSON.stringify(stored));
            profileMsg = {
                type: "success",
                text: "Profil berhasil diperbarui!",
            };
        } catch (e) {
            profileMsg = { type: "error", text: e.message };
        } finally {
            savingProfile = false;
        }
    }

    async function selectAvatarColor(color) {
        selectedColor = color;
        try {
            await ApiService.updateProfile({ avatar_color: color });
            if (profile) profile.avatar_color = color;
        } catch (e) {
            console.error("Failed to save avatar color:", e);
        }
    }

    async function saveNotificationPrefs() {
        savingNotifs = true;
        notifMsg = { type: "", text: "" };
        try {
            await ApiService.updateProfile({
                notify_usage_limit: notifyUsageLimit,
                notify_expiry: notifyExpiry,
            });
            notifMsg = {
                type: "success",
                text: "Preferensi notifikasi disimpan!",
            };
        } catch (e) {
            notifMsg = { type: "error", text: e.message };
        } finally {
            savingNotifs = false;
        }
    }

    async function savePassword() {
        passwordMsg = { type: "", text: "" };
        if (newPassword.length < 6) {
            passwordMsg = {
                type: "error",
                text: "Password baru minimal 6 karakter",
            };
            return;
        }
        if (newPassword !== confirmPassword) {
            passwordMsg = {
                type: "error",
                text: "Konfirmasi password tidak cocok",
            };
            return;
        }
        savingPassword = true;
        try {
            await ApiService.changePassword(currentPassword, newPassword);
            passwordMsg = {
                type: "success",
                text: "Password berhasil diubah!",
            };
            currentPassword = "";
            newPassword = "";
            confirmPassword = "";
        } catch (e) {
            passwordMsg = { type: "error", text: e.message };
        } finally {
            savingPassword = false;
        }
    }

    async function confirmDeleteAccount() {
        deleting = true;
        deleteError = "";
        try {
            await ApiService.deleteAccount(deletePassword);
            localStorage.clear();
            onLogout();
        } catch (e) {
            deleteError = e.message;
        } finally {
            deleting = false;
        }
    }

    function formatDate(iso) {
        if (!iso) return "-";
        const d = new Date(iso);
        return d.toLocaleDateString("id-ID", {
            day: "numeric",
            month: "short",
            year: "numeric",
        });
    }

    function formatDateTime(iso) {
        if (!iso) return "-";
        const d = new Date(iso);
        return d.toLocaleDateString("id-ID", {
            day: "numeric",
            month: "short",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    }

    function actionLabel(action) {
        if (action === "document_scan") return "Scan Dokumen";
        return action;
    }

    let planLabel = $derived(
        subscription?.plan === "pro" ? "Pro Plan" : "Free Plan",
    );
    let usagePercent = $derived(
        subscription?.usage_limit
            ? Math.min(
                  100,
                  Math.round(
                      (subscription.usage_count / subscription.usage_limit) *
                          100,
                  ),
              )
            : 0,
    );

    // Get current avatar bg class
    let avatarBg = $derived(
        avatarColors.find((c) => c.name === selectedColor)?.bg ||
            "bg-emerald-500",
    );
</script>

<div class="profile-page min-h-screen bg-slate-50">
    <!-- Mobile Header (sidebar handles desktop nav) -->
    <header
        class="lg:hidden bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10"
    >
        <h1 class="text-lg font-semibold text-slate-800">Profil</h1>
        <div class="flex items-center gap-2">
            <button
                type="button"
                onclick={toggleDarkMode}
                class="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                title={darkMode ? "Mode Terang" : "Mode Gelap"}
                aria-label={darkMode ? "Mode Terang" : "Mode Gelap"}
            >
                {#if darkMode}
                    <Sun class="h-5 w-5 text-amber-500" />
                {:else}
                    <Moon class="h-5 w-5 text-slate-500" />
                {/if}
            </button>
        </div>
    </header>

    {#if loading}
        <div class="loading-container">
            <div class="spinner"></div>
        </div>
    {:else if profile}
        <div class="profile-content">
            <div class="profile-grid">
                <!-- Left Column: Profile Card + Activity -->
                <div class="profile-col-left">
                    <!-- Profile Header Card -->
                    <div class="profile-card">
                        <div class="profile-header">
                            <div class="profile-header-inner">
                                <div class="avatar {avatarBg}">
                                    {profile.name?.charAt(0)?.toUpperCase() ||
                                        "U"}
                                </div>
                                <div class="profile-info">
                                    <h1 class="profile-name">
                                        {profile.name}
                                        {#if profile.is_admin}
                                            <span class="admin-badge">
                                                <Shield class="h-3 w-3" />
                                                Admin
                                            </span>
                                        {/if}
                                    </h1>
                                    <p class="profile-email">{profile.email}</p>
                                    <p class="profile-joined">
                                        Bergabung {formatDate(
                                            profile.created_at,
                                        )}
                                    </p>
                                </div>
                            </div>
                        </div>

                        <!-- Avatar Color Picker -->
                        <div class="avatar-picker">
                            <span class="picker-label">Warna Avatar</span>
                            <div class="color-options">
                                {#each avatarColors as color}
                                    <button
                                        onclick={() =>
                                            selectAvatarColor(color.name)}
                                        class="color-dot {color.bg} {selectedColor ===
                                        color.name
                                            ? 'ring-2 ring-offset-2 ' +
                                              color.ring
                                            : ''}"
                                        title={color.name}
                                        aria-label="Pilih warna {color.name}"
                                    ></button>
                                {/each}
                            </div>
                        </div>

                        <!-- Stats Row -->
                        <div class="stats-row">
                            <div class="stat-item">
                                <div class="stat-icon stat-icon-scan">
                                    <BarChart3 class="h-4 w-4" />
                                </div>
                                <div>
                                    <p class="stat-value">
                                        {profile.usage?.total ||
                                            0}{#if profile.usage?.limit}<span
                                                class="stat-limit"
                                                >/{profile.usage.limit}</span
                                            >{/if}
                                    </p>
                                    <p class="stat-label">Scan</p>
                                </div>
                            </div>
                            <div class="stat-divider"></div>
                            <div class="stat-item">
                                <div class="stat-icon stat-icon-group">
                                    <FolderOpen class="h-4 w-4" />
                                </div>
                                <div>
                                    <p class="stat-value">
                                        {groupCount}<span class="stat-limit"
                                            >/{subscription?.plan === "pro"
                                                ? "∞"
                                                : "2"}</span
                                        >
                                    </p>
                                    <p class="stat-label">Grup</p>
                                </div>
                            </div>
                            <div class="stat-divider"></div>
                            <div class="stat-item">
                                <div class="stat-icon stat-icon-plan">
                                    {#if subscription?.plan === "pro"}
                                        <Crown class="h-4 w-4" />
                                    {:else}
                                        <Zap class="h-4 w-4" />
                                    {/if}
                                </div>
                                <div>
                                    <p class="stat-value">{planLabel}</p>
                                    <p class="stat-label">Paket</p>
                                </div>
                            </div>
                        </div>

                        <!-- Usage Bar (free only) -->
                        {#if subscription?.plan === "free" && subscription?.usage_limit}
                            <div class="usage-bar-container">
                                <div class="usage-bar-track">
                                    <div
                                        class="usage-bar-fill {usagePercent > 80
                                            ? 'bar-red'
                                            : usagePercent > 50
                                              ? 'bar-amber'
                                              : 'bar-blue'}"
                                        style="width: {usagePercent}%"
                                    ></div>
                                </div>
                                <p class="usage-bar-text">
                                    {usagePercent}% kuota terpakai
                                </p>
                            </div>
                        {/if}

                        <!-- Subscription Details -->
                        <div class="subscription-details">
                            {#if subscription?.plan === "pro"}
                                <div class="sub-detail-row">
                                    <span class="sub-detail-label"
                                        >Berlangganan sejak</span
                                    >
                                    <span class="sub-detail-value"
                                        >{formatDate(
                                            subscription.subscribed_at,
                                        )}</span
                                    >
                                </div>
                                <div class="sub-detail-row">
                                    <span class="sub-detail-label"
                                        >Berlaku hingga</span
                                    >
                                    <span class="sub-detail-value"
                                        >{formatDate(
                                            subscription.subscription_ends,
                                        )}</span
                                    >
                                </div>
                            {:else}
                                {#if subscription?.trial_ends && subscription?.status === "trial"}
                                    <div class="sub-detail-row">
                                        <Clock
                                            class="h-3.5 w-3.5 text-amber-500"
                                        />
                                        <span class="sub-detail-label"
                                            >Trial berakhir</span
                                        >
                                        <span class="sub-detail-value"
                                            >{formatDate(
                                                subscription.trial_ends,
                                            )}</span
                                        >
                                    </div>
                                {/if}
                                <button
                                    onclick={onUpgradeRequest}
                                    class="upgrade-btn-full"
                                >
                                    <Crown class="h-4 w-4" />
                                    Upgrade ke Pro — Rp80.000/bulan
                                </button>
                                {#if trialStatus?.can_activate}
                                    <button
                                        onclick={onUpgradeRequest}
                                        class="upgrade-btn-full"
                                        style="background: linear-gradient(135deg, #8b5cf6, #6d28d9); margin-top: 8px;"
                                    >
                                        🎁 Coba Pro 7 Hari GRATIS
                                    </button>
                                {/if}
                            {/if}
                        </div>
                    </div>

                    <!-- Recent Activity -->
                    <div class="form-card">
                        <h2 class="form-title">
                            <Activity class="h-5 w-5 text-slate-400" />
                            Aktivitas Terakhir
                        </h2>
                        {#if loadingActivity}
                            <div class="activity-loading">
                                <Loader2
                                    class="h-5 w-5 animate-spin text-slate-300"
                                />
                            </div>
                        {:else if activities.length === 0}
                            <p class="activity-empty">
                                Belum ada aktivitas scan.
                            </p>
                        {:else}
                            <div class="activity-list">
                                {#each activities as act}
                                    <div class="activity-row">
                                        <div class="activity-dot"></div>
                                        <div class="activity-info">
                                            <span class="activity-action"
                                                >{actionLabel(act.action)}</span
                                            >
                                            <span class="activity-count"
                                                >{act.count} dokumen</span
                                            >
                                        </div>
                                        <span class="activity-date"
                                            >{formatDateTime(
                                                act.created_at,
                                            )}</span
                                        >
                                    </div>
                                {/each}
                            </div>
                        {/if}
                    </div>
                </div>

                <!-- Right Column: Settings -->
                <div class="profile-col-right">
                    <!-- Edit Profile Card -->
                    <div class="form-card">
                        <h2 class="form-title">
                            <User class="h-5 w-5 text-slate-400" />
                            Edit Profil
                        </h2>

                        <div class="form-fields">
                            <div>
                                <label for="profile-email" class="field-label"
                                    >Email</label
                                >
                                <input
                                    id="profile-email"
                                    type="email"
                                    value={profile.email}
                                    disabled
                                    class="field-input field-disabled"
                                />
                                <p class="field-hint">
                                    Email tidak dapat diubah
                                </p>
                            </div>

                            <div>
                                <label for="profile-name" class="field-label"
                                    >Nama Lengkap</label
                                >
                                <input
                                    id="profile-name"
                                    type="text"
                                    bind:value={editName}
                                    class="field-input"
                                    placeholder="Nama lengkap"
                                />
                            </div>

                            {#if profileMsg.text}
                                <div
                                    class="msg {profileMsg.type === 'success'
                                        ? 'msg-success'
                                        : 'msg-error'}"
                                >
                                    {#if profileMsg.type === "success"}
                                        <CheckCircle class="h-4 w-4" />
                                    {:else}
                                        <AlertCircle class="h-4 w-4" />
                                    {/if}
                                    {profileMsg.text}
                                </div>
                            {/if}

                            <button
                                onclick={saveProfile}
                                disabled={savingProfile ||
                                    editName.trim() === profile.name}
                                class="save-btn"
                            >
                                <Save class="h-4 w-4" />
                                {savingProfile
                                    ? "Menyimpan..."
                                    : "Simpan Perubahan"}
                            </button>
                        </div>
                    </div>

                    <!-- Notification Preferences -->
                    <div class="form-card">
                        <h2 class="form-title">
                            <Bell class="h-5 w-5 text-slate-400" />
                            Notifikasi
                        </h2>
                        <div class="form-fields">
                            <div class="toggle-row">
                                <div>
                                    <p class="toggle-label">
                                        Peringatan batas kuota
                                    </p>
                                    <p class="toggle-desc">
                                        Notifikasi saat mendekati batas scan
                                    </p>
                                </div>
                                <button
                                    onclick={() =>
                                        (notifyUsageLimit = !notifyUsageLimit)}
                                    class="toggle-switch {notifyUsageLimit
                                        ? 'toggle-on'
                                        : 'toggle-off'}"
                                    aria-label="Toggle Peringatan batas kuota"
                                >
                                    <span
                                        class="toggle-knob {notifyUsageLimit
                                            ? 'knob-on'
                                            : 'knob-off'}"
                                    ></span>
                                </button>
                            </div>
                            <div class="toggle-row">
                                <div>
                                    <p class="toggle-label">
                                        Peringatan masa berlaku
                                    </p>
                                    <p class="toggle-desc">
                                        Notifikasi sebelum trial/langganan
                                        berakhir
                                    </p>
                                </div>
                                <button
                                    onclick={() =>
                                        (notifyExpiry = !notifyExpiry)}
                                    class="toggle-switch {notifyExpiry
                                        ? 'toggle-on'
                                        : 'toggle-off'}"
                                    aria-label="Toggle Peringatan masa berlaku"
                                >
                                    <span
                                        class="toggle-knob {notifyExpiry
                                            ? 'knob-on'
                                            : 'knob-off'}"
                                    ></span>
                                </button>
                            </div>

                            {#if notifMsg.text}
                                <div
                                    class="msg {notifMsg.type === 'success'
                                        ? 'msg-success'
                                        : 'msg-error'}"
                                >
                                    {#if notifMsg.type === "success"}
                                        <CheckCircle class="h-4 w-4" />
                                    {:else}
                                        <AlertCircle class="h-4 w-4" />
                                    {/if}
                                    {notifMsg.text}
                                </div>
                            {/if}

                            <button
                                onclick={saveNotificationPrefs}
                                disabled={savingNotifs}
                                class="save-btn"
                            >
                                <Save class="h-4 w-4" />
                                {savingNotifs
                                    ? "Menyimpan..."
                                    : "Simpan Preferensi"}
                            </button>
                        </div>
                    </div>

                    <!-- Change Password Card -->
                    <div class="form-card">
                        <h2 class="form-title">
                            <Lock class="h-5 w-5 text-slate-400" />
                            Ubah Password
                        </h2>

                        <div class="form-fields">
                            <div>
                                <label
                                    for="current-password"
                                    class="field-label">Password Saat Ini</label
                                >
                                <input
                                    id="current-password"
                                    type="password"
                                    bind:value={currentPassword}
                                    class="field-input"
                                    placeholder="Masukkan password saat ini"
                                />
                            </div>

                            <div>
                                <label for="new-password" class="field-label"
                                    >Password Baru</label
                                >
                                <input
                                    id="new-password"
                                    type="password"
                                    bind:value={newPassword}
                                    class="field-input"
                                    placeholder="Minimal 6 karakter"
                                />
                            </div>

                            <div>
                                <label
                                    for="confirm-password"
                                    class="field-label"
                                    >Konfirmasi Password Baru</label
                                >
                                <input
                                    id="confirm-password"
                                    type="password"
                                    bind:value={confirmPassword}
                                    class="field-input"
                                    placeholder="Ulangi password baru"
                                />
                            </div>

                            {#if passwordMsg.text}
                                <div
                                    class="msg {passwordMsg.type === 'success'
                                        ? 'msg-success'
                                        : 'msg-error'}"
                                >
                                    {#if passwordMsg.type === "success"}
                                        <CheckCircle class="h-4 w-4" />
                                    {:else}
                                        <AlertCircle class="h-4 w-4" />
                                    {/if}
                                    {passwordMsg.text}
                                </div>
                            {/if}

                            <button
                                onclick={savePassword}
                                disabled={savingPassword ||
                                    !currentPassword ||
                                    !newPassword ||
                                    !confirmPassword}
                                class="save-btn save-btn-dark"
                            >
                                <Lock class="h-4 w-4" />
                                {savingPassword
                                    ? "Mengubah..."
                                    : "Ubah Password"}
                            </button>
                        </div>
                    </div>

                    <!-- Danger Zone -->
                    <div class="form-card danger-card">
                        <h2 class="form-title danger-title">
                            <Trash2 class="h-5 w-5 text-red-400" />
                            Zona Berbahaya
                        </h2>
                        <p class="danger-desc">
                            Hapus akun secara permanen. Semua data grup dan
                            riwayat akan dihapus. Tindakan ini tidak dapat
                            dibatalkan.
                        </p>
                        <button
                            onclick={() => (showDeleteModal = true)}
                            class="delete-btn"
                        >
                            <Trash2 class="h-4 w-4" />
                            Hapus Akun Saya
                        </button>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>

<!-- Delete Account Modal -->
{#if showDeleteModal}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="modal-overlay"
        onclick={() => (showDeleteModal = false)}
        onkeydown={(e) => {
            if (e.key === "Escape") showDeleteModal = false;
        }}
        role="dialog"
        aria-modal="true"
        tabindex="-1"
    >
        <!-- svelte-ignore a11y_no_static_element_interactions -->
        <div
            class="modal-content"
            onclick={(e) => e.stopPropagation()}
            onkeydown={() => {}}
        >
            <div class="modal-header">
                <h3 class="modal-title" style="color: #ef4444;">
                    <Trash2 class="h-5 w-5" />
                    Hapus Akun
                </h3>
                <button
                    onclick={() => (showDeleteModal = false)}
                    class="modal-close">✕</button
                >
            </div>
            <div class="modal-body">
                <p class="delete-warning">
                    Tindakan ini <strong>tidak dapat dibatalkan</strong>.
                    Masukkan password untuk konfirmasi.
                </p>
                <input
                    type="password"
                    bind:value={deletePassword}
                    placeholder="Password akun"
                    class="field-input"
                />
                {#if deleteError}
                    <div class="msg msg-error">
                        <AlertCircle class="h-4 w-4" />
                        {deleteError}
                    </div>
                {/if}
                <div class="delete-actions">
                    <button
                        onclick={() => (showDeleteModal = false)}
                        class="cancel-btn">Batal</button
                    >
                    <button
                        onclick={confirmDeleteAccount}
                        disabled={deleting || !deletePassword}
                        class="confirm-delete-btn"
                    >
                        {#if deleting}
                            <Loader2 class="h-4 w-4 animate-spin" />
                        {:else}
                            <Trash2 class="h-4 w-4" />
                        {/if}
                        Hapus Permanen
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

<style>
    /* ---- Base ---- */
    .profile-page {
        background: #f8fafc;
        min-height: 100vh;
    }
    :global(.dark) .profile-page {
        background: #0f172a;
    }

    /* ---- Navbar ---- */
    .profile-nav {
        border-bottom: 1px solid #e2e8f0;
        background: #fff;
        padding: 0.75rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    :global(.dark) .profile-nav {
        background: #1e293b;
        border-color: #334155;
    }
    @media (min-width: 640px) {
        .profile-nav {
            padding: 1rem 1.5rem;
        }
    }
    .nav-left {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    @media (min-width: 640px) {
        .nav-left {
            gap: 0.75rem;
        }
    }
    .back-btn {
        color: #64748b;
        background: none;
        border: none;
        padding: 0.5rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: color 0.2s;
        display: flex;
        align-items: center;
    }
    .back-btn:hover {
        color: #334155;
    }
    :global(.dark) .back-btn {
        color: #94a3b8;
    }
    :global(.dark) .back-btn:hover {
        color: #f1f5f9;
    }
    .logout-btn {
        color: #64748b;
        font-size: 0.875rem;
        background: none;
        border: none;
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: color 0.2s;
    }
    .logout-btn:hover {
        color: #ef4444;
    }

    /* ---- Loading ---- */
    .loading-container {
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 5rem 0;
    }
    .spinner {
        width: 2rem;
        height: 2rem;
        border: 2px solid transparent;
        border-bottom-color: #10b981;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }

    /* ---- Content Container ---- */
    .profile-content {
        max-width: 72rem;
        margin: 0 auto;
        padding: 1.25rem 1rem 2rem;
    }
    @media (min-width: 640px) {
        .profile-content {
            padding: 1.5rem 1.5rem 2rem;
        }
    }
    @media (min-width: 1024px) {
        .profile-content {
            padding: 2rem 2rem 3rem;
        }
    }

    /* ---- Two-Column Grid ---- */
    .profile-grid {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    @media (min-width: 640px) {
        .profile-grid {
            gap: 1.25rem;
        }
    }
    @media (min-width: 1024px) {
        .profile-grid {
            display: grid;
            grid-template-columns: 380px 1fr;
            gap: 1.5rem;
            align-items: start;
        }
    }
    .profile-col-left {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    @media (min-width: 1024px) {
        .profile-col-left {
            position: sticky;
            top: 4.5rem;
            gap: 1.25rem;
        }
    }
    .profile-col-right {
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }
    @media (min-width: 640px) {
        .profile-col-right {
            gap: 1.25rem;
        }
    }

    /* ---- Profile Card ---- */
    .profile-card {
        background: #fff;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        overflow: hidden;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    :global(.dark) .profile-card {
        background: #1e293b;
        border-color: #334155;
    }

    /* ---- Profile Header ---- */
    .profile-header {
        background: linear-gradient(135deg, #10b981, #0d9488);
        padding: 1.25rem 1rem;
        color: white;
    }
    @media (min-width: 640px) {
        .profile-header {
            padding: 1.5rem;
        }
    }
    .profile-header-inner {
        display: flex;
        align-items: center;
        gap: 0.75rem;
    }
    @media (min-width: 640px) {
        .profile-header-inner {
            gap: 1rem;
        }
    }
    .avatar {
        width: 3.5rem;
        height: 3.5rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        font-weight: 700;
        flex-shrink: 0;
        color: white;
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.3);
    }
    @media (min-width: 640px) {
        .avatar {
            width: 4rem;
            height: 4rem;
            font-size: 1.5rem;
        }
    }
    .profile-info {
        min-width: 0;
    }
    .profile-name {
        font-size: 1.1rem;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    @media (min-width: 640px) {
        .profile-name {
            font-size: 1.25rem;
        }
    }
    .admin-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.125rem 0.5rem;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 99px;
        font-size: 0.7rem;
        font-weight: 500;
    }
    .profile-email {
        color: rgba(167, 243, 208, 0.9);
        font-size: 0.8rem;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    .profile-joined {
        color: rgba(167, 243, 208, 0.6);
        font-size: 0.7rem;
        margin-top: 0.125rem;
    }

    /* ---- Avatar Color Picker ---- */
    .avatar-picker {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f1f5f9;
    }
    :global(.dark) .avatar-picker {
        border-color: #334155;
    }
    .picker-label {
        font-size: 0.75rem;
        color: #64748b;
        white-space: nowrap;
    }
    .color-options {
        display: flex;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    .color-dot {
        width: 1.5rem;
        height: 1.5rem;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        transition: transform 0.15s;
    }
    .color-dot:hover {
        transform: scale(1.2);
    }

    /* ---- Stats Row ---- */
    .stats-row {
        display: flex;
        align-items: center;
        padding: 1rem;
        gap: 0.75rem;
    }
    @media (min-width: 640px) {
        .stats-row {
            padding: 1rem 1.5rem;
        }
    }
    .stat-item {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .stat-icon {
        width: 2rem;
        height: 2rem;
        border-radius: 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .stat-icon-scan {
        background: #dbeafe;
        color: #2563eb;
    }
    .stat-icon-group {
        background: #d1fae5;
        color: #059669;
    }
    .stat-icon-plan {
        background: #fef3c7;
        color: #d97706;
    }
    :global(.dark) .stat-icon-scan {
        background: #1e3a5f;
    }
    :global(.dark) .stat-icon-group {
        background: #064e3b;
    }
    :global(.dark) .stat-icon-plan {
        background: #451a03;
    }
    .stat-value {
        font-weight: 700;
        font-size: 1rem;
        color: #1e293b;
        line-height: 1.2;
    }
    :global(.dark) .stat-value {
        color: #f1f5f9;
    }
    .stat-limit {
        font-weight: 400;
        font-size: 0.8rem;
        color: #94a3b8;
    }
    .stat-label {
        font-size: 0.7rem;
        color: #94a3b8;
    }
    .stat-divider {
        width: 1px;
        height: 2rem;
        background: #e2e8f0;
    }
    :global(.dark) .stat-divider {
        background: #334155;
    }

    /* ---- Usage Bar ---- */
    .usage-bar-container {
        padding: 0 1rem 1rem;
    }
    @media (min-width: 640px) {
        .usage-bar-container {
            padding: 0 1.5rem 1rem;
        }
    }
    .usage-bar-track {
        width: 100%;
        height: 0.5rem;
        background: #f1f5f9;
        border-radius: 99px;
        overflow: hidden;
    }
    :global(.dark) .usage-bar-track {
        background: #334155;
    }
    .usage-bar-fill {
        height: 100%;
        border-radius: 99px;
        transition: width 0.5s ease;
    }
    .bar-red {
        background: #f87171;
    }
    .bar-amber {
        background: #fbbf24;
    }
    .bar-blue {
        background: #60a5fa;
    }
    .usage-bar-text {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 0.25rem;
        text-align: right;
    }

    /* ---- Subscription Details ---- */
    .subscription-details {
        padding: 0.75rem 1rem 1rem;
        border-top: 1px solid #f1f5f9;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    :global(.dark) .subscription-details {
        border-color: #334155;
    }
    .sub-detail-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.8rem;
    }
    .sub-detail-label {
        color: #64748b;
    }
    .sub-detail-value {
        color: #1e293b;
        font-weight: 500;
        margin-left: auto;
    }
    :global(.dark) .sub-detail-value {
        color: #e2e8f0;
    }
    .upgrade-btn-full {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.625rem;
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
        font-size: 0.8rem;
        font-weight: 600;
        border-radius: 0.75rem;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
        margin-top: 0.25rem;
    }
    .upgrade-btn-full:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35);
    }
    .wa-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.625rem;
        background: #dcfce7;
        color: #166534;
        font-size: 0.8rem;
        font-weight: 500;
        border-radius: 0.75rem;
        text-decoration: none;
        transition: background 0.2s;
    }
    .wa-btn:hover {
        background: #bbf7d0;
    }
    :global(.dark) .wa-btn {
        background: #064e3b;
        color: #6ee7b7;
    }

    /* ---- Form Card ---- */
    .form-card {
        background: #fff;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        padding: 1.25rem 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    :global(.dark) .form-card {
        background: #1e293b;
        border-color: #334155;
    }
    @media (min-width: 640px) {
        .form-card {
            padding: 1.5rem;
        }
    }
    .form-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 1rem;
    }
    :global(.dark) .form-title {
        color: #f1f5f9;
    }
    .form-fields {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
    }

    /* ---- Fields ---- */
    .field-label {
        display: block;
        font-size: 0.8rem;
        font-weight: 500;
        color: #475569;
        margin-bottom: 0.25rem;
    }
    :global(.dark) .field-label {
        color: #94a3b8;
    }
    .field-input {
        width: 100%;
        padding: 0.625rem 0.75rem;
        border: 1px solid #e2e8f0;
        border-radius: 0.75rem;
        font-size: 0.875rem;
        color: #1e293b;
        background: #fff;
        outline: none;
        transition:
            border-color 0.2s,
            box-shadow 0.2s;
        box-sizing: border-box;
    }
    :global(.dark) .field-input {
        background: #0f172a;
        border-color: #334155;
        color: #e2e8f0;
    }
    .field-input:focus {
        border-color: #10b981;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
    }
    .field-disabled {
        background: #f8fafc;
        color: #94a3b8;
        cursor: not-allowed;
    }
    :global(.dark) .field-disabled {
        background: #1e293b;
        color: #64748b;
    }
    .field-hint {
        font-size: 0.7rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }

    /* ---- Toggle Switch ---- */
    .toggle-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.5rem 0;
    }
    .toggle-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #1e293b;
    }
    :global(.dark) .toggle-label {
        color: #e2e8f0;
    }
    .toggle-desc {
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .toggle-switch {
        position: relative;
        width: 2.75rem;
        height: 1.5rem;
        border-radius: 99px;
        border: none;
        cursor: pointer;
        transition: background 0.2s;
        flex-shrink: 0;
    }
    .toggle-on {
        background: #10b981;
    }
    .toggle-off {
        background: #cbd5e1;
    }
    :global(.dark) .toggle-off {
        background: #475569;
    }
    .toggle-knob {
        position: absolute;
        top: 2px;
        width: 1.25rem;
        height: 1.25rem;
        background: white;
        border-radius: 50%;
        transition: left 0.2s;
    }
    .knob-on {
        left: calc(100% - 1.25rem - 2px);
    }
    .knob-off {
        left: 2px;
    }

    /* ---- Messages ---- */
    .msg {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.75rem;
        border-radius: 0.5rem;
        font-size: 0.8rem;
    }
    .msg-success {
        background: #d1fae5;
        color: #065f46;
    }
    :global(.dark) .msg-success {
        background: #064e3b;
        color: #6ee7b7;
    }
    .msg-error {
        background: #fee2e2;
        color: #991b1b;
    }
    :global(.dark) .msg-error {
        background: #450a0a;
        color: #fca5a5;
    }

    /* ---- Save Buttons ---- */
    .save-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.625rem;
        background: #10b981;
        color: white;
        font-size: 0.875rem;
        font-weight: 600;
        border-radius: 0.75rem;
        border: none;
        cursor: pointer;
        transition: all 0.2s;
    }
    .save-btn:hover:not(:disabled) {
        background: #059669;
    }
    .save-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .save-btn-dark {
        background: #334155;
    }
    .save-btn-dark:hover:not(:disabled) {
        background: #1e293b;
    }

    /* ---- Activity Log ---- */
    .activity-loading {
        display: flex;
        justify-content: center;
        padding: 1.5rem;
    }
    .activity-empty {
        text-align: center;
        color: #94a3b8;
        font-size: 0.85rem;
        padding: 1.5rem 0;
    }
    .activity-list {
        display: flex;
        flex-direction: column;
        gap: 0;
    }
    .activity-row {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.625rem 0;
        border-bottom: 1px solid #f1f5f9;
    }
    :global(.dark) .activity-row {
        border-color: #334155;
    }
    .activity-row:last-child {
        border-bottom: none;
    }
    .activity-dot {
        width: 0.5rem;
        height: 0.5rem;
        border-radius: 50%;
        background: #10b981;
        flex-shrink: 0;
    }
    .activity-info {
        flex: 1;
        display: flex;
        flex-direction: column;
        min-width: 0;
    }
    .activity-action {
        font-size: 0.85rem;
        font-weight: 500;
        color: #1e293b;
    }
    :global(.dark) .activity-action {
        color: #e2e8f0;
    }
    .activity-count {
        font-size: 0.7rem;
        color: #94a3b8;
    }
    .activity-date {
        font-size: 0.7rem;
        color: #94a3b8;
        white-space: nowrap;
    }

    /* ---- Danger Zone ---- */
    .danger-card {
        border-color: #fecaca;
    }
    :global(.dark) .danger-card {
        border-color: #450a0a;
    }
    .danger-title {
        color: #ef4444 !important;
    }
    .danger-desc {
        font-size: 0.8rem;
        color: #64748b;
        margin-bottom: 1rem;
        line-height: 1.5;
    }
    .delete-btn {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.625rem 1.25rem;
        background: #fee2e2;
        color: #dc2626;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 0.75rem;
        border: 1px solid #fecaca;
        cursor: pointer;
        transition: all 0.2s;
    }
    .delete-btn:hover {
        background: #fecaca;
    }

    /* ---- Modals ---- */
    .modal-overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 50;
        padding: 1rem;
    }
    .modal-content {
        background: #fff;
        border-radius: 1rem;
        width: 100%;
        max-width: 24rem;
        overflow: hidden;
        box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
    }
    :global(.dark) .modal-content {
        background: #1e293b;
    }
    .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 1.25rem;
        border-bottom: 1px solid #f1f5f9;
    }
    :global(.dark) .modal-header {
        border-color: #334155;
    }
    .modal-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1rem;
        font-weight: 600;
        color: #1e293b;
    }
    :global(.dark) .modal-title {
        color: #f1f5f9;
    }
    .modal-close {
        background: none;
        border: none;
        color: #94a3b8;
        font-size: 1.25rem;
        cursor: pointer;
        padding: 0.25rem;
    }
    .modal-body {
        padding: 1.25rem;
        display: flex;
        flex-direction: column;
        gap: 1rem;
    }

    /* ---- Delete Modal ---- */
    .delete-warning {
        font-size: 0.85rem;
        color: #64748b;
        line-height: 1.5;
    }
    :global(.dark) .delete-warning {
        color: #94a3b8;
    }
    .delete-actions {
        display: flex;
        gap: 0.75rem;
        justify-content: flex-end;
    }
    .cancel-btn {
        padding: 0.5rem 1rem;
        background: #f1f5f9;
        color: #475569;
        border: none;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        cursor: pointer;
        font-weight: 500;
    }
    .cancel-btn:hover {
        background: #e2e8f0;
    }
    .confirm-delete-btn {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        padding: 0.5rem 1rem;
        background: #ef4444;
        color: white;
        border: none;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
    }
    .confirm-delete-btn:hover:not(:disabled) {
        background: #dc2626;
    }
    .confirm-delete-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }

    /* ---- Upgrade Modal ---- */
    .price-box {
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #d1fae5, #cffafe);
        border-radius: 0.75rem;
    }
    :global(.dark) .price-box {
        background: linear-gradient(135deg, #064e3b, #083344);
    }
    .price-amount {
        font-size: 1.75rem;
        font-weight: 700;
        color: #059669;
    }
    :global(.dark) .price-amount {
        color: #6ee7b7;
    }
    .price-period {
        font-size: 0.8rem;
        color: #64748b;
    }
    .price-alt {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-top: 0.25rem;
    }
    .transfer-box {
        background: #f8fafc;
        padding: 0.75rem;
        border-radius: 0.75rem;
        border: 1px solid #e2e8f0;
    }
    :global(.dark) .transfer-box {
        background: #0f172a;
        border-color: #334155;
    }
    .transfer-label {
        font-size: 0.75rem;
        color: #94a3b8;
        margin-bottom: 0.25rem;
    }
    .transfer-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .transfer-number {
        font-weight: 700;
        font-size: 0.9rem;
        color: #1e293b;
    }
    :global(.dark) .transfer-number {
        color: #f1f5f9;
    }
    .copy-btn {
        display: flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.75rem;
        color: #10b981;
        background: none;
        border: none;
        cursor: pointer;
        font-weight: 500;
    }
    .wa-confirm-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.75rem;
        background: #22c55e;
        color: white;
        font-size: 0.85rem;
        font-weight: 600;
        border-radius: 0.75rem;
        text-decoration: none;
        transition: background 0.2s;
    }
    .wa-confirm-btn:hover {
        background: #16a34a;
    }
</style>

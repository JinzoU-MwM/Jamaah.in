<!--
  WhatsAppBlast.svelte — Send template messages to jamaah via WhatsApp
  Uses wa.me deep links (zero cost, no API needed)
-->
<script>
    import {
        X,
        Send,
        MessageCircle,
        Eye,
        Users,
        ExternalLink,
        Loader2,
    } from "lucide-svelte";
    import { ApiService } from "../services/api.js";

    let { isOpen = false, onClose, group = null } = $props();

    // State
    let members = $state([]);
    let isLoading = $state(true);
    let selectedTemplate = $state("room_info");
    let customMessage = $state("");
    let showPreview = $state(false);
    let sentCount = $state(0);
    let isBulkSending = $state(false);

    // Templates
    const templates = {
        room_info: {
            label: "Info Kamar Hotel",
            icon: "🏨",
            message: `Assalamu'alaikum {nama},\n\nBerikut info kamar hotel Anda:\n🏨 *Kamar: {no_kamar}*\n\nMohon hadir di lobby hotel sesuai jadwal.\n\nTerima kasih.\n— {agency}`,
        },
        departure_reminder: {
            label: "Pengingat Keberangkatan",
            icon: "✈️",
            message: `Assalamu'alaikum {nama},\n\nMengingatkan keberangkatan:\n📅 Tanggal: {tanggal}\n👕 Ukuran baju: {baju_size}\n\nPastikan semua dokumen sudah siap:\n✅ Paspor\n✅ Visa\n✅ Tiket\n\nTerima kasih.\n— {agency}`,
        },
        general_info: {
            label: "Informasi Umum",
            icon: "📢",
            message: `Assalamu'alaikum {nama},\n\n{pesan}\n\nTerima kasih.\n— {agency}`,
        },
        custom: {
            label: "Pesan Custom",
            icon: "✏️",
            message: "",
        },
    };

    let activeTemplate = $derived(
        selectedTemplate === "custom"
            ? { ...templates.custom, message: customMessage }
            : templates[selectedTemplate],
    );

    // Load group members when opened
    $effect(() => {
        if (isOpen && group) {
            loadMembers();
        }
    });

    async function loadMembers() {
        isLoading = true;
        sentCount = 0;
        try {
            const fullGroup = await ApiService.getGroup(group.id);
            members = (fullGroup.members || []).map((m) => ({
                ...m,
                sent: false,
                hasPhone: !!(m.no_hp || "").trim(),
            }));
        } catch (e) {
            console.error("Failed to load members:", e);
        } finally {
            isLoading = false;
        }
    }

    function formatPhone(phone) {
        if (!phone) return "";
        let cleaned = phone.replace(/[\s\-\(\)]/g, "");
        if (cleaned.startsWith("0")) cleaned = "62" + cleaned.slice(1);
        if (!cleaned.startsWith("62") && !cleaned.startsWith("+62"))
            cleaned = "62" + cleaned;
        cleaned = cleaned.replace(/^\+/, "");
        return cleaned;
    }

    function fillTemplate(template, member) {
        let msg = template;
        msg = msg.replace(
            /{nama}/g,
            member.nama || member.nama_paspor || "Bpk/Ibu",
        );
        msg = msg.replace(
            /{no_kamar}/g,
            member.room_number || member.no_kamar || "-",
        );
        msg = msg.replace(/{baju_size}/g, member.baju_size || "-");
        msg = msg.replace(/{tanggal}/g, "{tanggal}"); // User fills manually
        msg = msg.replace(/{pesan}/g, "{pesan}"); // User fills manually
        msg = msg.replace(/{agency}/g, "Jamaah.in");
        return msg;
    }

    function getWaUrl(member) {
        const phone = formatPhone(member.no_hp);
        const message = fillTemplate(activeTemplate.message, member);
        return `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
    }

    function sendSingle(member, index) {
        window.open(getWaUrl(member), "_blank");
        members[index] = { ...members[index], sent: true };
        sentCount++;
    }

    async function sendBulk() {
        const unsent = members.filter((m, i) => m.hasPhone && !m.sent);
        if (unsent.length === 0) return;

        isBulkSending = true;
        for (let i = 0; i < members.length; i++) {
            const m = members[i];
            if (!m.hasPhone || m.sent) continue;

            window.open(getWaUrl(m), "_blank");
            members[i] = { ...members[i], sent: true };
            sentCount++;

            // Delay between opens to avoid popup blocking
            if (i < members.length - 1) {
                await new Promise((r) => setTimeout(r, 800));
            }
        }
        isBulkSending = false;
    }

    let membersWithPhone = $derived(members.filter((m) => m.hasPhone));
    let membersWithoutPhone = $derived(members.filter((m) => !m.hasPhone));
    let previewMember = $derived(
        membersWithPhone.length > 0
            ? membersWithPhone[0]
            : {
                  nama: "Ahmad",
                  no_hp: "08123456789",
                  no_kamar: "F-001",
                  baju_size: "L",
              },
    );
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_no_static_element_interactions a11y_click_events_have_key_events -->
    <div
        class="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onclick={onClose}
        onkeydown={(e) => {
            if (e.key === "Escape") onClose();
        }}
        role="button"
        tabindex="-1"
    >
        <!-- svelte-ignore a11y_click_events_have_key_events -->
        <div
            class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col"
            onclick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            tabindex="-1"
        >
            <!-- Header -->
            <div
                class="flex items-center justify-between px-5 py-4 border-b border-slate-200 dark:border-slate-700"
            >
                <div class="flex items-center gap-2.5">
                    <div
                        class="w-9 h-9 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center"
                    >
                        <MessageCircle class="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                        <h2
                            class="font-bold text-slate-800 dark:text-slate-100"
                        >
                            WhatsApp Blast
                        </h2>
                        <p class="text-xs text-slate-500">
                            {group?.name || "Grup"} · {membersWithPhone.length} punya
                            nomor HP
                        </p>
                    </div>
                </div>
                <button
                    onclick={onClose}
                    class="p-1.5 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                    aria-label="Tutup"
                >
                    <X class="h-5 w-5 text-slate-400" />
                </button>
            </div>

            <!-- Body -->
            <div class="flex-1 overflow-auto p-5 space-y-5">
                <!-- Template Selector -->
                <div>
                    <span
                        class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
                        >Template Pesan</span
                    >
                    <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {#each Object.entries(templates) as [key, tpl]}
                            <button
                                type="button"
                                onclick={() => (selectedTemplate = key)}
                                class="p-2.5 rounded-xl border-2 text-left transition-all text-xs
                  {selectedTemplate === key
                                    ? 'border-green-400 bg-green-50 dark:bg-green-900/20'
                                    : 'border-slate-200 dark:border-slate-600 hover:border-slate-300'}"
                            >
                                <span class="text-lg">{tpl.icon}</span>
                                <p
                                    class="font-medium text-slate-700 dark:text-slate-200 mt-1"
                                >
                                    {tpl.label}
                                </p>
                            </button>
                        {/each}
                    </div>
                </div>

                <!-- Custom Message Editor (only for custom template) -->
                {#if selectedTemplate === "custom"}
                    <div>
                        <span
                            class="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1"
                        >
                            Tulis Pesan
                            <span
                                class="text-xs text-slate-400 font-normal ml-1"
                                >Variabel: {"{nama}"}, {"{no_kamar}"}, {"{baju_size}"}</span
                            >
                        </span>
                        <textarea
                            bind:value={customMessage}
                            rows="5"
                            placeholder="Assalamu'alaikum ..."
                            class="w-full px-4 py-3 border border-slate-200 dark:border-slate-600 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-green-400 bg-white dark:bg-slate-700 dark:text-slate-100 resize-none"
                        ></textarea>
                    </div>
                {/if}

                <!-- Preview -->
                <div>
                    <button
                        type="button"
                        onclick={() => (showPreview = !showPreview)}
                        class="flex items-center gap-1.5 text-sm text-green-600 hover:text-green-700 font-medium mb-2"
                    >
                        <Eye class="w-4 h-4" />
                        {showPreview ? "Sembunyikan" : "Lihat"} Preview
                    </button>
                    {#if showPreview}
                        <div
                            class="bg-slate-50 dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-700"
                        >
                            <p class="text-xs text-slate-400 mb-2">
                                Preview untuk: <strong
                                    >{previewMember.nama || "Jamaah"}</strong
                                >
                            </p>
                            <pre
                                class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-sans">{fillTemplate(
                                    activeTemplate.message,
                                    previewMember,
                                )}</pre>
                        </div>
                    {/if}
                </div>

                <!-- Member List -->
                <div>
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <Users class="w-4 h-4 text-slate-400" />
                            <span
                                class="text-sm font-medium text-slate-700 dark:text-slate-300"
                                >Daftar Jamaah</span
                            >
                        </div>

                        {#if sentCount > 0}
                            <span class="text-xs text-green-600 font-medium"
                                >{sentCount}/{membersWithPhone.length} terkirim</span
                            >
                        {/if}
                    </div>

                    {#if isLoading}
                        <div
                            class="flex items-center justify-center py-6 text-slate-400"
                        >
                            <Loader2 class="h-5 w-5 animate-spin mr-2" />
                            Memuat data...
                        </div>
                    {:else}
                        <div class="space-y-1.5 max-h-60 overflow-auto">
                            {#each members as member, i}
                                <div
                                    class="flex items-center justify-between px-3 py-2 rounded-lg {member.sent
                                        ? 'bg-green-50 dark:bg-green-900/20'
                                        : 'bg-white dark:bg-slate-700'} border border-slate-100 dark:border-slate-600"
                                >
                                    <div class="flex-1 min-w-0">
                                        <p
                                            class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate"
                                        >
                                            {member.nama ||
                                                member.nama_paspor ||
                                                "-"}
                                        </p>
                                        <p
                                            class="text-xs text-slate-400 truncate"
                                        >
                                            {#if member.hasPhone}
                                                📱 {member.no_hp}
                                            {:else}
                                                <span class="text-amber-500"
                                                    >⚠ Tidak ada nomor HP</span
                                                >
                                            {/if}
                                        </p>
                                    </div>
                                    {#if member.hasPhone}
                                        {#if member.sent}
                                            <span
                                                class="text-xs text-green-600 font-medium px-2 py-1 bg-green-100 dark:bg-green-800/30 rounded-lg"
                                                >✓ Sent</span
                                            >
                                        {:else}
                                            <button
                                                type="button"
                                                onclick={() =>
                                                    sendSingle(member, i)}
                                                class="px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white text-xs font-medium rounded-lg flex items-center gap-1.5 transition-colors"
                                            >
                                                <Send class="w-3 h-3" />
                                                Kirim
                                            </button>
                                        {/if}
                                    {/if}
                                </div>
                            {/each}
                        </div>

                        {#if membersWithoutPhone.length > 0}
                            <p class="text-xs text-amber-500 mt-2">
                                ⚠ {membersWithoutPhone.length} jamaah tanpa nomor
                                HP
                            </p>
                        {/if}
                    {/if}
                </div>
            </div>

            <!-- Footer -->
            <div
                class="px-5 py-4 border-t border-slate-200 dark:border-slate-700 flex items-center justify-between gap-3"
            >
                <p class="text-xs text-slate-400">
                    Membuka WhatsApp per-jamaah via wa.me
                </p>
                <div class="flex gap-2">
                    <button
                        type="button"
                        onclick={onClose}
                        class="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        Tutup
                    </button>
                    <button
                        type="button"
                        onclick={sendBulk}
                        disabled={isBulkSending ||
                            membersWithPhone.length === 0 ||
                            !activeTemplate.message}
                        class="px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-300 text-white text-sm font-medium rounded-lg flex items-center gap-2 transition-colors"
                    >
                        {#if isBulkSending}
                            <Loader2 class="w-4 h-4 animate-spin" />
                            Mengirim...
                        {:else}
                            <ExternalLink class="w-4 h-4" />
                            Kirim Semua ({membersWithPhone.filter(
                                (m) => !m.sent,
                            ).length})
                        {/if}
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}

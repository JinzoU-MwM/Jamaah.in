<script>
  import { MessageCircle, Send, X, Plus } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let isOpen = $state(false);
  let isLoading = $state(false);
  let tickets = $state([]);
  let activeTicket = $state(null);
  let draft = $state("");
  let createMode = $state(false);
  let newSubject = $state("");
  let newMessage = $state("");
  let error = $state("");

  function formatTime(iso) {
    if (!iso) return "";
    try {
      return new Date(iso).toLocaleString("id-ID", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  }

  async function loadTickets() {
    try {
      tickets = await ApiService.listMyTickets({ limit: 20 });
      if (!activeTicket && tickets.length > 0) {
        await openTicket(tickets[0].id);
      }
    } catch (e) {
      error = e?.message || "Gagal memuat tiket";
    }
  }

  async function openTicket(ticketId) {
    isLoading = true;
    error = "";
    try {
      activeTicket = await ApiService.getMyTicketDetail(ticketId);
      createMode = false;
    } catch (e) {
      error = e?.message || "Gagal memuat detail tiket";
    } finally {
      isLoading = false;
    }
  }

  async function createTicket() {
    if (!newSubject.trim() || !newMessage.trim()) return;
    isLoading = true;
    error = "";
    try {
      const res = await ApiService.createTicket(
        newSubject.trim(),
        newMessage.trim(),
        "medium",
      );
      newSubject = "";
      newMessage = "";
      createMode = false;
      await loadTickets();
      if (res?.ticket_id) {
        await openTicket(res.ticket_id);
      }
    } catch (e) {
      error = e?.message || "Gagal membuat tiket";
    } finally {
      isLoading = false;
    }
  }

  async function sendReply() {
    if (!activeTicket?.id || !draft.trim()) return;
    isLoading = true;
    error = "";
    try {
      await ApiService.replyToTicket(activeTicket.id, draft.trim());
      draft = "";
      await openTicket(activeTicket.id);
      await loadTickets();
    } catch (e) {
      error = e?.message || "Gagal mengirim pesan";
    } finally {
      isLoading = false;
    }
  }

  $effect(() => {
    let interval;
    if (isOpen) {
      loadTickets();
      interval = setInterval(() => {
        if (activeTicket?.id) {
          openTicket(activeTicket.id);
        } else {
          loadTickets();
        }
      }, 15000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  });
</script>

<div class="fixed right-4 bottom-4 z-[70]">
  {#if isOpen}
    <div class="w-[22rem] max-w-[calc(100vw-2rem)] h-[30rem] bg-white border border-slate-200 shadow-2xl rounded-2xl overflow-hidden flex flex-col">
      <div class="px-4 py-3 border-b border-slate-200 bg-emerald-50 flex items-center justify-between">
        <div>
          <p class="text-sm font-semibold text-slate-800">Support Chat</p>
          <p class="text-[11px] text-slate-500">Hubungi admin support</p>
        </div>
        <button
          type="button"
          class="p-1.5 rounded-lg hover:bg-white"
          onclick={() => (isOpen = false)}
          aria-label="Tutup support"
        >
          <X class="w-4 h-4 text-slate-500" />
        </button>
      </div>

      <div class="px-3 py-2 border-b border-slate-100 flex items-center gap-2">
        <button
          type="button"
          class="px-2.5 py-1.5 rounded-lg text-xs font-medium border border-slate-200 hover:bg-slate-50"
          onclick={() => {
            createMode = true;
            activeTicket = null;
          }}
        >
          <span class="inline-flex items-center gap-1">
            <Plus class="w-3.5 h-3.5" /> Tiket Baru
          </span>
        </button>
      </div>

      {#if error}
        <div class="mx-3 mt-2 px-3 py-2 text-xs rounded-lg bg-red-50 text-red-700 border border-red-200">
          {error}
        </div>
      {/if}

      {#if createMode}
        <div class="flex-1 p-3 space-y-2 overflow-y-auto">
          <input
            type="text"
            bind:value={newSubject}
            placeholder="Subjek masalah"
            class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-300"
          />
          <textarea
            rows="7"
            bind:value={newMessage}
            placeholder="Tulis kendala Anda..."
            class="w-full px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-300"
          ></textarea>
          <button
            type="button"
            class="w-full px-3 py-2 rounded-lg bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
            onclick={createTicket}
            disabled={isLoading || !newSubject.trim() || !newMessage.trim()}
          >
            {isLoading ? "Mengirim..." : "Kirim Tiket"}
          </button>
        </div>
      {:else if activeTicket}
        <div class="px-3 pt-2 pb-1 border-b border-slate-100">
          <p class="text-xs font-semibold text-slate-700 truncate">{activeTicket.subject}</p>
          <p class="text-[11px] text-slate-500">Status: {activeTicket.status}</p>
        </div>

        <div class="flex-1 p-3 overflow-y-auto bg-slate-50">
          {#if activeTicket.messages?.length}
            <div class="space-y-2">
              {#each activeTicket.messages as msg}
                <div class="flex {msg.sender_type === 'user' ? 'justify-end' : 'justify-start'}">
                  <div class="{msg.sender_type === 'user' ? 'bg-emerald-600 text-white' : 'bg-white text-slate-700 border border-slate-200'} max-w-[85%] px-3 py-2 rounded-2xl text-xs leading-relaxed">
                    <p>{msg.content}</p>
                    <p class="{msg.sender_type === 'user' ? 'text-emerald-100' : 'text-slate-400'} mt-1 text-[10px]">
                      {formatTime(msg.created_at)}
                    </p>
                  </div>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-xs text-slate-500 text-center mt-6">Belum ada pesan</p>
          {/if}
        </div>

        <div class="p-2.5 border-t border-slate-200 bg-white flex items-end gap-2">
          <textarea
            rows="1"
            bind:value={draft}
            placeholder="Tulis pesan..."
            class="flex-1 resize-none px-3 py-2 text-sm rounded-lg border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-300"
          ></textarea>
          <button
            type="button"
            class="p-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50"
            onclick={sendReply}
            disabled={isLoading || !draft.trim()}
            aria-label="Kirim pesan"
          >
            <Send class="w-4 h-4" />
          </button>
        </div>
      {:else}
        <div class="flex-1 p-3 overflow-y-auto">
          {#if isLoading}
            <p class="text-xs text-slate-500 text-center mt-6">Memuat tiket...</p>
          {:else if tickets.length > 0}
            <div class="space-y-2">
              {#each tickets as ticket}
                <button
                  type="button"
                  class="w-full text-left p-3 rounded-xl border border-slate-200 hover:bg-slate-50"
                  onclick={() => openTicket(ticket.id)}
                >
                  <p class="text-xs font-semibold text-slate-700 truncate">{ticket.subject}</p>
                  <p class="text-[11px] text-slate-500 mt-0.5">Status: {ticket.status} • {ticket.message_count} pesan</p>
                </button>
              {/each}
            </div>
          {:else}
            <div class="text-center mt-8">
              <p class="text-xs text-slate-500">Belum ada tiket support.</p>
              <p class="text-xs text-slate-400 mt-1">Klik "Tiket Baru" untuk mulai chat.</p>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}

  <button
    type="button"
    class="mt-3 ml-auto w-14 h-14 rounded-full bg-emerald-600 text-white shadow-lg hover:bg-emerald-700 flex items-center justify-center"
    onclick={() => {
      isOpen = !isOpen;
      if (!isOpen) {
        createMode = false;
      }
    }}
    aria-label="Buka support chat"
  >
    <MessageCircle class="w-6 h-6" />
  </button>
</div>

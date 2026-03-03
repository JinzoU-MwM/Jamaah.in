<!--
  RegistrationLinkModal.svelte — Admin modal to generate/manage registration links
-->
<script>
  import { onMount } from "svelte";
  import {
    X,
    Copy,
    Check,
    Loader2,
    Link,
    Calendar,
    AlertCircle,
  } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let { groupId, onClose } = $props();

  let link = $state(null);
  let loading = $state(true);
  let generating = $state(false);
  let copied = $state(false);
  let error = $state("");

  onMount(async () => {
    await loadLink();
  });

  async function loadLink() {
    loading = true;
    error = "";
    try {
      const res = await ApiService.getRegistrationLink(groupId);
      if (res.active) {
        link = res;
      } else {
        link = null;
      }
    } catch (e) {
      console.error("Failed to load link:", e);
    } finally {
      loading = false;
    }
  }

  async function generateLink() {
    generating = true;
    error = "";
    try {
      const res = await ApiService.generateRegistrationLink(groupId, 30);
      link = res;
    } catch (e) {
      error = e.message || "Gagal membuat link";
    } finally {
      generating = false;
    }
  }

  async function copyLink() {
    if (!link?.link) return;
    try {
      await navigator.clipboard.writeText(link.link);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch (e) {
      // Fallback for non-https environments (like local LAN testing)
      const textArea = document.createElement("textarea");
      textArea.value = link.link;
      document.body.appendChild(textArea);
      textArea.select();
      try {
        document.execCommand("copy");
        copied = true;
        setTimeout(() => (copied = false), 2000);
      } catch (fallbackErr) {
        error = "Gagal menyalin link. Silakan copy manual.";
        console.error("Fallback copy failed", fallbackErr);
      }
      document.body.removeChild(textArea);
    }
  }

  async function revokeLink() {
    if (!confirm("Yakin ingin menonaktifkan link ini?")) return;
    try {
      await ApiService.revokeRegistrationLink(groupId);
      link = null;
    } catch (e) {
      error = e.message || "Gagal menonaktifkan link";
    }
  }

  function formatDate(isoString) {
    return new Date(isoString).toLocaleDateString("id-ID", {
      day: "numeric",
      month: "long",
      year: "numeric",
    });
  }
</script>

<div class="modal-overlay" onclick={onClose} role="button" tabindex="-1">
  <div class="modal" onclick={(e) => e.stopPropagation()}>
    <div class="modal-header">
      <div class="header-title">
        <Link class="w-5 h-5 text-emerald-500" />
        <h3>Link Pendaftaran</h3>
      </div>
      <button type="button" class="close-btn" onclick={onClose}>
        <X class="w-5 h-5" />
      </button>
    </div>

    <div class="modal-body">
      {#if loading}
        <div class="loading">
          <Loader2 class="w-6 h-6 animate-spin text-emerald-500" />
          <p>Memuat...</p>
        </div>
      {:else if error}
        <div class="error">
          <AlertCircle class="w-5 h-5" />
          {error}
        </div>
      {:else if link}
        <div class="link-info">
          <label>Link Pendaftaran</label>
          <div class="link-box">
            <input type="text" value={link.link} readonly />
            <button type="button" class="copy-btn" onclick={copyLink}>
              {#if copied}
                <Check class="w-4 h-4 text-emerald-500" />
              {:else}
                <Copy class="w-4 h-4" />
              {/if}
            </button>
          </div>

          <div class="expiry">
            <Calendar class="w-4 h-4" />
            <span
              >Berlaku hingga: <strong>{formatDate(link.expires_at)}</strong
              ></span
            >
          </div>

          {#if link.is_expired}
            <div class="expired-badge">Link sudah kadaluarsa</div>
          {/if}

          <button type="button" class="revoke-btn" onclick={revokeLink}>
            Nonaktifkan Link
          </button>

          <p class="hint">
            Bagikan link ini ke jamaah via WhatsApp untuk pendaftaran mandiri.
          </p>
        </div>
      {:else}
        <div class="no-link">
          <Link class="w-12 h-12 text-slate-300" />
          <p>Belum ada link pendaftaran untuk grup ini.</p>
          <button
            type="button"
            class="generate-btn"
            onclick={generateLink}
            disabled={generating}
          >
            {#if generating}
              <Loader2 class="w-4 h-4 animate-spin" />
              Membuat...
            {:else}
              Buat Link Pendaftaran
            {/if}
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
    padding: 1rem;
  }

  .modal {
    background: white;
    border-radius: 0.75rem;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #e2e8f0;
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .header-title h3 {
    font-weight: 600;
    color: #0f172a;
  }

  .close-btn {
    padding: 0.375rem;
    background: transparent;
    border: none;
    cursor: pointer;
    color: #64748b;
    border-radius: 0.375rem;
  }

  .close-btn:hover {
    background: #f1f5f9;
  }

  .modal-body {
    padding: 1.25rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 2rem;
    color: #64748b;
  }

  .loading p {
    margin-top: 0.5rem;
    font-size: 0.875rem;
  }

  .error {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem;
    background: #fef2f2;
    color: #dc2626;
    border-radius: 0.5rem;
    font-size: 0.875rem;
  }

  .link-info label {
    display: block;
    font-size: 0.75rem;
    font-weight: 500;
    color: #64748b;
    margin-bottom: 0.5rem;
  }

  .link-box {
    display: flex;
    gap: 0.5rem;
  }

  .link-box input {
    flex: 1;
    padding: 0.625rem 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 0.8125rem;
    background: #f8fafc;
  }

  .copy-btn {
    padding: 0.625rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    cursor: pointer;
    color: #64748b;
  }

  .copy-btn:hover {
    background: #f1f5f9;
  }

  .expiry {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.75rem;
    font-size: 0.8125rem;
    color: #64748b;
  }

  .expiry strong {
    color: #0f172a;
  }

  .expired-badge {
    margin-top: 0.75rem;
    padding: 0.5rem;
    background: #fef2f2;
    color: #dc2626;
    font-size: 0.75rem;
    font-weight: 500;
    text-align: center;
    border-radius: 0.375rem;
  }

  .revoke-btn {
    width: 100%;
    margin-top: 1rem;
    padding: 0.625rem;
    background: #fef2f2;
    color: #dc2626;
    border: none;
    border-radius: 0.5rem;
    font-size: 0.8125rem;
    font-weight: 500;
    cursor: pointer;
  }

  .revoke-btn:hover {
    background: #fee2e2;
  }

  .hint {
    margin-top: 1rem;
    font-size: 0.75rem;
    color: #9ca3af;
    text-align: center;
  }

  .no-link {
    text-align: center;
    padding: 1.5rem;
  }

  .no-link p {
    margin: 1rem 0;
    color: #64748b;
    font-size: 0.875rem;
  }

  .generate-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.875rem;
  }

  .generate-btn:hover:not(:disabled) {
    transform: translateY(-1px);
  }

  .generate-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>

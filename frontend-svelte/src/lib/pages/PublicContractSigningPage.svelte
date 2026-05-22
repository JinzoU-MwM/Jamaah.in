<script>
  import { onMount } from 'svelte';
  import { AlertCircle, CheckCircle2, Loader2, PenSquare, ShieldCheck, Type } from 'lucide-svelte';
  import BrandLogo from '../components/BrandLogo.svelte';
  import { ApiService } from '../services/api';

  let { token } = $props();

  let loading = $state(true);
  let signing = $state(false);
  let error = $state('');
  let contract = $state(null);
  let consentAccepted = $state(false);
  let scrolledToBottom = $state(false);
  let signatureMode = $state('draw');
  let typedName = $state('');
  let drawnSignature = $state('');
  let canvasEl = $state(null);
  let isDrawing = $state(false);
  let showSignedState = $derived(contract?.status === 'ditandatangani');

  onMount(async () => {
    await loadContract();
  });

  async function loadContract() {
    loading = true;
    error = '';
    try {
      const response = await ApiService.getPublicContract(token);
      contract = response.data ?? response;
      typedName = contract?.signed_name || contract?.recipient_name || '';
    } catch (e) {
      error = e.message || 'Link kontrak tidak valid atau sudah kadaluarsa.';
      contract = null;
    } finally {
      loading = false;
    }
  }

  function formatDate(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString('id-ID', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }

  function renderHtml(content) {
    return String(content || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  }

  function handleScroll(event) {
    const node = event.currentTarget;
    const remaining = node.scrollHeight - node.scrollTop - node.clientHeight;
    if (remaining <= 8) {
      scrolledToBottom = true;
    }
  }

  function pointerPosition(event) {
    const rect = canvasEl?.getBoundingClientRect();
    if (!rect) return null;
    const source = event.touches?.[0] || event;
    return {
      x: source.clientX - rect.left,
      y: source.clientY - rect.top,
    };
  }

  function ensureCanvasContext() {
    const ctx = canvasEl?.getContext('2d');
    if (!ctx) return null;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#0f172a';
    return ctx;
  }

  function startDraw(event) {
    const pos = pointerPosition(event);
    const ctx = ensureCanvasContext();
    if (!pos || !ctx) return;
    isDrawing = true;
    ctx.beginPath();
    ctx.moveTo(pos.x, pos.y);
    event.preventDefault();
  }

  function moveDraw(event) {
    if (!isDrawing) return;
    const pos = pointerPosition(event);
    const ctx = ensureCanvasContext();
    if (!pos || !ctx) return;
    ctx.lineTo(pos.x, pos.y);
    ctx.stroke();
    drawnSignature = canvasEl.toDataURL('image/png');
    event.preventDefault();
  }

  function stopDraw() {
    if (!isDrawing) return;
    isDrawing = false;
    drawnSignature = canvasEl?.toDataURL('image/png') || drawnSignature;
  }

  function clearSignature() {
    const ctx = canvasEl?.getContext('2d');
    if (!ctx || !canvasEl) return;
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
    drawnSignature = '';
  }

  async function submitSignature() {
    if (!contract?.can_sign) return;
    error = '';
    const signatureValue = signatureMode === 'draw' ? drawnSignature : typedName.trim();
    if (!typedName.trim()) {
      error = 'Nama penandatangan wajib diisi.';
      return;
    }
    if (!signatureValue) {
      error = signatureMode === 'draw' ? 'Tanda tangan belum dibuat.' : 'Nama ketik wajib diisi.';
      return;
    }

    signing = true;
    try {
      const response = await ApiService.signPublicContract(token, {
        signed_name: typedName.trim(),
        signature_mode: signatureMode,
        signature_value: signatureValue,
        consent_accepted: consentAccepted,
        scrolled_to_bottom: scrolledToBottom,
      });
      contract = response.data ?? response;
    } catch (e) {
      error = e.message || 'Gagal menandatangani kontrak.';
    } finally {
      signing = false;
    }
  }
</script>

<div class="min-h-screen bg-[linear-gradient(180deg,#f7efe0_0%,#fffaf2_42%,#ffffff_100%)] text-slate-900">
  <div class="mx-auto max-w-4xl px-4 py-6 sm:px-6 lg:px-8">
    <div class="mb-8 flex items-center justify-between">
      <BrandLogo size="small" />
      <span class="rounded-full bg-white/80 px-3 py-1 text-xs font-semibold text-slate-500 shadow-sm backdrop-blur">Tanda Tangan Digital</span>
    </div>

    {#if loading}
      <div class="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-slate-500">
        <Loader2 class="h-8 w-8 animate-spin" />
        <p>Memuat kontrak...</p>
      </div>
    {:else if error && !contract}
      <div class="flex min-h-[50vh] flex-col items-center justify-center gap-3 rounded-3xl border border-red-100 bg-white p-10 text-center shadow-sm">
        <AlertCircle class="h-10 w-10 text-red-500" />
        <h1 class="text-xl font-bold">Kontrak tidak tersedia</h1>
        <p class="max-w-md text-sm text-slate-500">{error}</p>
      </div>
    {:else if contract}
      <section class="overflow-hidden rounded-[32px] border border-amber-100 bg-white shadow-[0_30px_80px_-40px_rgba(120,53,15,0.35)]">
        <div class="relative overflow-hidden border-b border-amber-100 bg-[radial-gradient(circle_at_top_left,#fde68a_0%,#f59e0b_32%,#78350f_100%)] px-6 py-10 text-white sm:px-10">
          <div class="absolute -right-16 top-0 h-40 w-40 rounded-full bg-white/10 blur-2xl"></div>
          <div class="absolute bottom-0 left-0 h-24 w-24 rounded-full bg-black/10 blur-2xl"></div>
          <div class="relative max-w-3xl">
            <p class="mb-3 text-xs font-bold uppercase tracking-[0.3em] text-amber-100">E-Kontrak Jamaah</p>
            <h1 class="text-3xl font-black leading-tight sm:text-5xl">{contract.template_name}</h1>
            <p class="mt-4 max-w-2xl text-sm leading-relaxed text-amber-50 sm:text-base">
              Dokumen atas nama <span class="font-bold text-white">{contract.recipient_name}</span>. Link aktif sampai {formatDate(contract.expires_at)}.
            </p>
            <div class="mt-6 flex flex-wrap gap-3 text-sm">
              <span class="rounded-full bg-white/15 px-4 py-2 backdrop-blur">{contract.status}</span>
              {#if contract.document_hash}
                <span class="rounded-full bg-white/15 px-4 py-2 backdrop-blur">SHA-256 tersimpan</span>
              {/if}
            </div>
          </div>
        </div>

        <div class="grid gap-8 px-6 py-8 sm:px-10 lg:grid-cols-[1.05fr_0.95fr]">
          <div class="space-y-5">
            <div class="rounded-3xl border border-slate-200 bg-slate-50 p-4">
              <div class="mb-3 flex items-center gap-2 text-slate-700">
                <ShieldCheck class="h-4 w-4 text-emerald-600" />
                <span class="text-sm font-semibold">Baca sampai selesai sebelum tanda tangan</span>
              </div>
              <div
                class="max-h-[420px] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 text-sm leading-relaxed text-slate-700"
                onscroll={handleScroll}
              >
                {@html renderHtml(contract.rendered_content)}
              </div>
              <p class="mt-3 text-xs font-medium {scrolledToBottom ? 'text-emerald-700' : 'text-slate-500'}">
                {#if scrolledToBottom}
                  Anda sudah mencapai bagian akhir kontrak.
                {:else}
                  Scroll hingga bagian paling bawah untuk mengaktifkan tanda tangan.
                {/if}
              </p>
            </div>
          </div>

          <aside class="rounded-3xl border border-slate-200 bg-slate-50 p-6">
            {#if showSignedState}
              <div class="rounded-3xl border border-emerald-200 bg-white p-6 text-center shadow-sm">
                <CheckCircle2 class="mx-auto h-10 w-10 text-emerald-600" />
                <h2 class="mt-4 text-xl font-bold text-slate-900">Kontrak sudah ditandatangani</h2>
                <p class="mt-2 text-sm text-slate-500">Ditandatangani oleh {contract.signed_name} pada {formatDate(contract.signed_at)}.</p>
                {#if contract.document_hash}
                  <div class="mt-4 rounded-2xl bg-slate-50 px-4 py-3 text-left text-xs text-slate-500">
                    <p class="font-bold uppercase tracking-wide text-slate-400">Hash Dokumen</p>
                    <p class="mt-1 break-all">{contract.document_hash}</p>
                  </div>
                {/if}
              </div>
            {:else}
              <h2 class="text-lg font-bold">Tanda Tangan Jamaah</h2>
              <p class="mt-2 text-sm text-slate-500">Pilih cara tanda tangan. Link otomatis expired setelah 7 hari jika belum ditandatangani.</p>

              {#if error}
                <div class="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
                  {error}
                </div>
              {/if}

              <div class="mt-5 grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onclick={() => (signatureMode = 'draw')}
                  class="inline-flex items-center justify-center gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition-colors {signatureMode === 'draw' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}"
                >
                  <PenSquare class="h-4 w-4" />
                  Draw
                </button>
                <button
                  type="button"
                  onclick={() => (signatureMode = 'type')}
                  class="inline-flex items-center justify-center gap-2 rounded-2xl border px-4 py-3 text-sm font-semibold transition-colors {signatureMode === 'type' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50'}"
                >
                  <Type class="h-4 w-4" />
                  Type
                </button>
              </div>

              <div class="mt-5">
                <label for="signed-name" class="mb-1 block text-sm font-medium text-slate-700">Nama Penandatangan</label>
                <input
                  id="signed-name"
                  type="text"
                  bind:value={typedName}
                  class="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 outline-none transition-colors focus:border-primary-400 focus:ring-2 focus:ring-primary-100"
                />
              </div>

              {#if signatureMode === 'draw'}
                <div class="mt-5">
                  <div class="mb-2 flex items-center justify-between">
                    <p class="block text-sm font-medium text-slate-700">Area Tanda Tangan</p>
                    <button type="button" onclick={clearSignature} class="text-xs font-semibold text-primary-600">Bersihkan</button>
                  </div>
                  <canvas
                    bind:this={canvasEl}
                    width="520"
                    height="220"
                    class="w-full rounded-3xl border border-dashed border-slate-300 bg-white touch-none"
                    onmousedown={startDraw}
                    onmousemove={moveDraw}
                    onmouseup={stopDraw}
                    onmouseleave={stopDraw}
                    ontouchstart={startDraw}
                    ontouchmove={moveDraw}
                    ontouchend={stopDraw}
                  ></canvas>
                </div>
              {:else}
                <div class="mt-5 rounded-3xl border border-slate-200 bg-white p-5">
                  <p class="text-xs font-bold uppercase tracking-wide text-slate-400">Preview Nama Tertanam</p>
                  <p class="mt-4 font-serif text-2xl italic text-slate-900">{typedName || 'Nama Anda akan muncul di sini'}</p>
                </div>
              {/if}

              <label class="mt-5 flex items-start gap-3 rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                <input type="checkbox" bind:checked={consentAccepted} class="mt-0.5 rounded border-slate-300" />
                <span>{contract.consent_statement}</span>
              </label>

              <button
                type="button"
                onclick={submitSignature}
                disabled={!contract.can_sign || !consentAccepted || !scrolledToBottom || signing}
                class="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-4 text-sm font-bold text-white transition-colors hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {#if signing}
                  <Loader2 class="h-4 w-4 animate-spin" />
                  Memproses...
                {:else}
                  Tanda Tangani Kontrak
                {/if}
              </button>

              <p class="mt-3 text-xs leading-relaxed text-slate-500">
                Sistem menyimpan waktu penandatanganan, IP address, dan hash dokumen untuk verifikasi integritas.
              </p>
            {/if}
          </aside>
        </div>
      </section>
    {/if}
  </div>
</div>

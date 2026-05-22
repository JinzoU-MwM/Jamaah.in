<script>
  import { X } from 'lucide-svelte';

  let {
    open = false,
    title = '',
    width = '540px',
    onClose,
    children,
  } = $props();
</script>

{#if open}
  <!-- Backdrop -->
  <button
    type="button"
    class="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-[2px] transition-opacity"
    onclick={onClose}
    aria-label="Tutup"
  ></button>

  <!-- Drawer panel -->
  <div
    class="fixed right-0 top-0 z-50 flex h-full flex-col bg-white shadow-2xl transition-transform duration-300"
    style="width: min({width}, 100vw);"
    role="dialog"
    aria-modal="true"
    aria-label={title}
  >
    <!-- Header -->
    {#if title}
      <div class="flex h-16 flex-shrink-0 items-center justify-between border-b border-slate-100 px-6">
        <h2 class="text-base font-semibold text-slate-800">{title}</h2>
        <button
          type="button"
          onclick={onClose}
          class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          aria-label="Tutup"
        >
          <X class="h-5 w-5" />
        </button>
      </div>
    {:else}
      <div class="flex h-12 flex-shrink-0 items-center justify-end px-6 border-b border-slate-100">
        <button
          type="button"
          onclick={onClose}
          class="flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
          aria-label="Tutup"
        >
          <X class="h-5 w-5" />
        </button>
      </div>
    {/if}

    <!-- Scrollable content -->
    <div class="flex-1 overflow-y-auto">
      {@render children?.()}
    </div>
  </div>
{/if}

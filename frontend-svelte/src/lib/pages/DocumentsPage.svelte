<script>
  import { ClipboardList, Plus } from 'lucide-svelte';
  let { onNavigate, user = null } = $props();
</script>

<div class="flex h-screen flex-col">
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Dokumen & Paspor</h1>
        <p class="mt-0.5 text-sm text-slate-500">Checklist kelengkapan dokumen jamaah per trip</p>
      </div>
    </div>
  </div>
  <div class="flex flex-1 flex-col items-center justify-center gap-4 bg-slate-50 text-slate-400">
    <ClipboardList class="h-16 w-16 opacity-20" />
    <div class="text-center">
      <p class="font-semibold text-slate-600">Modul Dokumen & Paspor</p>
      <p class="mt-1 text-sm">Akan tersedia setelah backend endpoint siap.</p>
    </div>
  </div>
</div>

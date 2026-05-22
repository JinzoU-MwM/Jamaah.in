<script>
  import { Building2, Plus } from 'lucide-svelte';
  let { onNavigate, user = null } = $props();
</script>

<div class="flex h-screen flex-col">
  <div class="flex-shrink-0 border-b border-slate-100 bg-white px-6 py-5">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-xl font-bold text-slate-800">Vendor & Biaya Ops</h1>
        <p class="mt-0.5 text-sm text-slate-500">Kelola vendor dan catat pengeluaran operasional per trip</p>
      </div>
      <button type="button" class="flex items-center gap-2 rounded-xl bg-primary-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-700">
        <Plus class="h-4 w-4" /> Tambah Vendor
      </button>
    </div>
  </div>
  <div class="flex flex-1 flex-col items-center justify-center gap-4 bg-slate-50 text-slate-400">
    <Building2 class="h-16 w-16 opacity-20" />
    <div class="text-center">
      <p class="font-semibold text-slate-600">Modul Vendor & Biaya Ops</p>
      <p class="mt-1 text-sm">Akan tersedia setelah backend endpoint siap.</p>
    </div>
  </div>
</div>

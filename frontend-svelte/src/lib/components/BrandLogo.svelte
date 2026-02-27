<script>
  import { UsersRound, ArrowRightToLine } from 'lucide-svelte';
  
  let { size = 'default', iconOnly = false } = $props();
  
  const sizeClasses = {
    small: 'text-xl',
    default: 'text-2xl',
    large: 'text-3xl'
  };
  
  const iconSizes = {
    small: 'h-5 w-5',
    default: 'h-6 w-6',
    large: 'h-8 w-8'
  };
</script>

{#if iconOnly}
  <!-- Icon only mode for collapsed sidebar -->
  <div class="flex items-center justify-center">
    <div class="flex items-center">
      <UsersRound class="{iconSizes[size]} text-emerald-500" />
    </div>
  </div>
{:else}
  <!-- Full logo with icon and text -->
  <div class="flex items-center gap-2">
    <!-- Icon Group: Users + Arrow (Login/Entry Concept) -->
    <div class="flex items-center -space-x-1">
      <UsersRound class="{iconSizes[size]} text-emerald-500" />
      <ArrowRightToLine class="{iconSizes[size]} text-emerald-600" />
    </div>
    
    <!-- Brand Text -->
    <span class="{sizeClasses[size]} font-bold text-slate-800">
      Jamaah<span class="text-emerald-500">.in</span>
    </span>
  </div>
{/if}

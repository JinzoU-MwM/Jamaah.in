<script>
  import { ArrowRightToLine, UsersRound } from 'lucide-svelte';
  
  let { size = 'default', iconOnly = false, variant = 'default' } = $props();
  
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

  const textColor = $derived(variant === 'light' ? 'text-white' : 'text-slate-950');
  const dotColor = $derived(variant === 'light' ? 'text-emerald-400' : 'text-emerald-500');
  const peopleColor = $derived(variant === 'light' ? 'text-emerald-400' : 'text-emerald-500');
  const arrowColor = $derived(variant === 'light' ? 'text-emerald-300' : 'text-emerald-600');
</script>

{#if iconOnly}
  <div class="flex items-center justify-center">
    <div class="flex items-center {peopleColor}">
      <UsersRound class={iconSizes[size]} strokeWidth={2.35} />
    </div>
  </div>
{:else}
  <div class="flex items-center gap-2">
    <div class="flex items-center -space-x-1 {peopleColor}">
      <UsersRound class={iconSizes[size]} strokeWidth={2.25} />
      <ArrowRightToLine class="{iconSizes[size]} {arrowColor}" strokeWidth={2.35} />
    </div>

    <span class="{sizeClasses[size]} font-black tracking-normal {textColor}">
      Jamaah<span class={dotColor}>.in</span>
    </span>
  </div>
{/if}

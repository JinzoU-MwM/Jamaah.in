<script>
  export let count = 5;
  export let type = 'row'; // 'row' or 'card'
</script>

<div class="space-y-3">
  {#each Array(count) as _}
    {#if type === 'row'}
      <div class="animate-pulse flex items-center space-x-4">
        <div class="h-12 w-12 rounded bg-gray-200 dark:bg-gray-700"></div>
        <div class="flex-1 space-y-2">
          <div class="h-4 w-3/4 rounded bg-gray-200 dark:bg-gray-700"></div>
          <div class="h-4 w-1/2 rounded bg-gray-200 dark:bg-gray-700"></div>
        </div>
      </div>
    {:else}
      <div class="animate-pulse rounded-lg border bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="h-6 w-1/3 rounded bg-gray-200 dark:bg-gray-700"></div>
        <div class="mt-3 space-y-2">
          <div class="h-4 w-full rounded bg-gray-200 dark:bg-gray-700"></div>
          <div class="h-4 w-2/3 rounded bg-gray-200 dark:bg-gray-700"></div>
        </div>
      </div>
    {/if}
  {/each}
</div>

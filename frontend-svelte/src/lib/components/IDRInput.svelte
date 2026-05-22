<script>
  /**
   * IDRInput — currency input in IDR.
   * Binds to a numeric `value` prop (raw integer, e.g. 25000000).
   * Displays formatted: "Rp 25.000.000"
   */
  let {
    value = $bindable(0),
    label = '',
    placeholder = '0',
    required = false,
    disabled = false,
    error = '',
    class: extraClass = '',
  } = $props();

  function formatIDR(num) {
    if (!num && num !== 0) return '';
    return new Intl.NumberFormat('id-ID').format(num);
  }

  function parseIDR(str) {
    const cleaned = str.replace(/[^\d]/g, '');
    return cleaned ? parseInt(cleaned, 10) : 0;
  }

  let displayValue = $state(formatIDR(value));

  function handleInput(e) {
    const raw = parseIDR(e.target.value);
    value = raw;
    // Reformat in-place, preserve cursor won't jump since we set value after
    displayValue = formatIDR(raw);
    // Svelte won't patch the DOM if we just set a new $state immediately,
    // so we set the input element's value directly:
    e.target.value = displayValue;
  }

  function handleFocus(e) {
    // Select all on focus for easy replacement
    e.target.select();
  }

  // Keep display in sync if value is changed externally
  $effect(() => {
    displayValue = formatIDR(value);
  });
</script>

<div class="flex flex-col gap-1 {extraClass}">
  {#if label}
    <label class="text-sm font-medium text-slate-700">
      {label}{#if required}<span class="ml-0.5 text-red-500">*</span>{/if}
    </label>
  {/if}

  <div class="relative flex items-center">
    <span class="pointer-events-none absolute left-3 text-sm font-medium text-slate-400">Rp</span>
    <input
      type="text"
      inputmode="numeric"
      value={displayValue}
      {placeholder}
      {required}
      {disabled}
      oninput={handleInput}
      onfocus={handleFocus}
      class="w-full rounded-xl border py-2.5 pl-9 pr-3 text-sm font-medium text-right text-slate-800
             transition-colors outline-none
             {error ? 'border-red-300 bg-red-50 focus:border-red-400 focus:ring-2 focus:ring-red-100'
                    : 'border-slate-200 bg-white focus:border-primary-400 focus:ring-2 focus:ring-primary-100'}
             {disabled ? 'cursor-not-allowed opacity-50' : ''}"
    />
  </div>

  {#if error}
    <p class="text-xs text-red-500">{error}</p>
  {/if}
</div>

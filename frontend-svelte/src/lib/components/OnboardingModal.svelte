<script>
  import { onMount } from 'svelte';
  
  let step = $state(0);
  let show = $state(false);
  
  const steps = [
    {
      title: 'Upload Dokumen',
      description: 'Foto KTP, Paspor, atau Visa Anda. AI akan otomatis mengisi data.',
      icon: '📄'
    },
    {
      title: 'Review & Edit',
      description: 'Periksa hasil OCR dan edit jika ada yang salah.',
      icon: '✏️'
    },
    {
      title: 'Export Excel',
      description: 'Download file Excel yang siap upload ke Siskopatuh.',
      icon: '📊'
    }
  ];
  
  function next() {
    if (step < steps.length - 1) {
      step++;
    } else {
      complete();
    }
  }
  
  function skip() {
    complete();
  }
  
  function complete() {
    show = false;
    localStorage.setItem('onboarding-completed', 'true');
  }
  
  onMount(() => {
    show = !localStorage.getItem('onboarding-completed');
  });
</script>

{#if show}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
    <div class="m-4 max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
      <!-- Progress bar -->
      <div class="mb-6">
        <div class="h-2 bg-gray-200 rounded-full dark:bg-gray-700">
          <div 
            class="h-2 rounded-full bg-emerald-500 transition-all"
            style="width: {((step + 1) / steps.length) * 100}%"
          ></div>
        </div>
      </div>
      
      <!-- Step content -->
      <div class="mb-6 text-center">
        <div class="text-6xl mb-4">{steps[step].icon}</div>
        <h2 class="mb-2 text-xl font-bold">{steps[step].title}</h2>
        <p class="text-gray-600 dark:text-gray-400">{steps[step].description}</p>
      </div>
      
      <!-- Actions -->
      <div class="flex gap-3">
        <button 
          on:click={skip}
          class="flex-1 rounded-lg border px-4 py-2 text-gray-600 hover:bg-gray-100 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700"
        >
          Lewati
        </button>
        <button 
          on:click={next}
          class="flex-1 rounded-lg bg-emerald-500 px-4 py-2 text-white hover:bg-emerald-600"
        >
          {step === steps.length - 1 ? 'Mulai!' : 'Lanjut'}
        </button>
      </div>
    </div>
  </div>
{/if}

<script>
  import { onMount } from "svelte";
  import {
    UploadCloud,
    FileText,
    X,
    Loader2,
    Clipboard,
    CheckCircle,
    AlertCircle,
    Clock,
  } from "lucide-svelte";

  let {
    files = $bindable([]),
    isProcessing,
    errorMessage,
    onProcess,
    progress = null,
  } = $props();

  let dragOver = $state(false);

  function handleFiles(newFiles) {
    const validFiles = Array.from(newFiles).filter(
      (file) =>
        file.type.startsWith("image/") || file.type === "application/pdf",
    );
    files = [...files, ...validFiles];
  }

  function onDrop(e) {
    e.preventDefault();
    dragOver = false;
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }

  function onFileSelect(e) {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }

  async function handlePaste() {
    try {
      const clipboardItems = await navigator.clipboard.read();
      for (const item of clipboardItems) {
        const imageType = item.types.find((type) => type.startsWith("image/"));
        if (imageType) {
          const blob = await item.getType(imageType);
          const file = new File([blob], `pasted_image_${Date.now()}.png`, {
            type: imageType,
          });
          files = [...files, file];
        }
      }
    } catch (err) {
      console.error("Failed to read clipboard", err);
    }
  }

  function removeFile(index) {
    files = files.filter((_, i) => i !== index);
  }

  function clearFiles() {
    files = [];
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function triggerFileInput() {
    document.getElementById("fileInput").click();
  }

  function getThumbnail(file) {
    if (file.type.startsWith("image/")) {
      return URL.createObjectURL(file);
    }
    return null;
  }

  onMount(() => {
    const pasteListener = (e) => {
      if (e.clipboardData && e.clipboardData.files.length > 0) {
        handleFiles(e.clipboardData.files);
      }
    };
    window.addEventListener("paste", pasteListener);
    return () => window.removeEventListener("paste", pasteListener);
  });

  // Computed progress values
  let progressPercent = $derived(
    progress && progress.total > 0
      ? Math.round((progress.current / progress.total) * 100)
      : 0,
  );

  let progressLabel = $derived(() => {
    if (!progress) return "";
    const statusMap = {
      starting: "Memulai...",
      processing: `Memproses file ${progress.current}/${progress.total}...`,
      "post-processing": "Membersihkan data...",
      sanitizing: "Sanitasi data...",
      merging: "Menggabungkan data duplikat...",
      validating: "Validasi data...",
      complete: "Selesai!",
      error: "Terjadi kesalahan",
    };
    return statusMap[progress.status] || progress.status;
  });
</script>

<div class="max-w-5xl mx-auto px-4 sm:px-6 mt-4 sm:mt-8">
  <!-- Card Wrapper -->
  <div
    class="bg-white dark:bg-slate-800 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700 p-5 sm:p-8"
  >
    <!-- Hero with Brand -->
    <div class="text-center mb-6 sm:mb-8">
      <h2
        class="text-lg sm:text-2xl font-bold text-slate-800 dark:text-slate-100 mb-1 sm:mb-2"
      >
        Upload Dokumen Jamaah
      </h2>
      <p class="text-slate-500 text-sm sm:text-base">
        Ekstrak data dari KTP, Paspor, dan Visa secara otomatis.
      </p>
    </div>

    <!-- Dropzone -->
    <div
      class="group relative border-2 border-dashed rounded-xl sm:rounded-2xl p-6 sm:p-10 text-center transition-all cursor-pointer {dragOver
        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
        : 'border-slate-200 dark:border-slate-600 hover:border-emerald-400 hover:bg-emerald-50/30 dark:hover:bg-emerald-900/10'}"
      ondragover={(e) => {
        e.preventDefault();
        dragOver = true;
      }}
      ondragleave={() => {
        dragOver = false;
      }}
      ondrop={onDrop}
      onclick={triggerFileInput}
      role="button"
      tabindex="0"
      onkeydown={(e) => {
        if (e.key === "Enter") triggerFileInput();
      }}
    >
      <input
        id="fileInput"
        type="file"
        multiple
        accept="image/*,.pdf"
        class="hidden"
        onchange={onFileSelect}
      />

      <div class="flex flex-col items-center gap-3 sm:gap-4">
        <div
          class="bg-slate-100 p-3 sm:p-4 rounded-full group-hover:bg-emerald-100 transition-colors"
        >
          <UploadCloud
            class="h-8 w-8 sm:h-10 sm:w-10 text-slate-400 group-hover:text-emerald-500"
          />
        </div>
        <div>
          <p class="text-base sm:text-lg font-medium text-slate-700">
            Klik atau Seret File
          </p>
          <p class="text-xs sm:text-sm text-slate-400 mt-1">
            Format: JPG, PNG, PDF
          </p>
        </div>
        <div
          class="text-xs text-slate-400 border px-3 py-1 rounded-full hidden sm:block"
        >
          Tips: Tekan <kbd class="font-mono bg-slate-200 px-1 rounded"
            >Ctrl+V</kbd
          > untuk paste gambar
        </div>
      </div>

      <!-- Paste Button -->
      <button
        class="absolute top-2 right-2 sm:top-4 sm:right-4 bg-white border border-slate-200 text-slate-600 px-2 sm:px-3 py-1 sm:py-1.5 rounded-lg text-xs sm:text-sm font-medium hover:bg-slate-50 shadow-sm flex items-center gap-1 sm:gap-2"
        onclick={(e) => {
          e.stopPropagation();
          handlePaste();
        }}
      >
        <Clipboard class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
        <span class="hidden sm:inline">Paste</span>
      </button>
    </div>

    <!-- Error -->
    {#if errorMessage}
      <div
        class="bg-red-50 text-red-600 p-4 rounded-xl mt-6 flex items-center gap-3 border border-red-100"
      >
        <AlertCircle class="h-5 w-5 flex-shrink-0" />
        {errorMessage}
      </div>
    {/if}

    <!-- File List -->
    {#if files.length > 0}
      <div class="mt-8">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-semibold text-slate-700">
            File Terpilih ({files.length})
          </h3>
          <button
            class="text-sm text-red-500 hover:text-red-600"
            onclick={clearFiles}>Hapus Semua</button
          >
        </div>

        <div
          class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 sm:gap-4"
        >
          {#each files as file, i}
            <div
              class="relative group bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-lg p-2 shadow-sm hover:shadow-md transition-shadow"
            >
              <button
                class="absolute -top-2 -right-2 bg-white dark:bg-slate-700 rounded-full p-1 shadow-md text-slate-400 hover:text-red-500 border border-slate-200 dark:border-slate-600 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity z-10"
                onclick={() => removeFile(i)}
              >
                <X class="h-4 w-4" />
              </button>

              <div
                class="aspect-square bg-slate-100 rounded-md overflow-hidden flex items-center justify-center mb-2"
              >
                {#if file.type.startsWith("image/")}
                  <img
                    src={getThumbnail(file)}
                    alt="preview"
                    class="w-full h-full object-cover"
                  />
                {:else}
                  <FileText class="h-8 w-8 text-slate-400" />
                {/if}
              </div>
              <p
                class="text-xs text-slate-600 dark:text-slate-300 truncate px-1"
              >
                {file.name}
              </p>
              <p class="text-[10px] text-slate-400 px-1">
                {formatFileSize(file.size)}
              </p>

              <!-- Per-file status indicator during processing -->
              {#if isProcessing && progress}
                {#if progress.completed_files?.includes(file.name)}
                  <div
                    class="absolute top-1 left-1 bg-emerald-500 rounded-full p-0.5"
                  >
                    <CheckCircle class="h-3.5 w-3.5 text-white" />
                  </div>
                {:else if progress.failed_files?.includes(file.name)}
                  <div
                    class="absolute top-1 left-1 bg-red-500 rounded-full p-0.5"
                  >
                    <AlertCircle class="h-3.5 w-3.5 text-white" />
                  </div>
                {:else if progress.current_file === file.name}
                  <div
                    class="absolute top-1 left-1 bg-amber-400 rounded-full p-0.5"
                  >
                    <Loader2 class="h-3.5 w-3.5 text-white animate-spin" />
                  </div>
                {:else}
                  <div
                    class="absolute top-1 left-1 bg-slate-300 rounded-full p-0.5"
                  >
                    <Clock class="h-3.5 w-3.5 text-white" />
                  </div>
                {/if}
              {/if}
            </div>
          {/each}
        </div>
      </div>

      <!-- Progress Bar (during processing) -->
      {#if isProcessing && progress}
        <div
          class="mt-6 bg-white border border-slate-200 rounded-xl p-6 shadow-sm"
        >
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm font-medium text-slate-700"
              >{progressLabel()}</span
            >
            <span class="text-sm font-bold text-emerald-600"
              >{progressPercent}%</span
            >
          </div>
          <div class="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
            <div
              class="bg-gradient-to-r from-emerald-400 to-emerald-600 h-3 rounded-full transition-all duration-500 ease-out"
              style="width: {progressPercent}%"
            ></div>
          </div>
          {#if progress.current_file}
            <p class="text-xs text-slate-400 mt-2">
              📄 {progress.current_file}
            </p>
          {/if}
        </div>
      {/if}

      <!-- Process Button -->
      <div class="mt-8 flex justify-center">
        <button
          onclick={onProcess}
          disabled={isProcessing}
          class="w-full sm:w-auto bg-emerald-500 hover:bg-emerald-600 text-white text-base sm:text-lg font-semibold py-3 px-8 sm:px-12 rounded-xl shadow-lg hover:shadow-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3"
        >
          {#if isProcessing}
            <Loader2 class="h-6 w-6 animate-spin" />
            Memproses...
          {:else}
            🔍 Proses & Pratinjau
          {/if}
        </button>
      </div>
    {/if}
  </div>
</div>

<!--
  PublicRegistrationPage.svelte — Self-service jamaah registration page
  Accessible via jamaah.in/reg/{token}
-->
<script>
  import { onMount } from "svelte";
  import { Upload, Check, Loader2, AlertCircle, Camera } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let { token } = $props();

  let loading = $state(true);
  let error = $state("");
  let groupInfo = $state(null);

  let phone = $state("");
  let ktpFile = $state(null);
  let passportFile = $state(null);
  let visaFile = $state(null);
  let submitting = $state(false);
  let submitted = $state(false);

  onMount(async () => {
    try {
      const res = await ApiService.getRegistrationInfo(token);
      groupInfo = res;
    } catch (e) {
      error = e.message || "Link tidak valid atau sudah kadaluarsa";
    } finally {
      loading = false;
    }
  });

  async function handleSubmit() {
    if (!phone || !ktpFile) return;

    submitting = true;
    error = "";

    try {
      const formData = new FormData();
      formData.append("phone_number", phone);
      if (ktpFile) formData.append("ktp", ktpFile);
      if (passportFile) formData.append("passport", passportFile);
      if (visaFile) formData.append("visa", visaFile);

      await ApiService.submitRegistration(token, formData);
      submitted = true;
    } catch (e) {
      error = e.message || "Gagal mengirim data";
    } finally {
      submitting = false;
    }
  }

  function handleKtpChange(e) {
    ktpFile = e.target.files?.[0] || null;
  }

  function handlePassportChange(e) {
    passportFile = e.target.files?.[0] || null;
  }

  function handleVisaChange(e) {
    visaFile = e.target.files?.[0] || null;
  }
</script>

<div class="registration-page">
  {#if loading}
    <div class="loading">
      <Loader2 class="w-8 h-8 animate-spin text-emerald-500" />
      <p>Memuat...</p>
    </div>
  {:else if error && !groupInfo}
    <div class="error">
      <AlertCircle class="w-12 h-12 text-red-500" />
      <h2>Link Tidak Valid</h2>
      <p>{error}</p>
    </div>
  {:else if submitted}
    <div class="success">
      <div class="success-icon">
        <Check class="w-10 h-10" />
      </div>
      <h2>Data Terkirim!</h2>
      <p>Data Anda sedang dalam proses review oleh tim travel.</p>
      <p class="note">Kami akan menghubungi Anda melalui WhatsApp.</p>
    </div>
  {:else}
    <div class="form-container">
      <div class="header">
        <h1>Pendaftaran Jamaah</h1>
        <p class="group-name">{groupInfo?.group_name}</p>
      </div>

      {#if error}
        <div class="alert error">
          <AlertCircle class="w-4 h-4" />
          {error}
        </div>
      {/if}

      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="field">
          <label for="phone">Nomor WhatsApp <span class="required">*</span></label>
          <input
            id="phone"
            type="tel"
            bind:value={phone}
            placeholder="08xxxxxxxxxx"
            required
          />
        </div>

        <div class="field">
          <label>
            <Camera class="w-4 h-4" />
            Foto KTP/KK <span class="required">*</span>
          </label>
          <div class="upload-area">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onchange={handleKtpChange}
            />
            {#if ktpFile}
              <div class="file-selected">
                <Check class="w-5 h-5 text-emerald-500" />
                <span>{ktpFile.name}</span>
              </div>
            {:else}
              <Upload class="w-8 h-8 text-slate-400" />
              <span>Klik untuk foto atau pilih file KTP/KK</span>
            {/if}
          </div>
        </div>

        <div class="field">
          <label>
            <Camera class="w-4 h-4" />
            Foto Paspor <span class="optional">(Opsional)</span>
          </label>
          <div class="upload-area optional">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onchange={handlePassportChange}
            />
            {#if passportFile}
              <div class="file-selected">
                <Check class="w-5 h-5 text-emerald-500" />
                <span>{passportFile.name}</span>
              </div>
            {:else}
              <Upload class="w-6 h-6 text-slate-300" />
              <span>Paspor (opsional)</span>
            {/if}
          </div>
        </div>

        <div class="field">
          <label>
            <Camera class="w-4 h-4" />
            Foto Visa <span class="optional">(Opsional)</span>
          </label>
          <div class="upload-area optional">
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onchange={handleVisaChange}
            />
            {#if visaFile}
              <div class="file-selected">
                <Check class="w-5 h-5 text-emerald-500" />
                <span>{visaFile.name}</span>
              </div>
            {:else}
              <Upload class="w-6 h-6 text-slate-300" />
              <span>Visa (opsional)</span>
            {/if}
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting || !phone || !ktpFile}
        >
          {#if submitting}
            <Loader2 class="w-5 h-5 animate-spin" />
            Memproses...
          {:else}
            Kirim Data
          {/if}
        </button>
      </form>

      <p class="deadline">
        Link berlaku hingga: {new Date(groupInfo?.expires_at).toLocaleDateString('id-ID', {
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        })}
      </p>
    </div>
  {/if}
</div>

<style>
  .registration-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #f0fdf4, #ecfeff, #f0f9ff);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  .loading, .error, .success {
    text-align: center;
    padding: 2rem;
  }

  .loading p, .error p, .success p {
    color: #64748b;
    margin-top: 0.5rem;
  }

  .error h2 {
    color: #dc2626;
    margin-top: 1rem;
  }

  .success-icon {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, #10b981, #059669);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    color: white;
  }

  .success h2 {
    color: #059669;
    margin-top: 1rem;
  }

  .success .note {
    font-size: 0.875rem;
    color: #64748b;
    margin-top: 1rem;
  }

  .form-container {
    background: white;
    border-radius: 1rem;
    padding: 1.5rem;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  .header {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  h1 {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-bottom: 0.25rem;
  }

  .group-name {
    color: #10b981;
    font-weight: 500;
    font-size: 0.9375rem;
  }

  .alert {
    padding: 0.75rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
  }

  .alert.error {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
  }

  .field {
    margin-bottom: 1.25rem;
  }

  label {
    display: flex;
    align-items: center;
    gap: 0.375rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
    color: #374151;
  }

  .required {
    color: #dc2626;
  }

  .optional {
    color: #9ca3af;
    font-weight: 400;
    font-size: 0.75rem;
  }

  input[type="tel"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 1rem;
    transition: border-color 0.2s;
  }

  input[type="tel"]:focus {
    outline: none;
    border-color: #10b981;
  }

  .upload-area {
    border: 2px dashed #cbd5e1;
    border-radius: 0.5rem;
    padding: 1.5rem;
    text-align: center;
    position: relative;
    transition: all 0.2s;
    cursor: pointer;
  }

  .upload-area:hover {
    border-color: #10b981;
    background: #f0fdf4;
  }

  .upload-area.optional {
    padding: 1rem;
    border-color: #e2e8f0;
  }

  .upload-area input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
  }

  .upload-area span {
    display: block;
    margin-top: 0.5rem;
    font-size: 0.8125rem;
    color: #64748b;
  }

  .file-selected {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    color: #059669;
    font-size: 0.875rem;
  }

  button {
    width: 100%;
    padding: 0.875rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 0.5rem;
    font-weight: 600;
    font-size: 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.2s;
  }

  button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .deadline {
    text-align: center;
    font-size: 0.75rem;
    color: #9ca3af;
    margin-top: 1rem;
  }
</style>

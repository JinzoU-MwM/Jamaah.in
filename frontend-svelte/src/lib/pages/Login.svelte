<script>
  import {
    KeyRound,
    User,
    Mail,
    ArrowLeft,
    Loader2,
    ShieldCheck,
    RefreshCw,
  } from "lucide-svelte";
  import BrandLogo from "../components/BrandLogo.svelte";
  import { ApiService } from "../services/api";

  let { onLoginSuccess, onBack, initialMode = "login" } = $props();

  // mode: "login" | "register" | "verify" | "forgot" | "forgot-code" | "forgot-reset"
  let mode = $state("login");

  $effect(() => {
    if (initialMode) mode = initialMode;
  });

  let email = $state("");
  let password = $state("");
  let name = $state("");
  let error = $state("");
  let success = $state("");
  let isLoading = $state(false);

  // OTP verification
  let otpCode = $state("");
  let verifyEmail_addr = $state("");

  // Forgot password
  let resetCode = $state("");
  let newPassword = $state("");
  let confirmPassword = $state("");

  // Cooldown for resend
  let resendCooldown = $state(0);
  let cooldownInterval = null;

  function startCooldown(seconds = 60) {
    resendCooldown = seconds;
    if (cooldownInterval) clearInterval(cooldownInterval);
    cooldownInterval = setInterval(() => {
      resendCooldown--;
      if (resendCooldown <= 0) clearInterval(cooldownInterval);
    }, 1000);
  }

  // ── Login ──
  async function handleLogin(e) {
    e.preventDefault();
    error = "";
    success = "";
    isLoading = true;
    try {
      const result = await ApiService.login(email, password);
      localStorage.setItem("token", result.access_token);
      localStorage.setItem("user", JSON.stringify(result.user));
      onLoginSuccess(result.user);
    } catch (err) {
      const msg = err.message;
      // If unverified, redirect to OTP screen
      if (msg.includes("belum diverifikasi")) {
        verifyEmail_addr = email;
        mode = "verify";
        error = "";
        success = "Silakan masukkan kode OTP yang dikirim ke email Anda.";
      } else {
        error = msg;
      }
    } finally {
      isLoading = false;
    }
  }

  // ── Register ──
  async function handleRegister(e) {
    e.preventDefault();
    error = "";
    success = "";
    if (password.length < 6) {
      error = "Password minimal 6 karakter";
      return;
    }
    isLoading = true;
    try {
      const result = await ApiService.register(email, password, name);
      // Registration now returns email_verified: false + sends OTP
      verifyEmail_addr = email;
      mode = "verify";
      success = result.message || "Kode verifikasi telah dikirim ke email Anda";
      startCooldown(60);
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  // ── Verify OTP ──
  async function handleVerifyOtp(e) {
    e.preventDefault();
    error = "";
    success = "";
    if (otpCode.length !== 6) {
      error = "Masukkan 6 digit kode OTP";
      return;
    }
    isLoading = true;
    try {
      const result = await ApiService.verifyEmail(verifyEmail_addr, otpCode);
      if (result.access_token) {
        localStorage.setItem("token", result.access_token);
        localStorage.setItem("user", JSON.stringify(result.user));
        onLoginSuccess(result.user);
      } else {
        success = result.message;
        mode = "login";
      }
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  // ── Resend OTP ──
  async function handleResendOtp() {
    error = "";
    success = "";
    isLoading = true;
    try {
      const result = await ApiService.resendOtp(verifyEmail_addr);
      success = result.message || "Kode verifikasi baru telah dikirim";
      startCooldown(60);
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  // ── Forgot Password (step 1: send code) ──
  async function handleForgotSend(e) {
    e.preventDefault();
    error = "";
    success = "";
    isLoading = true;
    try {
      const result = await ApiService.forgotPassword(email);
      success = result.message;
      verifyEmail_addr = email;
      mode = "forgot-code";
      startCooldown(60);
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }

  // ── Forgot Password (step 2: verify code + new password) ──
  async function handleResetPassword(e) {
    e.preventDefault();
    error = "";
    success = "";
    if (newPassword.length < 6) {
      error = "Password baru minimal 6 karakter";
      return;
    }
    if (newPassword !== confirmPassword) {
      error = "Konfirmasi password tidak cocok";
      return;
    }
    isLoading = true;
    try {
      const result = await ApiService.resetPassword(
        verifyEmail_addr,
        resetCode,
        newPassword,
      );
      success = result.message || "Password berhasil direset. Silakan login.";
      mode = "login";
      resetCode = "";
      newPassword = "";
      confirmPassword = "";
    } catch (err) {
      error = err.message;
    } finally {
      isLoading = false;
    }
  }
</script>

<div
  class="flex-grow flex items-center justify-center p-4 bg-slate-50 min-h-screen"
>
  <div
    class="bg-white p-8 rounded-2xl shadow-xl w-full max-w-md border border-slate-200"
  >
    <!-- Back Button -->
    {#if onBack && (mode === "login" || mode === "register")}
      <button
        onclick={onBack}
        class="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-600 transition-colors mb-4"
      >
        <ArrowLeft class="h-4 w-4" />
        Kembali
      </button>
    {:else if mode !== "login" && mode !== "register"}
      <button
        onclick={() => {
          mode = "login";
          error = "";
          success = "";
        }}
        class="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-600 transition-colors mb-4"
      >
        <ArrowLeft class="h-4 w-4" />
        Kembali ke Login
      </button>
    {/if}

    <!-- Brand Logo -->
    <div class="flex justify-center mb-3">
      <BrandLogo size="large" />
    </div>

    <!-- ═══════════════════════════════════════════════ -->
    <!-- LOGIN / REGISTER MODE -->
    <!-- ═══════════════════════════════════════════════ -->
    {#if mode === "login" || mode === "register"}
      <!-- Mode Toggle -->
      <div class="flex rounded-xl bg-slate-100 p-1 mb-6">
        <button
          onclick={() => {
            mode = "login";
            error = "";
            success = "";
          }}
          class="flex-1 py-2 text-sm font-semibold rounded-lg transition-all {mode ===
          'login'
            ? 'bg-white text-slate-800 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'}"
        >
          Masuk
        </button>
        <button
          onclick={() => {
            mode = "register";
            error = "";
            success = "";
          }}
          class="flex-1 py-2 text-sm font-semibold rounded-lg transition-all {mode ===
          'register'
            ? 'bg-white text-slate-800 shadow-sm'
            : 'text-slate-500 hover:text-slate-700'}"
        >
          Daftar
        </button>
      </div>

      <!-- Tagline -->
      <p class="text-center text-slate-500 text-sm mb-6">
        {mode === "register"
          ? "Daftar gratis — dapatkan trial 7 hari!"
          : "Input Data Jamaah, Gak Pake Lama."}
      </p>

      {#if error}
        <div
          class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
        >
          {error}
        </div>
      {/if}

      {#if success}
        <div
          class="bg-emerald-50 text-emerald-600 p-3 rounded-lg mb-4 text-sm text-center border border-emerald-100"
        >
          {success}
        </div>
      {/if}

      <form
        onsubmit={mode === "login" ? handleLogin : handleRegister}
        class="space-y-4"
      >
        {#if mode === "register"}
          <div>
            <label
              for="name"
              class="block text-sm font-medium text-slate-700 mb-1"
              >Nama Lengkap</label
            >
            <div class="relative">
              <div
                class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
              >
                <User class="h-5 w-5 text-slate-400" />
              </div>
              <input
                id="name"
                type="text"
                bind:value={name}
                required
                class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
                placeholder="Nama lengkap"
              />
            </div>
          </div>
        {/if}

        <div>
          <label
            for="email"
            class="block text-sm font-medium text-slate-700 mb-1">Email</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <Mail class="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="email"
              type="email"
              bind:value={email}
              required
              class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
              placeholder="email@contoh.com"
            />
          </div>
        </div>

        <div>
          <label
            for="password"
            class="block text-sm font-medium text-slate-700 mb-1"
            >Password</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <KeyRound class="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="password"
              type="password"
              bind:value={password}
              required
              minlength="6"
              class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
              placeholder="••••••••"
            />
          </div>
        </div>

        {#if mode === "login"}
          <div class="text-right">
            <button
              type="button"
              onclick={() => {
                mode = "forgot";
                error = "";
                success = "";
              }}
              class="text-sm text-emerald-500 hover:text-emerald-600 font-medium transition-colors"
            >
              Lupa Password?
            </button>
          </div>
        {/if}

        <button
          type="submit"
          disabled={isLoading}
          class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 text-white font-semibold py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 disabled:transform-none flex items-center justify-center gap-2"
        >
          {#if isLoading}
            <Loader2 class="h-5 w-5 animate-spin" />
            {mode === "register" ? "Mendaftar..." : "Masuk..."}
          {:else}
            {mode === "register" ? "Daftar Gratis" : "Masuk"}
          {/if}
        </button>
      </form>

      <!-- ═══════════════════════════════════════════════ -->
      <!-- OTP VERIFICATION MODE -->
      <!-- ═══════════════════════════════════════════════ -->
    {:else if mode === "verify"}
      <div class="text-center mb-6">
        <div
          class="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <ShieldCheck class="h-8 w-8 text-emerald-500" />
        </div>
        <h2 class="text-xl font-bold text-slate-800">Verifikasi Email</h2>
        <p class="text-slate-500 text-sm mt-2">
          Kode 6 digit telah dikirim ke<br />
          <strong class="text-slate-700">{verifyEmail_addr}</strong>
        </p>
      </div>

      {#if error}
        <div
          class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
        >
          {error}
        </div>
      {/if}

      {#if success}
        <div
          class="bg-emerald-50 text-emerald-600 p-3 rounded-lg mb-4 text-sm text-center border border-emerald-100"
        >
          {success}
        </div>
      {/if}

      <form onsubmit={handleVerifyOtp} class="space-y-4">
        <div>
          <input
            id="otp"
            type="text"
            bind:value={otpCode}
            maxlength="6"
            required
            inputmode="numeric"
            pattern="[0-9]*"
            class="block w-full text-center text-2xl font-mono tracking-[0.5em] py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
            placeholder="000000"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading || otpCode.length !== 6}
          class="w-full bg-emerald-500 hover:bg-emerald-600 disabled:bg-emerald-300 text-white font-semibold py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {#if isLoading}
            <Loader2 class="h-5 w-5 animate-spin" />
            Memverifikasi...
          {:else}
            <ShieldCheck class="h-5 w-5" />
            Verifikasi
          {/if}
        </button>
      </form>

      <div class="text-center mt-4">
        <button
          onclick={handleResendOtp}
          disabled={isLoading || resendCooldown > 0}
          class="text-sm text-emerald-500 hover:text-emerald-600 disabled:text-slate-400 font-medium transition-colors inline-flex items-center gap-1"
        >
          <RefreshCw class="h-4 w-4" />
          {resendCooldown > 0
            ? `Kirim ulang (${resendCooldown}s)`
            : "Kirim ulang kode"}
        </button>
      </div>

      <!-- ═══════════════════════════════════════════════ -->
      <!-- FORGOT PASSWORD (step 1: enter email) -->
      <!-- ═══════════════════════════════════════════════ -->
    {:else if mode === "forgot"}
      <div class="text-center mb-6">
        <h2 class="text-xl font-bold text-slate-800">Lupa Password?</h2>
        <p class="text-slate-500 text-sm mt-2">
          Masukkan email Anda dan kami akan mengirimkan kode reset.
        </p>
      </div>

      {#if error}
        <div
          class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
        >
          {error}
        </div>
      {/if}

      <form onsubmit={handleForgotSend} class="space-y-4">
        <div>
          <label
            for="forgot-email"
            class="block text-sm font-medium text-slate-700 mb-1">Email</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <Mail class="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="forgot-email"
              type="email"
              bind:value={email}
              required
              class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none transition-all"
              placeholder="email@contoh.com"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          class="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-semibold py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {#if isLoading}
            <Loader2 class="h-5 w-5 animate-spin" />
            Mengirim...
          {:else}
            <Mail class="h-5 w-5" />
            Kirim Kode Reset
          {/if}
        </button>
      </form>

      <!-- ═══════════════════════════════════════════════ -->
      <!-- FORGOT PASSWORD (step 2: enter code + new pw) -->
      <!-- ═══════════════════════════════════════════════ -->
    {:else if mode === "forgot-code"}
      <div class="text-center mb-6">
        <h2 class="text-xl font-bold text-slate-800">Reset Password</h2>
        <p class="text-slate-500 text-sm mt-2">
          Masukkan kode 6 digit dan password baru Anda.
        </p>
      </div>

      {#if error}
        <div
          class="bg-red-50 text-red-600 p-3 rounded-lg mb-4 text-sm text-center border border-red-100"
        >
          {error}
        </div>
      {/if}

      {#if success}
        <div
          class="bg-emerald-50 text-emerald-600 p-3 rounded-lg mb-4 text-sm text-center border border-emerald-100"
        >
          {success}
        </div>
      {/if}

      <form onsubmit={handleResetPassword} class="space-y-4">
        <div>
          <label
            for="reset-code"
            class="block text-sm font-medium text-slate-700 mb-1"
            >Kode Reset</label
          >
          <input
            id="reset-code"
            type="text"
            bind:value={resetCode}
            maxlength="6"
            required
            inputmode="numeric"
            pattern="[0-9]*"
            class="block w-full text-center text-2xl font-mono tracking-[0.5em] py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
            placeholder="000000"
          />
        </div>

        <div>
          <label
            for="new-password"
            class="block text-sm font-medium text-slate-700 mb-1"
            >Password Baru</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <KeyRound class="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="new-password"
              type="password"
              bind:value={newPassword}
              required
              minlength="6"
              class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="Minimal 6 karakter"
            />
          </div>
        </div>

        <div>
          <label
            for="confirm-password"
            class="block text-sm font-medium text-slate-700 mb-1"
            >Konfirmasi Password</label
          >
          <div class="relative">
            <div
              class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none"
            >
              <KeyRound class="h-5 w-5 text-slate-400" />
            </div>
            <input
              id="confirm-password"
              type="password"
              bind:value={confirmPassword}
              required
              minlength="6"
              class="block w-full pl-10 pr-3 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 outline-none transition-all"
              placeholder="Ulangi password baru"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || resetCode.length !== 6}
          class="w-full bg-amber-500 hover:bg-amber-600 disabled:bg-amber-300 text-white font-semibold py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2"
        >
          {#if isLoading}
            <Loader2 class="h-5 w-5 animate-spin" />
            Mereset...
          {:else}
            <KeyRound class="h-5 w-5" />
            Reset Password
          {/if}
        </button>
      </form>

      <div class="text-center mt-4">
        <button
          onclick={() => {
            mode = "forgot";
            error = "";
            success = "";
          }}
          class="text-sm text-slate-500 hover:text-slate-700 font-medium transition-colors"
        >
          Kirim ulang kode reset
        </button>
      </div>
    {/if}

    <!-- Footer -->
    <p class="text-center text-xs text-slate-400 mt-6">
      © 2026 Jamaah.in · Otomatisasi Siskopatuh
    </p>
  </div>
</div>

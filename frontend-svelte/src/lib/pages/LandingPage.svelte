<script>
  import {
    UsersRound,
    ArrowRightToLine,
    FileSearch,
    Zap,
    FileSpreadsheet,
    Shield,
    Clock,
    Star,
    ChevronRight,
    Check,
    X as XIcon,
    Package,
    Hotel,
    ScanLine,
    Smartphone,
    Frown,
    Smile,
    Sparkles,
    BadgeCheck,
    Rocket,
  } from "lucide-svelte";

  let { onGoToLogin, onGoToRegister } = $props();
</script>

<div class="landing">
  <!-- Navbar -->
  <nav class="nav">
    <div class="nav-inner">
      <a href="/" class="logo">
        <div class="logo-icons">
          <UsersRound class="logo-icon-1" />
          <ArrowRightToLine class="logo-icon-2" />
        </div>
        <span class="logo-text">Jamaah<span class="logo-dot">.in</span></span>
      </a>
      <div class="nav-actions">
        <button
          type="button"
          onclick={() =>
            document
              .getElementById("features")
              ?.scrollIntoView({ behavior: "smooth" })}
          class="nav-link">Fitur</button
        >
        <button
          type="button"
          onclick={() =>
            document
              .getElementById("pricing")
              ?.scrollIntoView({ behavior: "smooth" })}
          class="nav-link">Harga</button
        >
        <button type="button" onclick={onGoToLogin} class="nav-link"
          >Masuk</button
        >
        <button type="button" onclick={onGoToRegister} class="nav-cta"
          >Coba Gratis</button
        >
      </div>
    </div>
  </nav>

  <!-- ================================================================== -->
  <!-- 1. HERO SECTION -->
  <!-- ================================================================== -->
  <section class="hero">
    <div class="hero-glow"></div>
    <div class="hero-content">
      <div class="hero-badge">
        <Sparkles class="w-4 h-4" />
        <span>All-in-One ERP Ringan untuk Travel Umrah</span>
      </div>
      <h1 class="hero-title">
        Berhenti Ketik Manual.<br />
        <span class="hero-highlight">Urus Jamaah 10x Lebih Cepat.</span>
      </h1>
      <p class="hero-desc">
        Dari scan KTP langsung jadi Excel Siskopatuh, bagi kamar hotel otomatis,
        sampai manifest digital untuk Mutawwif di Saudi — semua diurus AI dalam
        hitungan detik.
      </p>
      <div class="hero-actions">
        <button type="button" onclick={onGoToRegister} class="btn-hero-primary">
          Coba Gratis 7 Hari
          <ChevronRight class="w-5 h-5" />
        </button>
        <button
          type="button"
          onclick={() =>
            document
              .getElementById("features")
              ?.scrollIntoView({ behavior: "smooth" })}
          class="btn-hero-secondary"
        >
          Lihat Fitur
        </button>
      </div>
      <p class="hero-note">
        <Check class="w-4 h-4" /> Tanpa kartu kredit · 50 scan gratis · Setup 30
        detik
      </p>
    </div>
  </section>

  <!-- ================================================================== -->
  <!-- 2. PAIN vs. GAIN SECTION -->
  <!-- ================================================================== -->
  <section class="section comparison">
    <div class="section-inner">
      <div class="section-header">
        <h2 class="section-title">
          Masih Urus Jamaah Pakai <span class="text-red-400">Cara Lama</span>?
        </h2>
        <p class="section-desc">
          Lihat perbedaan nyata antara kerja manual dengan Jamaah.in.
        </p>
      </div>

      <div class="comparison-grid">
        <!-- OLD WAY -->
        <div class="compare-card old">
          <div class="compare-header old-header">
            <Frown class="w-5 h-5" />
            <span>Cara Lama 😩</span>
          </div>
          <ul class="compare-list">
            <li>
              <XIcon class="w-4 h-4 text-red-400 flex-shrink-0" />
              <span
                >Ketik data jamaah <strong>satu per satu</strong> ke Siskopatuh —
                berjam-jam tengah malam</span
              >
            </li>
            <li>
              <XIcon class="w-4 h-4 text-red-400 flex-shrink-0" />
              <span
                ><strong>Pusing bagi kamar</strong> hotel — coret-coret kertas, salah
                terus gender-nya</span
              >
            </li>
            <li>
              <XIcon class="w-4 h-4 text-red-400 flex-shrink-0" />
              <span
                >Mutawwif di Saudi <strong>bawa kertas lecek,</strong> absen manual,
                jamaah terlewat</span
              >
            </li>
            <li>
              <XIcon class="w-4 h-4 text-red-400 flex-shrink-0" />
              <span
                >Distribusi koper & ihram <strong>dicatat di buku</strong> — bocor
                melulu</span
              >
            </li>
            <li>
              <XIcon class="w-4 h-4 text-red-400 flex-shrink-0" />
              <span
                >Typo data paspor → <strong>gagal berangkat,</strong> rugi puluhan
                juta</span
              >
            </li>
          </ul>
        </div>

        <!-- NEW WAY -->
        <div class="compare-card new">
          <div class="compare-header new-header">
            <Smile class="w-5 h-5" />
            <span>Pakai Jamaah.in 🚀</span>
          </div>
          <ul class="compare-list">
            <li>
              <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span
                ><strong>Scan KTP → langsung jadi Excel</strong> Siskopatuh 32 kolom,
                selesai 30 detik</span
              >
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span
                ><strong>Auto-Rooming 1 klik</strong> — gender dipisahkan, keluarga
                disatukan otomatis</span
              >
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span
                >Mutawwif buka <strong>manifest digital di HP,</strong> absen ceklis,
                WhatsApp langsung</span
              >
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span
                ><strong>Inventori digital</strong> — stok koper & ihram tercatat
                rapi, siapa sudah terima nampak</span
              >
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span
                >AI cerdas men-<strong>deteksi nama yang sama</strong> dari beberapa
                dokumen → 0 duplikat</span
              >
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- ================================================================== -->
  <!-- 3. CORE FEATURES GRID -->
  <!-- ================================================================== -->
  <section class="section features" id="features">
    <div class="section-inner">
      <div class="section-header">
        <h2 class="section-title">
          4 Pilar yang Bikin Operasional <span class="text-emerald-400"
            >Anti Ribet</span
          >
        </h2>
        <p class="section-desc">
          Setiap fitur dirancang khusus untuk tantangan nyata travel umrah &
          haji di Indonesia.
        </p>
      </div>
      <div class="features-grid features-grid-2x2">
        <!-- Feature 1: AI Document Scanner -->
        <div class="feature-card feature-card-large">
          <div class="feature-icon blue">
            <ScanLine class="w-6 h-6" />
          </div>
          <div class="feature-label">AI-Powered</div>
          <h3>AI Document Scanner</h3>
          <p class="feature-tagline">
            "Scan KTP, Paspor, Visa — langsung jadi format 32 kolom Siskopatuh."
          </p>
          <ul class="feature-bullets">
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Powered by Gemini Flash
              — akurasi tinggi untuk dokumen Indonesia
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Upload banyak dokumen
              sekaligus, proses paralel dalam detik
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Fuzzy Merge mengenali
              orang yang sama dari beberapa dokumen
            </li>
          </ul>
        </div>

        <!-- Feature 2: Smart Auto-Rooming -->
        <div class="feature-card feature-card-large">
          <div class="feature-icon cyan">
            <Hotel class="w-6 h-6" />
          </div>
          <div class="feature-label">Pro</div>
          <h3>Smart Auto-Rooming</h3>
          <p class="feature-tagline">
            "Pisahkan gender & satukan keluarga otomatis."
          </p>
          <ul class="feature-bullets">
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Algoritma cerdas mengisi
              kamar Quad/Triple/Double secara optimal
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Laki-laki dan perempuan
              dipisahkan, keluarga tetap satu kamar
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Drag & drop untuk penyesuaian
              manual — visual, cepat, akurat
            </li>
          </ul>
        </div>

        <!-- Feature 3: Mutawwif Mobile Manifest -->
        <div class="feature-card feature-card-large">
          <div class="feature-icon purple">
            <Smartphone class="w-6 h-6" />
          </div>
          <div class="feature-label">Pro</div>
          <h3>Mutawwif Mobile Manifest</h3>
          <p class="feature-tagline">
            "Tinggalkan absen kertas. Tour Leader pakai HP."
          </p>
          <ul class="feature-bullets">
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Generate link manifest
              aman dengan PIN — share ke Mutawwif
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Ceklis kehadiran digital,
              cari jamaah instan, data selalu update
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Tombol WhatsApp langsung
              — komunikasi 1 klik dari manifest
            </li>
          </ul>
        </div>

        <!-- Feature 4: Inventory Checklist -->
        <div class="feature-card feature-card-large">
          <div class="feature-icon amber">
            <Package class="w-6 h-6" />
          </div>
          <div class="feature-label">Pro</div>
          <h3>Inventory Checklist</h3>
          <p class="feature-tagline">
            "Gudang nggak akan bocor. Distribusi tercatat rapi."
          </p>
          <ul class="feature-bullets">
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Kelola stok Koper, Ihram,
              Mukena, Baju — semua di satu tempat
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Forecast otomatis kebutuhan
              berdasarkan jumlah jamaah & gender
            </li>
            <li>
              <Check class="w-3.5 h-3.5 text-emerald-400" /> Tracking distribusi
              per jamaah — siapa sudah terima, siapa belum
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>

  <!-- ================================================================== -->
  <!-- 4. PRICING SECTION -->
  <!-- ================================================================== -->
  <section class="section pricing" id="pricing">
    <div class="section-inner">
      <div class="section-header">
        <h2 class="section-title">
          Investasi <span class="text-emerald-400">Lebih Murah</span> dari Lembur
          1 Malam
        </h2>
        <p class="section-desc">
          Mulai gratis tanpa risiko. Coba Pro 7 hari gratis, upgrade kapan saja.
        </p>
      </div>
      <div class="pricing-grid">
        <!-- Free Tier -->
        <div class="price-card">
          <div class="price-plan">Free</div>
          <div class="price-value">
            <span class="price-amount">Rp 0</span>
            <span class="price-period"> / selamanya</span>
          </div>
          <p class="price-subtitle">
            Cukup untuk test drive. Tanpa batas waktu.
          </p>
          <ul class="price-features">
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> <strong>5 scan</strong>
              dokumen
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> AI OCR (Gemini Flash)
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> Preview & edit hasil scan
            </li>
            <li class="muted">
              <XIcon class="w-4 h-4" /> Export Excel Siskopatuh
            </li>
            <li class="muted">
              <XIcon class="w-4 h-4" /> Auto-Rooming & Manifest
            </li>
            <li class="muted">
              <XIcon class="w-4 h-4" /> Inventori & Distribusi
            </li>
          </ul>
          <button type="button" onclick={onGoToRegister} class="btn-secondary"
            >Mulai Gratis</button
          >
        </div>
        <!-- Pro Monthly -->
        <div class="price-card">
          <div class="price-plan">Pro</div>
          <div class="price-value">
            <span class="price-amount">Rp 80.000</span>
            <span class="price-period"> / bulan</span>
          </div>
          <p class="price-subtitle">
            Fleksibel, bayar per bulan sesuai kebutuhan.
          </p>
          <ul class="price-features">
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Unlimited</strong> scan dokumen
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Unlimited</strong> grup jamaah
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> AI OCR + Fuzzy Merge
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> Export Excel Siskopatuh
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Auto-Rooming</strong> Hotel
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Manifest Digital</strong> Mutawwif
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Inventori</strong> & Distribusi
            </li>
          </ul>
          <button type="button" onclick={onGoToRegister} class="btn-secondary"
            >Pilih Pro — Rp 80rb/bln</button
          >
          <p class="price-guarantee">Bayar bulanan, batalkan kapan saja.</p>
        </div>
        <!-- Pro Annual -->
        <div class="price-card featured">
          <div class="price-badge">HEMAT 17%</div>
          <div class="price-plan">Pro Annual</div>
          <div class="price-value">
            <span class="price-amount">Rp 800.000</span>
            <span class="price-period"> / tahun</span>
          </div>
          <p class="price-subtitle">
            <strong>Rp 66.700/bulan</strong> — hemat 2 bulan gratis!
          </p>
          <ul class="price-features">
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>7 hari Pro Trial</strong> GRATIS
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Unlimited</strong> scan dokumen
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Unlimited</strong> grup jamaah
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> AI OCR + Fuzzy Merge
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" /> Export Excel Siskopatuh
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Auto-Rooming</strong> + Manifest
            </li>
            <li>
              <Check class="w-4 h-4 text-emerald-400" />
              <strong>Prioritas</strong> Support
            </li>
          </ul>
          <button type="button" onclick={onGoToRegister} class="btn-primary"
            >Pilih Annual — Rp 800rb/thn</button
          >
          <p class="price-guarantee">Hemat Rp 160.000 per tahun!</p>
        </div>
      </div>
    </div>
  </section>

  <!-- ================================================================== -->
  <!-- 5. FINAL CTA -->
  <!-- ================================================================== -->
  <section class="section final-cta">
    <div class="section-inner">
      <div class="cta-box">
        <Rocket class="w-10 h-10 text-emerald-400 mx-auto mb-4" />
        <h2 class="cta-title">
          Keberangkatan Bulan Ini?<br />
          <span class="hero-highlight">Urus Sekarang Pakai Jamaah.in.</span>
        </h2>
        <p class="cta-desc">
          Daftar dalam 30 detik. Langsung scan dokumen jamaah. Tanpa training,
          tanpa setup ribet.
        </p>
        <div class="cta-actions">
          <button
            type="button"
            onclick={onGoToRegister}
            class="btn-hero-primary btn-cta-large"
          >
            Daftar Gratis Sekarang
            <ChevronRight class="w-5 h-5" />
          </button>
        </div>
        <p class="hero-note" style="margin-top: 1rem;">
          <Check class="w-4 h-4" /> 7 hari gratis · 50 scan · Tanpa kartu kredit
        </p>
      </div>
    </div>
  </section>

  <!-- Footer -->
  <footer class="footer">
    <div class="footer-inner">
      <div class="flex items-center gap-2">
        <UsersRound class="w-5 h-5 text-emerald-400" />
        <span class="font-bold text-white"
          >Jamaah<span class="text-emerald-400">.in</span></span
        >
      </div>
      <p class="text-sm text-slate-500">
        © 2026 Jamaah.in · All-in-One ERP Ringan untuk Travel Umrah & Haji
      </p>
    </div>
  </footer>
</div>

<style>
  .landing {
    font-family:
      "Plus Jakarta Sans",
      system-ui,
      -apple-system,
      sans-serif;
    background: #0a0f1a;
    color: #e2e8f0;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ---- NAV ---- */
  .nav {
    position: fixed;
    inset: 0 0 auto;
    z-index: 50;
    background: rgba(10, 15, 26, 0.85);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
  .nav-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0.875rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .logo {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
  }
  .logo-icons {
    display: flex;
    align-items: center;
    margin-right: -4px;
  }
  .logo-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: white;
  }
  .logo-dot {
    color: #10b981;
  }
  .nav-actions {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .nav-link {
    color: #94a3b8;
    font-size: 0.875rem;
    font-weight: 500;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    background: transparent;
    border: none;
    cursor: pointer;
    transition: all 0.15s;
  }
  .nav-link:hover {
    color: white;
    background: rgba(255, 255, 255, 0.05);
  }
  .nav-cta {
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
    padding: 0.5rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    transition: all 0.15s;
  }
  .nav-cta:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
  }

  /* ---- HERO ---- */
  .hero {
    position: relative;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 7rem 1.5rem 4rem;
    text-align: center;
  }
  .hero-glow {
    position: absolute;
    top: -150px;
    left: 50%;
    transform: translateX(-50%);
    width: 700px;
    height: 500px;
    background: radial-gradient(
      ellipse,
      rgba(16, 185, 129, 0.1) 0%,
      transparent 70%
    );
    pointer-events: none;
  }
  .hero-content {
    position: relative;
    z-index: 1;
    max-width: 720px;
  }
  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    background: rgba(16, 185, 129, 0.08);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #34d399;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.375rem 0.875rem;
    border-radius: 999px;
    margin-bottom: 1.25rem;
  }
  .hero-title {
    font-size: clamp(2rem, 6vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    color: #f8fafc;
    margin-bottom: 1.25rem;
  }
  .hero-highlight {
    background: linear-gradient(135deg, #34d399, #10b981);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .hero-desc {
    font-size: 1.0625rem;
    color: #94a3b8;
    line-height: 1.7;
    margin-bottom: 1.75rem;
    max-width: 580px;
    margin-left: auto;
    margin-right: auto;
  }
  .hero-actions {
    display: flex;
    gap: 0.875rem;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 1.25rem;
  }
  .btn-hero-primary {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    font-weight: 700;
    font-size: 1rem;
    padding: 0.8125rem 1.75rem;
    border-radius: 0.625rem;
    border: none;
    cursor: pointer;
    transition: all 0.2s;
  }
  .btn-hero-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.35);
  }
  .btn-hero-secondary {
    background: transparent;
    color: #94a3b8;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.8125rem 1.75rem;
    border-radius: 0.625rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
    cursor: pointer;
    transition: all 0.15s;
  }
  .btn-hero-secondary:hover {
    color: white;
    border-color: rgba(255, 255, 255, 0.25);
  }
  .hero-note {
    font-size: 0.8125rem;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.375rem;
  }

  /* ---- SECTIONS ---- */
  .section {
    padding: 5rem 0;
  }
  .section-inner {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 1.5rem;
  }
  .section-header {
    text-align: center;
    margin-bottom: 2.5rem;
  }
  .section-title {
    font-size: clamp(1.5rem, 4vw, 2.25rem);
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 0.625rem;
  }
  .section-desc {
    font-size: 1rem;
    color: #94a3b8;
    max-width: 560px;
    margin: 0 auto;
  }

  /* ---- COMPARISON (Pain vs Gain) ---- */
  .comparison {
    background: linear-gradient(180deg, #0a0f1a, #111827);
  }
  .comparison-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.25rem;
    max-width: 900px;
    margin: 0 auto;
  }
  .compare-card {
    border-radius: 1rem;
    padding: 1.75rem;
  }
  .compare-card.old {
    background: rgba(239, 68, 68, 0.04);
    border: 1px solid rgba(239, 68, 68, 0.12);
  }
  .compare-card.new {
    background: rgba(16, 185, 129, 0.04);
    border: 1px solid rgba(16, 185, 129, 0.15);
    box-shadow: 0 0 24px rgba(16, 185, 129, 0.04);
  }
  .compare-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    font-size: 0.9375rem;
    margin-bottom: 1.25rem;
    padding-bottom: 0.75rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }
  .old-header {
    color: #f87171;
  }
  .new-header {
    color: #34d399;
  }
  .compare-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.875rem;
  }
  .compare-list li {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: #cbd5e1;
    line-height: 1.6;
  }

  /* ---- FEATURES ---- */
  .features {
    background: #0a0f1a;
  }
  .features-grid-2x2 {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.25rem;
  }
  .feature-card {
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.04);
    border-radius: 0.875rem;
    padding: 1.75rem;
    transition: all 0.2s;
  }
  .feature-card:hover {
    border-color: rgba(16, 185, 129, 0.15);
    background: rgba(255, 255, 255, 0.03);
    transform: translateY(-2px);
  }
  .feature-card h3 {
    font-size: 1.125rem;
    font-weight: 700;
    color: #f1f5f9;
    margin-bottom: 0.5rem;
  }
  .feature-label {
    display: inline-block;
    font-size: 0.625rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid rgba(16, 185, 129, 0.15);
    padding: 0.125rem 0.5rem;
    border-radius: 999px;
    margin-bottom: 0.5rem;
  }
  .feature-tagline {
    font-size: 0.875rem;
    color: #94a3b8;
    line-height: 1.6;
    font-style: italic;
    margin-bottom: 0.875rem;
  }
  .feature-bullets {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .feature-bullets li {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: #cbd5e1;
    line-height: 1.5;
  }
  .feature-icon {
    width: 44px;
    height: 44px;
    border-radius: 0.625rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 0.875rem;
  }
  .feature-icon.blue {
    background: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }
  .feature-icon.purple {
    background: rgba(168, 85, 247, 0.1);
    color: #a855f7;
  }
  .feature-icon.amber {
    background: rgba(245, 158, 11, 0.1);
    color: #f59e0b;
  }
  .feature-icon.cyan {
    background: rgba(6, 182, 212, 0.1);
    color: #06b6d4;
  }

  /* ---- PRICING ---- */
  .pricing {
    background: #111827;
  }
  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.25rem;
    max-width: 740px;
    margin: 0 auto;
    align-items: start;
  }
  .price-card {
    position: relative;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 1rem;
    padding: 2rem;
  }
  .price-card.featured {
    border-color: rgba(16, 185, 129, 0.25);
    background: rgba(16, 185, 129, 0.04);
    box-shadow: 0 0 32px rgba(16, 185, 129, 0.06);
  }
  .price-badge {
    position: absolute;
    top: -10px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    font-size: 0.625rem;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.25rem 0.875rem;
    border-radius: 999px;
  }
  .price-plan {
    font-size: 0.875rem;
    font-weight: 600;
    color: #94a3b8;
    margin-bottom: 0.375rem;
  }
  .price-value {
    margin-bottom: 0.5rem;
  }
  .price-amount {
    font-size: 1.75rem;
    font-weight: 800;
    color: #f8fafc;
  }
  .price-period {
    font-size: 0.8125rem;
    color: #64748b;
  }
  .price-subtitle {
    font-size: 0.8125rem;
    color: #64748b;
    margin-bottom: 1.25rem;
    line-height: 1.5;
  }
  .price-features {
    list-style: none;
    padding: 0;
    margin: 0 0 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.625rem;
  }
  .price-features li {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.8125rem;
    color: #cbd5e1;
  }
  .price-features li.muted {
    color: #475569;
  }
  .price-guarantee {
    font-size: 0.75rem;
    color: #64748b;
    text-align: center;
    margin-top: 0.75rem;
  }
  .btn-primary {
    width: 100%;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    font-weight: 600;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.15s;
  }
  .btn-primary:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3);
  }
  .btn-secondary {
    width: 100%;
    background: transparent;
    color: #94a3b8;
    font-weight: 600;
    padding: 0.75rem 1.25rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(148, 163, 184, 0.2);
    cursor: pointer;
    font-size: 0.875rem;
    transition: all 0.15s;
  }
  .btn-secondary:hover {
    color: white;
    border-color: rgba(255, 255, 255, 0.25);
  }

  /* ---- FINAL CTA ---- */
  .final-cta {
    background: linear-gradient(180deg, #111827, #0a0f1a);
  }
  .cta-box {
    text-align: center;
    background: rgba(16, 185, 129, 0.04);
    border: 1px solid rgba(16, 185, 129, 0.1);
    border-radius: 1.5rem;
    padding: 3.5rem 2rem;
    max-width: 680px;
    margin: 0 auto;
  }
  .cta-title {
    font-size: clamp(1.5rem, 4vw, 2rem);
    font-weight: 800;
    color: #f8fafc;
    margin-bottom: 1rem;
    line-height: 1.3;
  }
  .cta-desc {
    font-size: 1rem;
    color: #94a3b8;
    margin-bottom: 1.5rem;
    max-width: 480px;
    margin-left: auto;
    margin-right: auto;
  }
  .cta-actions {
    display: flex;
    justify-content: center;
  }
  .btn-cta-large {
    font-size: 1.0625rem;
    padding: 0.875rem 2.25rem;
  }

  /* ---- FOOTER ---- */
  .footer {
    background: #0a0f1a;
    border-top: 1px solid rgba(255, 255, 255, 0.04);
    padding: 1.5rem 0;
  }
  .footer-inner {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  /* ---- UTILITY ---- */
  .text-emerald-400 {
    color: #34d399;
  }
  .text-red-400 {
    color: #f87171;
  }

  /* ---- RESPONSIVE ---- */
  @media (max-width: 768px) {
    .comparison-grid {
      grid-template-columns: 1fr;
      max-width: 440px;
    }
    .features-grid-2x2 {
      grid-template-columns: 1fr;
    }
    .pricing-grid {
      grid-template-columns: 1fr;
      max-width: 380px;
    }
    .footer-inner {
      flex-direction: column;
      gap: 0.5rem;
      text-align: center;
    }
  }
  @media (max-width: 480px) {
    .hero {
      padding: 5.5rem 1rem 3rem;
    }
    .hero-actions {
      flex-direction: column;
    }
    .btn-hero-primary,
    .btn-hero-secondary {
      width: 100%;
      justify-content: center;
    }
    .cta-box {
      padding: 2.5rem 1.25rem;
    }
  }
</style>

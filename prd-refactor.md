# PRD — Jamaah.in v2.1
## Platform Administrasi Bisnis Travel Umroh & Haji

| Item | Detail |
|------|--------|
| **Nama Produk** | Jamaah.in |
| **Versi** | 2.1 — Travel Admin System |
| **Tagline** | Satu Dashboard untuk Seluruh Operasional Travel Umroh & Haji Anda |
| **Website** | https://jamaah.in |
| **Kategori** | SaaS B2B — Travel & Umroh/Haji Administration |
| **Target Pasar** | Indonesia |
| **Status** | In Development |
| **Tanggal Dokumen** | 2025 |

---

## 1. Latar Belakang & Alasan Pivot

### 1.1 Masalah dengan v1.0

Jamaah.in v1 berfokus pada AI Scanner dan fitur-fitur koordinasi jamaah (manifest digital, auto-rooming, WhatsApp blast). Di lapangan, sebagian besar fitur koordinasi tersebut kalah bersaing dengan kebiasaan yang sudah ada: **grup WhatsApp per keberangkatan** sudah digunakan oleh hampir semua travel dan efektif untuk komunikasi real-time.

Fitur yang terbukti dipakai: **AI Scanner** (menghemat waktu input data signifikan).

Fitur yang tidak dipakai secara aktif karena sudah ada solusi lain: manifest digital, WhatsApp blast, auto-rooming berbasis drag-drop.

### 1.2 Gap Nyata yang Belum Terisi

Meskipun WA group menyelesaikan masalah koordinasi, travel agent masih kesulitan dengan:

- Tidak ada sistem yang bisa membuat dan melacak **invoice per jamaah** secara otomatis
- **Piutang jamaah** yang belum lunas sering tidak terpantau — owner baru tahu saat berangkat sudah dekat
- **Profit & Loss per trip** tidak bisa dilihat secara real-time; butuh Excel manual
- **Pengeluaran ke vendor** (hotel, maskapai, katering) tidak tercatat sistematis
- **Komisi agen** dihitung manual dan sering terlambat dibayar
- **Database jamaah** tidak terintegrasi lintas tahun — tidak tahu siapa yang sudah umroh dan potensial repeat order
- **Paket & harga** dikelola di Excel atau WhatsApp — tidak ada single source of truth

### 1.3 Posisi Produk Baru

Jamaah.in v2 bukan lagi "tools untuk input data jamaah ke Siskopatuh" — melainkan **sistem administrasi bisnis lengkap khusus travel umroh & haji**, setara Jurnal/Accurate tapi dirancang dari awal untuk konteks PPIU Indonesia.

Software akuntansi umum tidak mengerti konsep: paket reguler vs VIP, skema DP + cicilan per musim haji, komisi jaringan sub-agen, checklist kelengkapan paspor & visa. Jamaah.in v2 mengerti semua itu sejak hari pertama.

---

## 2. Target Pengguna

### 2.1 Segmen Utama

| Segmen | Persona | Pain Point Utama |
|--------|---------|-----------------|
| **Owner / Direktur Travel** | Memiliki 1-5 staff, handle 3-20 trip per tahun | Tidak bisa lihat profit real-time, tidak tahu siapa yang belum bayar |
| **Staff Admin** | Merekap pembayaran, buat kwitansi manual, hubungi jamaah | Proses manual memakan waktu, rawan human error |
| **Marketing / CS** | Terima pendaftaran, follow up calon jamaah | Tidak ada sistem tracking status calon jamaah |
| **Akuntan / Finance** | Buat laporan keuangan, rekonsiliasi kas | Data pembayaran tidak tersentralisasi |

### 2.2 Skala Bisnis Target

- **Tier Kecil**: 1-3 trip per tahun, 30-100 jamaah per trip — pemilik handle semua sendiri
- **Tier Menengah**: 4-12 trip per tahun, 1-3 staff admin, mulai punya jaringan agen
- **Tier Besar**: 12+ trip per tahun, tim terpisah (marketing, operasional, keuangan)

### 2.3 Market Size

- 2.200+ PPIU terdaftar Kemenag RI
- Estimasi 1-2 juta jamaah umroh per tahun
- Estimasi 220.000 jamaah haji per tahun
- TAM: ~Rp 26 miliar per tahun (asumsi Rp 1 juta/travel/bulan, 2.200 PPIU)

---

## 3. Arsitektur Produk

Dengan semua modul baru, arsitektur lengkap Jamaah.in v2:

```
┌────────────────────────────────────────────────────────────────────┐
│                     JAMAAH.IN v2.0 — ADMIN SYSTEM                  │
├─────────────────┬─────────────────┬──────────────┬─────────────────┤
│  PAKET &        │   CRM &         │  INVOICE &   │  LAPORAN        │
│  HARGA          │   PIPELINE      │  PEMBAYARAN  │  KEUANGAN       │
├─────────────────┼─────────────────┼──────────────┼─────────────────┤
│  VENDOR &       │   KOMISI        │  DOKUMEN &   │  AI SCANNER     │
│  BIAYA OPS      │   AGEN          │  PASPOR      │  (v1 enhanced)  │
├─────────────────┼─────────────────┼──────────────┼─────────────────┤
│  E-KONTRAK      │  PEMBATALAN     │  PERSEDIAAN  │  PENGGAJIAN     │
│  DIGITAL        │  & REFUND       │  (INVENTORY) │  (PAYROLL)      │
└─────────────────┴─────────────────┴──────────────┴─────────────────┘
                         12 Modul Total
```

---

## 4. Modul 1 — Manajemen Paket & Harga

### 4.1 Deskripsi

Fondasi seluruh sistem. Setiap paket yang dibuat di sini akan menjadi referensi untuk invoice, laporan profit, dan pipeline jamaah. Tanpa modul ini, tidak ada paket yang bisa dikaitkan ke jamaah.

### 4.2 Fitur

#### 4.2.1 Buat & Kelola Paket

- **Informasi dasar**: nama paket, jenis (umroh reguler / umroh plus / haji khusus / haji ONH plus), tanggal keberangkatan, tanggal kepulangan, durasi otomatis (hari)
- **Kuota**: jumlah kursi total, kursi terisi, kursi tersisa (real-time dari data jamaah)
- **Status paket**: Draft, Open (bisa diisi), Full (penuh), Closed (ditutup manual), Done (sudah berangkat)
- **Maskapai**: nama maskapai, nomor penerbangan keberangkatan & kepulangan
- **Hotel Makkah**: nama hotel, bintang, jarak ke Masjidil Haram, jumlah malam
- **Hotel Madinah**: nama hotel, bintang, jarak ke Masjid Nabawi, jumlah malam
- **Keterangan program**: itinerary singkat (plain text atau rich text)
- **Dokumen lampiran**: upload brosur PDF/gambar paket

#### 4.2.2 Struktur Harga Bertingkat

Setiap paket bisa memiliki beberapa tier harga berdasarkan tipe kamar:

| Tipe Kamar | Contoh Harga |
|------------|-------------|
| Quad (4 orang) | Rp 22.500.000 |
| Triple (3 orang) | Rp 25.000.000 |
| Double (2 orang) | Rp 29.000.000 |
| Single (1 orang) | Rp 38.000.000 |

- Harga bisa diubah kapan saja; jamaah yang sudah terdaftar tidak terpengaruh (harga di-snapshot saat pendaftaran)
- Early bird: harga khusus dengan tanggal kedaluwarsa
- Harga khusus per jamaah (override individual)

#### 4.2.3 Komponen Biaya (Cost Breakdown)

Admin bisa mendefinisikan komponen biaya internal per paket untuk menghitung HPP (Harga Pokok Paket):

- Tiket pesawat per orang
- Hotel Makkah (per malam × jumlah malam × porsi per orang)
- Hotel Madinah (per malam × jumlah malam × porsi per orang)
- Visa umroh / haji
- Bus lokal & transportasi darat
- Muthawwif / tour leader
- Perlengkapan (koper, ihram, mukena, baju)
- Biaya lain-lain (handling, tips, emergency fund)
- **Margin otomatis dihitung**: Harga Jual − HPP = Margin per jamaah × kuota = Proyeksi Profit Trip

#### 4.2.4 Publikasi Paket

- Setiap paket menghasilkan link shareable: `jamaah.in/paket/{slug}`
- Halaman publik menampilkan: nama paket, tanggal, hotel, maskapai, harga per tipe kamar, sisa kursi, tombol "Daftar"
- Owner bisa toggle: paket tampil publik atau hanya internal (untuk agen)

### 4.3 Role Access

| Role | Aksi |
|------|------|
| Owner | Buat, edit, hapus, publish paket |
| Admin | Buat, edit paket; tidak bisa hapus / publish |
| Viewer | Lihat saja |

---

## 5. Modul 2 — CRM & Pipeline Pendaftar

### 5.1 Deskripsi

Sistem untuk melacak perjalanan setiap calon jamaah dari pertama kali kontak sampai berangkat. Menggantikan buku tulis, grup WA, dan spreadsheet pendaftaran yang selama ini dipakai.

### 5.2 Pipeline Status Jamaah

```
PROSPEK → SURVEY → BOOKING → DP → CICILAN → LUNAS → BERANGKAT → SELESAI
```

| Status | Keterangan |
|--------|-----------|
| **Prospek** | Sudah kontak, belum pasti paket |
| **Survey** | Sudah diskusi paket, dalam pertimbangan |
| **Booking** | Konfirmasi paket & tipe kamar, belum bayar |
| **DP** | Sudah bayar uang muka |
| **Cicilan** | Sedang mencicil (untuk skema cicilan) |
| **Lunas** | Pembayaran 100% selesai |
| **Berangkat** | Sudah dalam perjalanan |
| **Selesai** | Sudah pulang |
| **Batal** | Dibatalkan, refund diproses |

### 5.3 Profil Jamaah

Data yang disimpan per jamaah:

**Identitas (diisi oleh AI Scanner atau manual)**
- Nama lengkap sesuai paspor
- NIK KTP
- Nomor paspor, tanggal terbit, tanggal expired
- Tempat & tanggal lahir
- Jenis kelamin
- Kewarganegaraan
- Alamat lengkap
- Golongan darah

**Kontak**
- Nomor HP (WhatsApp)
- Email
- Kontak darurat: nama & nomor HP

**Hubungan**
- Mahram (relasi ke jamaah lain dalam trip yang sama)
- Sumber lead: walk-in / referral / online / agen (nama agen jika via agen)

**Histori Perjalanan**
- Daftar semua trip yang pernah diikuti (otomatis terisi)
- Status tiap trip
- Total yang sudah dibayar

### 5.4 Tindakan per Jamaah

- Tambah catatan internal (visible ke semua staff, tidak ke jamaah)
- Tandai follow-up: set pengingat dengan tanggal & deskripsi
- Kirim pesan WA: buka wa.me/{nomor} dengan template pesan
- Generate invoice
- Upload dokumen (KTP, paspor, foto)
- Lihat histori semua transaksi pembayaran

### 5.5 Pendaftaran Self-Service (opsional)

Admin generate link pendaftaran per paket: `jamaah.in/daftar/{paket-token}`

Calon jamaah isi form:
- Data diri dasar
- Pilih tipe kamar
- Upload foto KTP, paspor (opsional di tahap ini)
- Nomor HP (untuk OTP verifikasi)

Masuk ke antrian pendaftaran → admin review → Approve (otomatis buat profil + invoice awal) atau Reject dengan alasan.

### 5.6 Notifikasi & Reminder Otomatis

- Jamaah yang masih di status Booking lebih dari X hari → reminder bayar DP
- Jamaah yang jatuh tempo cicilan dalam 7 hari → reminder
- Paspor expired dalam 90 hari → alert ke admin
- Paspor expired dalam 30 hari → alert urgent ke admin + owner

---

## 6. Modul 3 — Invoice & Pembayaran

### 6.1 Deskripsi

Jantung dari sistem administrasi. Setiap jamaah yang terdaftar di paket memiliki invoice yang mencatat total tagihan, skema pembayaran yang disepakati, dan seluruh histori pembayaran yang masuk.

### 6.2 Pembuatan Invoice

Invoice dibuat otomatis saat jamaah di-approve dari pendaftaran, atau dibuat manual oleh admin.

**Komponen Invoice:**
- Nomor invoice otomatis (format: INV/2025/MMDD/XXXX)
- Nama jamaah + paket + tipe kamar
- Harga paket (snapshot harga saat pendaftaran)
- Diskon (nominal atau persentase)
- Biaya tambahan (perlengkapan, upgrade kamar, lainnya)
- **Total tagihan**
- Tanggal diterbitkan
- Jatuh tempo

**Skema Pembayaran (dipilih saat buat invoice):**

*Skema 1 — DP + Pelunasan*
- Tentukan nominal atau persentase DP (misal: 30% atau Rp 8.000.000)
- Jatuh tempo pelunasan (misal: H-60 keberangkatan)

*Skema 2 — Cicilan Bebas*
- Admin input: jumlah cicilan, nominal per cicilan, tanggal jatuh tempo masing-masing
- Bisa berbeda nominal tiap cicilan (fleksibel)
- Sistem hitung apakah total cicilan = total tagihan (validasi)

*Skema 3 — Lunas Langsung*
- Tidak ada jatuh tempo cicilan; langsung catat pembayaran penuh

### 6.3 Rekam Pembayaran

Setiap kali jamaah bayar, admin input transaksi:
- Tanggal bayar
- Nominal
- Metode: Transfer Bank / QRIS / Tunai / Cek / Giro
- Bank tujuan / rekening (jika transfer)
- Nomor referensi / bukti transfer
- Upload foto bukti bayar (opsional)
- Catatan

Sistem otomatis:
- Update sisa tagihan
- Update status invoice (Belum Bayar → Sebagian → Lunas)
- Update status jamaah di pipeline

### 6.4 Output Dokumen

**Kwitansi Pembayaran (per transaksi)**
- Header: logo & nama travel
- Nomor kwitansi, tanggal, nama jamaah
- Nominal diterima, metode, oleh siapa
- Tanda terima digital
- Format: PDF siap cetak & kirim

**Invoice Resmi (per jamaah)**
- Rincian tagihan lengkap
- Tabel histori pembayaran yang sudah masuk
- Sisa tagihan yang belum dibayar
- Format: PDF, bisa dikirim via link WA

**Kartu Pembayaran (ringkasan cicilan)**
- Tabel semua termin cicilan: yang sudah bayar (✓), belum bayar (○), jatuh tempo
- Berguna untuk jamaah yang cicil lama

### 6.5 Rekonsiliasi & Monitoring

**Dashboard Piutang (untuk Owner & Admin)**
- Total piutang seluruh paket aktif
- Daftar jamaah yang jatuh tempo cicilan hari ini / minggu ini
- Jamaah yang melewati jatuh tempo (overdue)
- Filter per paket, per status, per metode bayar

**Laporan Kas Harian**
- Semua pembayaran masuk hari ini, dikelompokkan per metode
- Total kas masuk per rekening bank
- Berguna untuk rekonsiliasi manual dengan mutasi rekening

---

## 7. Modul 4 — Laporan Keuangan & P&L Trip

### 7.1 Deskripsi

Memberikan owner visibilitas penuh atas kesehatan keuangan bisnis travel, mulai dari profit per trip sampai arus kas keseluruhan.

### 7.2 Dashboard Owner

Tampilan utama saat login sebagai owner:

**Ringkasan Periode (bulan ini / tahun ini / custom range)**
- Total pemasukan dari jamaah
- Total pengeluaran ke vendor
- Gross profit
- Total piutang (belum dibayar jamaah)
- Total utang ke vendor (belum dibayar travel)

**Top 5 Trip Most Profitable (bulan ini)**

**Jamaah yang Harus Segera Di-follow-up**
- Jatuh tempo hari ini
- Overdue lebih dari 7 hari

### 7.3 P&L per Trip

Untuk setiap paket/trip, sistem menghitung:

```
PENDAPATAN
  Tagihan jamaah (total invoice)
  − Diskon yang diberikan
  = Total Pendapatan Bersih

PENGELUARAN
  Biaya tiket pesawat (total)
  Biaya hotel Makkah (total)
  Biaya hotel Madinah (total)
  Biaya visa (total)
  Biaya transportasi
  Biaya muthawwif / guide
  Biaya perlengkapan
  Biaya lain-lain
  = Total Pengeluaran

LABA KOTOR = Pendapatan Bersih − Total Pengeluaran
MARGIN % = Laba Kotor / Pendapatan Bersih × 100%
```

Perbandingan: Proyeksi Profit (dari komponen biaya yang diinput saat setup paket) vs Profit Aktual (dari pengeluaran nyata yang dicatat).

### 7.4 Laporan Piutang Aging

Laporan piutang dikelompokkan berdasarkan umur:
- 0-30 hari
- 31-60 hari
- 61-90 hari
- > 90 hari

Per jamaah: nama, paket, total tagihan, yang sudah dibayar, sisa.

### 7.5 Laporan Arus Kas

Proyeksi kas masuk dari cicilan jamaah yang akan datang (berdasarkan jadwal cicilan), berguna untuk planning pembayaran ke vendor.

### 7.6 Export

- Semua laporan bisa diexport ke Excel (.xlsx)
- Invoice & kwitansi bisa diexport ke PDF
- Format laporan kompatibel untuk diserahkan ke akuntan

---

## 8. Modul 5 — Vendor & Biaya Operasional

### 8.1 Deskripsi

Mencatat semua pengeluaran riil travel ke vendor eksternal untuk setiap trip. Data ini yang membentuk sisi "pengeluaran" di laporan P&L.

### 8.2 Master Data Vendor

Simpan database vendor yang sering digunakan:
- Maskapai (Garuda, Saudi Airlines, dll.)
- Hotel di Makkah & Madinah
- Perusahaan bus / transportasi lokal
- Vendor perlengkapan (koper, ihram, mukena)
- Vendor katering / konsumsi
- Vendor lainnya

Setiap vendor: nama, tipe, NPWP, alamat, kontak PIC, nomor rekening.

### 8.3 Tagihan Vendor per Trip

Untuk setiap trip, admin bisa input tagihan dari vendor:
- Pilih vendor dari master
- Deskripsi layanan (misal: "Hotel Makkah — 5 malam × 50 pax")
- Nominal total tagihan (dalam IDR atau SAR dengan konversi)
- Tanggal jatuh tempo pembayaran ke vendor
- Status: Belum Bayar / Sebagian / Lunas

### 8.4 Rekam Pembayaran ke Vendor

- Tanggal bayar
- Nominal
- Dari rekening mana
- Bukti transfer
- Sisa hutang ke vendor otomatis diupdate

### 8.5 Monitoring Hutang Vendor

- Daftar semua tagihan vendor yang belum / sebagian dibayar
- Filter per trip, per vendor, per jatuh tempo
- Alert jika jatuh tempo dalam 7 hari

---

## 9. Modul 6 — Komisi Agen & Referral

### 9.1 Deskripsi

Travel umroh umumnya memiliki jaringan sub-agen atau individu yang mendatangkan jamaah dengan imbalan komisi. Modul ini mengotomatisasi perhitungan dan pencatatan komisi.

### 9.2 Master Data Agen

- Nama agen / kantor agen
- Tipe: Perorangan / Badan Usaha
- Kota / wilayah kerja
- Kontak WA
- Nomor rekening untuk transfer komisi
- NPWP (untuk keperluan pajak)

### 9.3 Struktur Komisi

Komisi bisa dikonfigurasi per paket atau per agen:

- **Flat nominal**: Rp X per jamaah yang berhasil berangkat
- **Persentase**: X% dari harga paket
- **Bertingkat**: semakin banyak jamaah yang dikirim, komisi per orang makin besar

Contoh:
- 1-5 jamaah: Rp 500.000/orang
- 6-10 jamaah: Rp 700.000/orang
- >10 jamaah: Rp 1.000.000/orang

### 9.4 Trigger Komisi

Komisi dihitung otomatis ketika:
- Jamaah mencapai status **Lunas** (komisi penuh)
- Atau bisa dikonfigurasi saat status **Berangkat** (komisi dibayar setelah jamaah terbukti berangkat)

### 9.5 Rekap & Pembayaran Komisi

- Laporan komisi per agen per periode
- Status: Belum Dibayar / Sudah Dibayar
- Admin input tanggal & bukti transfer komisi

### 9.6 Portal Agen (Opsional — Fase 2)

Agen bisa login ke portal sederhana `jamaah.in/agen/{token}` untuk:
- Lihat jamaah yang mereka referralkan dan statusnya
- Lihat akumulasi komisi yang sudah/belum dibayar
- Tidak bisa melihat data keuangan travel secara keseluruhan

---

## 10. Modul 7 — Pengurusan Dokumen & Paspor

### 10.1 Deskripsi

Melacak kelengkapan dokumen setiap jamaah per trip. Checklist digital yang menggantikan spreadsheet atau papan tulis fisik di kantor.

### 10.2 Checklist Dokumen per Jamaah

Sistem menyediakan checklist default yang bisa dikustomisasi per paket:

**Dokumen Wajib**
- [ ] KTP (sudah di-scan & data diverifikasi)
- [ ] KK (Kartu Keluarga)
- [ ] Paspor (valid min. 6 bulan dari keberangkatan)
- [ ] Pas foto 4×6 background putih (4 lembar)
- [ ] Pas foto 3×4 background putih (2 lembar)
- [ ] Suntik meningitis (sertifikat ICV)
- [ ] Formulir pendaftaran

**Dokumen Tambahan (jika berlaku)**
- [ ] Surat mahram (untuk wanita tanpa mahram langsung)
- [ ] Akta nikah
- [ ] Akta lahir (untuk anak)
- [ ] Surat rekomendasi dari lurah / kepala desa

**Dokumen Visa**
- [ ] Formulir visa diisi
- [ ] Visa approved (nomor visa diinput)

### 10.3 Status per Dokumen

Setiap dokumen bisa ditandai:
- **Belum diterima** — default
- **Sudah diterima** — staf terima fisik atau digital
- **Diproses** — misal: sedang diurus visa
- **Selesai** — dokumen sudah lengkap & kembali ke jamaah / siap berangkat

### 10.4 Upload Dokumen Digital

Untuk setiap dokumen, admin bisa upload file digital (PDF, JPG, PNG) yang bisa diakses kapan saja tanpa harus cari dokumen fisik.

### 10.5 Integrasi AI Scanner

Saat admin upload foto KTP/KK/Paspor di modul dokumen, AI Scanner otomatis aktif:
- Data diekstrak dan dipopulate ke profil jamaah
- Admin tinggal verifikasi & konfirmasi
- Foto tersimpan sebagai dokumen terkait

### 10.6 Alert Paspor Expired

| Kondisi | Alert |
|---------|-------|
| Paspor expired dalam 90 hari dari keberangkatan | Peringatan kuning di profil |
| Paspor expired dalam 30 hari dari keberangkatan | Peringatan merah, notifikasi ke owner |
| Paspor sudah expired | Blokir status jamaah sampai diperbaharui |

---

## 11. AI Scanner (Dipertahankan & Diperkaya dari v1)

### 11.1 Perubahan dari v1

AI Scanner tetap menjadi fitur andalan, tetapi output-nya berubah:

| v1 | v2 |
|----|----|
| Output: 32 kolom Siskopatuh di Excel | Output: Populate profil jamaah di sistem CRM |
| Standalone tool | Terintegrasi penuh dengan modul Dokumen & CRM |
| Hanya untuk input Siskopatuh | Untuk pendaftaran & verifikasi jamaah |

### 11.2 Fitur yang Dipertahankan

- Upload KTP, KK, Paspor, Visa (JPG, PNG, WebP, PDF)
- AI ekstrak data (nama, NIK, nomor paspor, tanggal lahir, alamat, dll.)
- Batch processing hingga 50 file per request
- AI Cache: gambar yang sudah diproses tidak dikenakan biaya ulang
- Preview & edit data sebelum disimpan

### 11.3 Fitur Baru

- Hasil scan langsung bisa "Simpan ke Profil Jamaah" — terhubung ke trip yang dipilih
- Jika NIK / nomor paspor sudah ada di database, sistem mengenali sebagai jamaah lama (repeat customer) — data di-merge bukan duplikasi
- Export 32 kolom Siskopatuh tetap tersedia sebagai opsi (untuk kebutuhan Kemenag)

---

## 12. Manajemen Tim & Organisasi

### 12.1 Multi-User

Satu akun travel bisa memiliki multiple user dengan role berbeda:

| Role | Akses |
|------|-------|
| **Owner** | Full access semua modul + laporan keuangan + setting |
| **Admin** | Kelola jamaah, paket, invoice, dokumen — tidak bisa hapus data penting atau akses laporan keuangan sensitif |
| **Finance** | Khusus modul invoice, pembayaran, laporan keuangan |
| **CS / Marketing** | Khusus CRM pipeline, tidak bisa lihat laporan keuangan |
| **Viewer** | Read-only semua modul |

### 12.2 Audit Log

Setiap aksi tercatat: siapa, kapan, apa yang diubah. Owner bisa melihat log untuk keamanan dan akuntabilitas.

### 12.3 Multi-Branch (Fase 2)

Travel dengan beberapa cabang atau afiliasi bisa mengelola cabang terpisah dalam satu platform dengan laporan konsolidasi di level pusat.

---

## 13. Pricing

Dengan bertambahnya modul signifikan, tier pricing direvisi:

| Paket | Harga | Modul yang Termasuk |
|-------|-------|---------------------|
| **Free Trial** | Gratis 14 hari | Semua fitur Pro |
| **Starter** | Rp 149.000/bln | Paket, CRM, Invoice, Dokumen — maks 3 paket aktif, 2 user |
| **Pro** | Rp 299.000/bln | Semua modul kecuali Payroll & Multi-branch — 5 user |
| **Business** | Rp 599.000/bln | Semua 12 modul termasuk Payroll, Portal Agen, unlimited user |
| **Pro Tahunan** | Rp 2.990.000/thn | Hemat ~2 bulan vs Pro bulanan |
| **Business Tahunan** | Rp 5.990.000/thn | Hemat ~2 bulan vs Business bulanan |

*AI Scanner credits tetap terpisah dari subscription (lihat Bagian 13.2)*

---

## 14. User Flow Utama

### 14.1 Flow Onboarding Travel Baru

```
Daftar akun → Setup profil travel (nama, logo, rekening bank) →
Buat paket pertama → Input komponen harga → Publish paket →
Tambah jamaah pertama (manual atau AI Scanner) → Buat invoice → Rekam pembayaran
```

### 14.2 Flow Pendaftaran Jamaah Baru

```
Calon jamaah hubungi travel (WA/walk-in/agen)
  → Admin buka CRM → Tambah jamaah baru
  → Upload KTP/Paspor → AI Scanner ekstrak data (5-15 detik)
  → Verifikasi & simpan ke profil
  → Pilih paket + tipe kamar + skema pembayaran
  → Sistem generate invoice otomatis
  → Kirim invoice PDF ke WA jamaah
  → Rekam pembayaran DP
  → Status jamaah: Booking → DP
```

### 14.3 Flow Rekam Pembayaran Cicilan

```
Jamaah transfer cicilan ke rekening travel
  → Admin terima bukti di WA
  → Buka profil jamaah → Invoice → Tambah Pembayaran
  → Input nominal, tanggal, upload bukti
  → Sistem hitung sisa tagihan otomatis
  → Generate kwitansi PDF → Kirim ke WA jamaah
  → Status diupdate otomatis
```

### 14.4 Flow Review Keuangan Trip (Owner)

```
Login → Dashboard Owner
  → Pilih trip → P&L Trip
  → Lihat: Total Pendapatan, Total Pengeluaran Vendor, Gross Profit
  → Cek: Siapa yang belum lunas
  → Input pengeluaran vendor yang baru masuk
  → Export laporan ke Excel untuk akuntan
```

### 14.5 Flow Menjelang Keberangkatan

```
H-30 keberangkatan:
  → Sistem kirim alert: jamaah yang belum lunas (list)
  → Alert: paspor yang akan expired
  → Checklist dokumen: siapa yang belum lengkap

H-7 keberangkatan:
  → Export data jamaah ke Excel Siskopatuh (dari AI Scanner)
  → Rekap komisi agen yang perlu dibayar
  → Konfirmasi semua pengeluaran vendor sudah tercatat
```

---

## 15. Dashboard & Notifikasi

### 15.1 Dashboard Owner

Widget yang ditampilkan saat login sebagai Owner:

- **Total Pendapatan Bulan Ini** (vs bulan lalu: +/-%)
- **Total Piutang Aktif** (jamaah belum lunas, semua paket)
- **Total Hutang Vendor** (yang belum dibayar travel)
- **Gross Profit Bulan Ini**
- **Trip Aktif**: daftar paket yang sedang berjalan + progress pembayaran jamaah
- **Alert**: jamaah jatuh tempo hari ini, paspor expired, dokumen tidak lengkap
- **Grafik**: Pendapatan 6 bulan terakhir

### 15.2 Dashboard Admin/CS

- **Jamaah Perlu Di-follow-up**: overdue pembayaran, dokumen kurang
- **Pendaftaran Masuk**: dari link pendaftaran self-service (jika dipakai)
- **Trip Mendatang**: countdown H- keberangkatan
- **Quick Actions**: Tambah Jamaah, Buat Invoice, Rekam Pembayaran

### 15.3 Sistem Notifikasi

| Trigger | Penerima | Kanal |
|---------|---------|-------|
| Jamaah jatuh tempo cicilan | Admin, Owner | In-app notification |
| Jamaah overdue 7+ hari | Owner | In-app + email |
| Paspor expired 90 hari | Admin | In-app |
| Paspor expired 30 hari | Admin + Owner | In-app + email |
| Pembayaran baru masuk | Admin yang input | In-app |
| Paket hampir penuh (sisa 5 kursi) | Owner | In-app |

---

## 16. Keputusan Fitur dari v1

| Fitur v1 | Keputusan | Alasan |
|----------|-----------|--------|
| AI Scanner (OCR) | **Pertahankan + Perkuat** | Terbukti dipakai, jadi engine input data |
| Export Excel Siskopatuh | **Pertahankan** | Tetap dibutuhkan untuk pelaporan Kemenag |
| Manajemen Grup/Trip | **Transformasi** → Paket | Digabung ke modul Paket yang lebih kaya fitur |
| Auto-Rooming | **Simplify** | Hanya export PDF rooming list sederhana; detail WA group yang handle |
| Manifest Digital Mutawwif | **Hapus** | WA group sudah cukup; development cost tidak worth |
| WhatsApp Blast | **Simplify** | Tetap ada template WA, tapi kirim manual via wa.me; tidak perlu API blast |
| Itinerary Manager | **Hapus** | Menjadi bagian dari deskripsi paket (plain text), tidak perlu modul terpisah |
| Self-Service Registration | **Pertahankan** | Useful untuk agen yang kirim jamaah; masuk ke modul CRM |
| Team / Organisasi | **Pertahankan + Perkuat** | Role-based access lebih granular di v2 |
| Inventaris & Logistik | **Hapus** | Terlalu niche, bisa ditangani di modul Vendor sebagai pengeluaran |
| Dashboard Analytics | **Transformasi** → Financial Dashboard | Dari "stat jamaah" ke "financial health" |

---

## 17. Key Differentiators vs Kompetitor

### vs Software Akuntansi Umum (Jurnal, Accurate, Bukukas)

| Aspek | Akuntansi Umum | Jamaah.in v2 |
|-------|---------------|-------------|
| Setup | Perlu kustomisasi chart of accounts | Langsung pakai, sudah konfigurasi untuk travel umroh |
| Paket umroh | Tidak ada konsep paket trip | Native: paket, kuota, tanggal keberangkatan |
| Skema cicilan jamaah | Manual | Otomatis: DP + pelunasan / cicilan bebas |
| Komisi agen | Manual | Otomatis berdasarkan trigger |
| Paspor & dokumen | Tidak ada | Native checklist per jamaah |
| AI Scanner | Tidak ada | Ekstrak 32+ field dari foto dokumen |
| Siskopatuh export | Tidak ada | Built-in |

### vs Spreadsheet Excel

- Tidak perlu keahlian Excel
- Multi-user simultan tanpa risiko overwrite
- Notifikasi & alert otomatis
- Laporan real-time tanpa perlu recalculate manual
- Data tidak hilang jika laptop rusak

### vs Aplikasi Sejenis (jika ada)

- Harga 5-10x lebih murah dari solusi enterprise
- Onboarding < 30 menit, tidak perlu training panjang
- Fokus pada kebutuhan PPIU Indonesia (Siskopatuh, mata uang IDR + SAR)

---

## 18. Roadmap Pengembangan

### Phase 1 — Foundation (3 bulan)
1. Manajemen Paket & Harga (dengan komponen biaya & bundle perlengkapan)
2. CRM & Pipeline Jamaah (profil + status + ukuran perlengkapan)
3. Invoice & Pembayaran (buat invoice, rekam bayar, kwitansi PDF)
4. Dashboard Owner (piutang, P&L sederhana)
5. AI Scanner → populate profil jamaah langsung

### Phase 2 — Operations (2 bulan)
6. Vendor & Biaya Operasional
7. P&L per Trip detail (termasuk HPP perlengkapan)
8. Laporan Piutang Aging & Arus Kas Proyeksi
9. Alert & Notifikasi otomatis
10. Dokumen & Checklist Paspor

### Phase 3 — Trust & Inventory (2 bulan)
11. E-Kontrak Digital (template, variabel, tanda tangan, monitoring)
12. Pembatalan & Refund (full workflow + kebijakan + laporan)
13. Persediaan / Inventory (stock in, proyeksi, distribusi otomatis, kartu stok)

### Phase 4 — People & Commission (2 bulan)
14. Penggajian / Payroll (karyawan tetap + freelance per trip + kasbon)
15. Komisi Agen & Referral (otomatis + portal agen)
16. Export laporan profesional (Excel + PDF yang rapi)

### Phase 5 — Growth (Ongoing)
17. Pendaftaran self-service via link publik
18. Multi-branch & konsolidasi laporan
19. Integrasi rekening bank (auto-reconcile) — v3
20. Mobile app native (iOS & Android)
21. API terbuka untuk integrasi pihak ketiga

---

## 19. Tech Stack v2 — Go Microservices

v2 adalah full rewrite dari v1 (Python/FastAPI). Alasan utama: arsitektur microservices membutuhkan service yang startup cepat (<10ms), memory footprint kecil (~15MB/container), dan concurrency tinggi — ketiganya adalah kekuatan inti Go. Python/FastAPI kurang optimal untuk pola ini.

### 19.1 Bahasa & Framework Utama

**Go (Golang)** — digunakan untuk semua backend services.

Keunggulan untuk konteks ini:
- Goroutines: concurrency ribuan request dengan overhead minimal (~2KB/goroutine vs ~1MB/OS thread)
- Kompilasi ke single static binary — ideal untuk Docker container kecil
- gRPC first-class: komunikasi antar service typed, lebih cepat 5-10x dari REST/JSON
- Strong typing mencegah bug runtime di production
- Digunakan oleh: Uber (microservices), Docker (container runtime), Kubernetes (orchestrator)

### 19.2 Daftar Services

| Service | Tanggung Jawab | Framework |
|---------|---------------|-----------|
| **API Gateway** | Single entry point, routing, rate limiting, TLS termination | Go + Fiber |
| **Auth Service** | JWT issuance & validation, RBAC, OTP, session management | Go + gRPC |
| **Package Service** | Paket & harga, komponen biaya, bundle perlengkapan | Go + gRPC |
| **CRM Service** | Profil jamaah, pipeline status, follow-up, histori | Go + gRPC |
| **Invoice Service** | Invoice lifecycle, rekam pembayaran, skema cicilan | Go + gRPC |
| **Finance Service** | P&L per trip, laporan piutang, arus kas proyeksi | Go + gRPC |
| **Vendor Service** | Master vendor, tagihan vendor, hutang vendor | Go + gRPC |
| **Contract Service** | Template e-kontrak, alur tanda tangan, penyimpanan PDF | Go + gRPC |
| **Inventory Service** | Stok master, stock in/out, distribusi, kartu stok | Go + gRPC |
| **Payroll Service** | Slip gaji, komponen gaji, PPh 21, kasbon, honor per trip | Go + gRPC |
| **Commission Service** | Kalkulasi komisi agen, portal agen, rekap pembayaran | Go + gRPC |
| **Document Service** | Checklist dokumen, upload, alert paspor expired | Go + gRPC |
| **AI / OCR Service** | Google Gemini Vision integration, AI cache layer | Go + gRPC |
| **PDF Service** | Generate semua PDF: invoice, kwitansi, slip gaji, kontrak | Go + Chromium headless |
| **Notification Service** | WA (Fonnte), Email (Resend), in-app push, scheduler | Go + gRPC |

### 19.3 Komunikasi Antar Service

| Protokol | Digunakan untuk | Alasan |
|----------|----------------|--------|
| **gRPC + Protobuf** | Sync request/response antar service | Typed schema, ~10x lebih cepat dari REST JSON, auto-generate client code |
| **NATS JetStream** | Async event bus antar service | Fire-and-forget events (jamaah lunas → trigger invoice update + komisi + notif WA sekaligus) |
| **REST / JSON** | Client (browser/mobile) → API Gateway | Standar web, mudah dikonsumsi frontend Svelte |

**Contoh event flow NATS:**
```
Invoice Service publish: "payment.completed" {jamaah_id, invoice_id, amount}
  → Finance Service subscribe: update P&L trip
  → Commission Service subscribe: hitung komisi agen jika ada
  → Notification Service subscribe: kirim kwitansi WA ke jamaah
  → Inventory Service subscribe: unlock distribusi perlengkapan jika sudah lunas
```

### 19.4 Data Layer

| Komponen | Teknologi | Pola |
|----------|-----------|------|
| **Primary database** | PostgreSQL 16 (self-hosted) | Database-per-service: setiap service punya schema/DB sendiri — tidak ada shared database |
| **Cache & session** | Redis 7 (self-hosted) | Rate limiting, JWT blacklist, API response cache, AI OCR cache |
| **Event bus** | NATS JetStream (self-hosted) | Durable event stream, replay capability |
| **File storage** | MinIO (self-hosted) | Dokumen jamaah, foto KTP/paspor, PDF invoice — S3-compatible API, data tidak keluar server |
| **Secret management** | `.env` terenkripsi + SOPS | Sederhana tapi aman untuk single-server; cukup untuk skala ini |

**Database-per-service** adalah pola kunci microservices: setiap service adalah satu-satunya yang boleh mengakses database-nya sendiri. Service lain harus minta data melalui gRPC API, bukan direct DB query. Implementasi praktis di dedicated server: satu instance PostgreSQL dengan multiple databases (satu per service) — lebih efisien resource daripada multiple PostgreSQL instance.

### 19.5 Frontend (Dipertahankan dari v1)

| Layer | Teknologi |
|-------|-----------|
| **Framework** | Svelte 5 + SvelteKit |
| **Styling** | TailwindCSS |
| **PWA** | Service worker, installable di HP |
| **API client** | Fetch API + type-safe client dari Protobuf definitions |
| **Static hosting** | Di-serve langsung dari server via Nginx (bukan CDN eksternal) |

### 19.6 Server Specs & Alokasi Storage (500 GB)

Dedicated server digunakan untuk semua layer: aplikasi, database, file storage, monitoring.

**Estimasi Alokasi Disk:**

| Partisi / Direktori | Alokasi | Isi |
|--------------------|---------|-----|
| OS + system | 30 GB | Ubuntu 22.04 LTS, dependencies |
| Docker images & containers | 40 GB | Semua service images + build cache |
| PostgreSQL data | 80 GB | Database semua services (jamaah, invoice, dll.) |
| Redis data | 5 GB | Cache, session, rate limit |
| NATS JetStream | 10 GB | Event log buffer |
| MinIO (file storage) | 200 GB | Foto KTP/paspor, PDF invoice, kontrak, slip gaji |
| Logs (Loki) | 40 GB | Centralized log 90 hari terakhir |
| Monitoring data (Prometheus) | 20 GB | Metrics 30 hari terakhir |
| Backup lokal (pg_dump) | 60 GB | Snapshot harian 7 hari terakhir |
| Buffer & pertumbuhan | 15 GB | Ruang gerak |
| **Total** | **500 GB** | |

*Estimasi ini untuk ~500 travel aktif x ~200 jamaah x rata-rata 5 dokumen — cukup untuk 2-3 tahun operasi.*

**Rekomendasi Server Minimum:**
- CPU: 8 core (untuk menjalankan ~15 service container secara paralel)
- RAM: 16 GB (setiap Go service ~50-100MB, total ~2GB services + 4GB DB + 2GB Redis + sisanya OS/buffer)
- Storage: 500 GB SSD (NVMe lebih baik untuk I/O database)
- Network: 1 Gbps uplink

### 19.7 Infrastructure & DevOps (Self-Hosted)

| Komponen | Teknologi | Keterangan |
|----------|-----------|-----------|
| **Containerization** | Docker + Docker Compose | Setiap service = 1 container; Compose untuk orchestration single-server |
| **Orchestration** | **k3s** (lightweight Kubernetes) | Full K8s API tapi ringan — cocok untuk single dedicated server, mudah scale ke multi-node nanti |
| **Ingress / Reverse Proxy** | **Traefik v3** | Routing ke service, SSL auto-renew via Let's Encrypt, dashboard monitoring |
| **File storage** | **MinIO** | Self-hosted S3-compatible — data dokumen tidak keluar server |
| **CI/CD** | GitHub Actions (build + test) + **Watchtower** | Push ke GitHub -> Actions build & push image -> Watchtower auto-pull & restart di server |
| **Image registry** | GitHub Container Registry (GHCR) | Gratis untuk public/private repo |
| **Monitoring** | Prometheus + Grafana | Self-hosted, metrics semua service |
| **Logging** | Loki + Promtail + Grafana | Centralized log aggregation, semua log dari semua container |
| **Tracing** | Jaeger | Distributed tracing antar service |
| **Load testing** | k6 | Dijalankan lokal sebelum deploy ke server |
| **Process manager** | systemd + k3s | k3s di-manage systemd, auto-restart jika server reboot |

**Kenapa k3s bukan Docker Compose biasa?** Docker Compose tidak punya rolling deploy tanpa downtime atau resource limit per service yang proper. k3s memberikan semua kemampuan Kubernetes dengan overhead minimal — bisa jalan di server 2GB RAM sekalipun, dan kalau suatu saat perlu tambah node, tinggal join ke cluster yang sama.

### 19.8 Topologi Jaringan di Server

```
Internet
    |
    v
Cloudflare (DNS + proxy — Free tier, proteksi DDoS dasar)
    |
    v
Dedicated Server :443 / :80
    |
    v
Traefik (ingress, SSL termination, routing)
    |
    +---> /api/*          -> API Gateway service
    +---> /               -> SvelteKit frontend (static)
    +---> /minio          -> MinIO console (internal only)
    +---> /grafana        -> Grafana dashboard (internal only)
         |
         v
    k3s cluster (semua pod di server yang sama)
    +-- api-gateway, auth-service
    +-- package-service, crm-service, invoice-service
    +-- finance-service, vendor-service, contract-service
    +-- inventory-service, payroll-service, commission-service
    +-- document-service, ai-ocr-service, pdf-service, notification-service
    +-- postgresql (1 instance, multiple databases)
    +-- redis, nats, minio
    +-- prometheus + grafana + loki + jaeger
```

### 19.9 Backup Strategy

Data di dedicated server harus punya backup offsite — kalau server crash, tidak ada cloud managed backup yang menyelamatkan.

**Stack backup: rclone + rclone crypt → Google Drive (Google One)**

Sudah berlangganan Google One sehingga tidak ada biaya tambahan. Yang wajib diaktifkan adalah **rclone crypt** — data dienkripsi di server sebelum dikirim ke Google Drive. Google hanya melihat file terenkripsi, tidak bisa membaca isi foto KTP, paspor, atau dokumen finansial jamaah sama sekali.

```bash
# Konfigurasi rclone — simpan di /etc/rclone.conf (permission 600)
[gdrive]
type = drive
# ... OAuth2 token dari: rclone config

[gdrive-crypt]
type = crypt
remote = gdrive:jamaah-in-backup
filename_encryption = standard
directory_name_encryption = true
password  = <diambil dari SOPS secret>
password2 = <salt, diambil dari SOPS secret>

# Contoh backup script (dijalankan via cron)
rclone sync /backup/postgresql gdrive-crypt:postgresql/ --transfers=4
rclone sync /backup/minio      gdrive-crypt:minio/      --transfers=8
```

Kunci enkripsi (`password` + `password2`) disimpan terenkripsi via SOPS di server, bukan di Google Drive.

| Layer | Strategi | Frekuensi | Retensi |
|-------|----------|-----------|---------|
| **PostgreSQL** | `pg_dump` + gzip → `rclone sync` ke `gdrive-crypt:postgresql/` | Setiap 6 jam | 7 hari lokal, 30 hari GDrive |
| **MinIO** | `rclone sync /minio` ke `gdrive-crypt:minio/` | Setiap malam | 30 hari GDrive |
| **Redis** | RDB snapshot lokal | Setiap jam | 24 jam (cache, tidak kritis) |
| **NATS** | JetStream snapshot lokal | Setiap hari | 7 hari lokal |
| **Config & secrets** | Git private repo (secrets di-encrypt SOPS) | Setiap ada perubahan | Permanent |
| **Full server snapshot** | Snapshot dari provider server | Mingguan | 4 snapshot terakhir |

**Catatan operasional:**
- Google Drive membatasi upload **750 GB/hari** — untuk initial backup besar, jalankan bertahap. Setelah itu incremental backup harian jauh di bawah limit.
- Gunakan `rclone sync` (bukan `copy`) agar file lama yang sudah terhapus di server ikut terhapus dari GDrive — hemat kuota.
- **Wajib test restore berkala** setiap bulan: `rclone copy gdrive-crypt:postgresql/ /tmp/restore-test/` — backup yang belum pernah dicoba restore belum bisa diandalkan.

### 19.10 Security (Self-Hosted Context)

| Layer | Implementasi |
|-------|-------------|
| **Akses server** | SSH key only, password auth dinonaktifkan, port SSH dipindah dari 22 |
| **Firewall** | UFW: hanya port 80, 443, dan SSH custom yang terbuka dari luar |
| **Fail2ban** | Auto-ban IP yang gagal SSH login 5x |
| **TLS client ke server** | HTTPS via Traefik + Let's Encrypt (auto-renew) |
| **Komunikasi antar service** | Internal k3s network — tidak exposed ke luar sama sekali |
| **Secrets** | SOPS + Age key untuk enkripsi `.env` files di Git |
| **Database** | PostgreSQL hanya listen di internal network, tidak exposed keluar |
| **MinIO** | Hanya accessible dari internal network, tidak exposed langsung ke internet |
| **Monitoring tools** | Grafana, Jaeger — hanya accessible via Traefik dengan basic auth |
| **Auto-update OS** | `unattended-upgrades` untuk security patches otomatis |
| **Audit log** | Semua write operation dicatat di level aplikasi |

### 19.11 Integrasi Eksternal (Tetap, Data Tidak Disimpan di Sana)

| Layanan | Digunakan Untuk | Catatan |
|---------|----------------|---------|
| **Google Gemini Vision** | OCR dokumen (KTP, paspor, visa) | API call keluar, hasil kembali ke server — tidak disimpan di Google |
| **Pakasir** | Payment gateway (QRIS, VA) | Webhook masuk ke server |
| **Fonnte** | WhatsApp API untuk notifikasi & OTP | API call keluar server |
| **Resend** | Email transaksional (invoice, kwitansi, kontrak, slip gaji) | API call keluar server |
| **Cloudflare** | DNS + DDoS protection dasar (free tier) | Tidak pakai R2 — sudah ada MinIO di server sendiri |
| **Google Drive** | Offsite backup via rclone crypt | Sudah termasuk Google One — tidak ada biaya tambahan |
| **GitHub** | Source code + CI/CD (Actions) + image registry (GHCR) | Gratis untuk tim kecil |

### 19.9 Mengapa Bukan Python lagi?

| Kriteria | Python/FastAPI (v1) | Go (v2) |
|----------|--------------------|---------| 
| Startup time | ~500ms-1s (cold start) | <10ms |
| Memory per service | ~100-200MB | ~15-30MB |
| Goroutine/Thread model | GIL membatasi true parallelism | Native goroutines, no GIL |
| gRPC | Bisa, tapi second-class | First-class, generated code lebih bersih |
| Binary deployment | Butuh Python runtime + venv | Single static binary |
| Type safety | Dynamic typing, runtime errors | Compile-time type checking |
| Cocok untuk microservices | Cukup (monolith lebih natural) | Dirancang untuk ini |

Untuk monolith atau prototype cepat, Python masih excellent. Untuk microservices yang butuh performa dan skalabilitas, Go adalah pilihan yang tepat. v2 adalah greenfield project — tidak ada legacy yang perlu dipertahankan.

---

## 20. Risiko & Mitigasi

| Risiko | Probabilitas | Dampak | Mitigasi |
|--------|-------------|--------|----------|
| User tidak mau pindah dari Excel | Tinggi | Tinggi | Onboarding hands-on, import dari Excel |
| Data jamaah hilang / leak | Rendah | Sangat Tinggi | Enkripsi, backup harian, audit log |
| Travel kecil tidak mau bayar | Sedang | Sedang | Free trial 14 hari, pricing tier yang terjangkau |
| AI Scanner accuracy rendah | Rendah | Sedang | Wajib review sebelum simpan, AI Cache untuk hemat biaya |
| Regulasi Kemenag berubah | Sedang | Sedang | Modul Siskopatuh bisa diupdate cepat karena modular |

---

## 21. Success Metrics

### Business Metrics (6 bulan post-launch)
- MRR (Monthly Recurring Revenue): target Rp 50 juta
- Jumlah travel aktif berbayar: target 300
- Churn rate: < 5% per bulan
- NPS: > 40

### Product Metrics
- Waktu setup paket baru: < 10 menit
- Waktu buat invoice jamaah: < 2 menit
- % travel yang aktif pakai modul invoice: > 80% dalam 30 hari pertama
- AI Scanner accuracy rate: > 95%

### Adoption Metrics
- DAU/MAU ratio: > 60% (artinya dipakai hampir setiap hari kerja)
- Feature adoption modul Laporan Keuangan: > 70%

---

## 22. Modul 8 — E-Kontrak Digital

### 22.1 Deskripsi

Setiap jamaah yang mendaftar wajib menandatangani surat perjanjian perjalanan (kontrak) dengan travel. Selama ini kontrak dicetak fisik, ditandatangani, lalu difoto/discan — proses yang lambat dan rawan hilang. Modul E-Kontrak mendigitalkan proses ini dari awal sampai akhir.

### 22.2 Template Kontrak

Admin bisa membuat dan menyimpan template kontrak yang bisa digunakan berulang kali:

- **Editor template**: rich text editor dengan variabel dinamis
- **Variabel yang tersedia**:
  - `{{nama_jamaah}}` — nama lengkap sesuai paspor
  - `{{no_paspor}}` — nomor paspor
  - `{{nama_paket}}` — nama paket
  - `{{tanggal_berangkat}}` — tanggal keberangkatan
  - `{{tanggal_pulang}}` — tanggal kepulangan
  - `{{tipe_kamar}}` — quad / triple / double / single
  - `{{harga_paket}}` — harga sesuai tipe kamar (format Rupiah)
  - `{{skema_bayar}}` — ringkasan skema pembayaran yang disepakati
  - `{{nama_travel}}` — nama travel / PPIU
  - `{{tanggal_kontrak}}` — tanggal kontrak ditandatangani
  - `{{ketentuan_refund}}` — tabel kebijakan refund dari Modul 9 (auto-populate)
- **Pasal-pasal umum** yang bisa dimasukkan: hak & kewajiban jamaah, hak & kewajiban travel, ketentuan pembatalan & refund, ketentuan force majeure
- Bisa simpan beberapa template (misal: template umroh reguler vs haji khusus)

### 22.3 Alur Penandatanganan

```
Admin generate kontrak → Sistem isi variabel otomatis dari data jamaah →
Preview PDF kontrak → Kirim link ke jamaah via WA / email →
Jamaah buka link di HP → Baca kontrak → Tanda tangan digital (draw/type) →
Upload foto KTP sebagai verifikasi identitas (opsional) →
Konfirmasi → Kontrak tersimpan dengan timestamp & IP address →
Admin & jamaah sama-sama dapat PDF kontrak yang sudah ditandatangani
```

### 22.4 Halaman Penandatanganan Jamaah

Jamaah membuka link di HP (tidak perlu install app):
- Tampil kontrak dalam format yang mudah dibaca (mobile-friendly)
- Tombol scroll-to-sign: jamaah harus scroll sampai bawah sebelum bisa tanda tangan
- Area tanda tangan: draw dengan jari di layar sentuh atau type nama
- Checkbox persetujuan: "Saya menyatakan telah membaca dan menyetujui seluruh isi kontrak"
- Tombol Tanda Tangan — generate PDF final dengan tanda tangan tertanam
- Link expires setelah 7 hari jika belum ditandatangani

### 22.5 Penyimpanan & Keabsahan

- Setiap kontrak yang ditandatangani disimpan sebagai PDF permanen dengan:
  - Tanda tangan digital tertanam
  - Timestamp (tanggal + jam + zona waktu)
  - IP address penandatangan
  - Hash dokumen SHA-256 (untuk verifikasi integritas — jika file diubah, hash berubah)
- Kontrak tidak bisa diubah setelah ditandatangani (immutable)
- Catatan: e-kontrak ini bersifat administratif dan operasional. Untuk keperluan hukum formal yang memerlukan kekuatan hukum penuh, integrasi dengan platform e-sign tersertifikasi (PrivyID, Tanda) bisa dipertimbangkan di fase berikutnya.

### 22.6 Monitoring Status Kontrak

| Status | Keterangan |
|--------|-----------|
| `Belum Dikirim` | Kontrak belum di-generate / dikirim |
| `Terkirim` | Link sudah dikirim ke jamaah |
| `Ditandatangani` | Jamaah sudah tanda tangan, PDF tersimpan |
| `Expired` | Link sudah 7 hari tidak ditandatangani |

- Dashboard admin: daftar jamaah yang belum tanda tangan kontrak
- Reminder otomatis: jika 3 hari belum ditandatangani, sistem kirim reminder via WA

### 22.7 Integrasi dengan Modul Lain

- Kontrak otomatis di-generate bersamaan dengan invoice (opsional, bisa dipisah)
- Status "Ditandatangani" bisa menjadi syarat sebelum pembayaran DP dicatat (toggle: wajib / tidak wajib)
- Kontrak tersimpan di tab Dokumen pada profil jamaah

---

## 23. Modul 9 — Pembatalan & Refund

### 23.1 Deskripsi

Pembatalan jamaah adalah skenario yang rumit: ada biaya yang sudah terlanjur dikeluarkan travel ke vendor (tiket, visa), ada kebijakan potongan yang berbeda per travel, dan prosesnya harus transparan agar tidak menimbulkan konflik. Modul ini mendefinisikan workflow pembatalan yang jelas, terdokumentasi, dan dapat diaudit.

### 23.2 Kebijakan Refund (Master Policy)

Admin mendefinisikan kebijakan refund default yang bisa di-override per paket:

**Struktur Kebijakan Berdasarkan Waktu Pembatalan:**

| Waktu Pembatalan | Potongan Default |
|-----------------|----------|
| > 90 hari sebelum berangkat | Biaya administrasi flat (contoh: Rp 500.000) |
| 60–90 hari sebelum berangkat | 25% dari harga paket |
| 30–59 hari sebelum berangkat | 50% dari harga paket |
| 15–29 hari sebelum berangkat | 75% dari harga paket |
| < 15 hari sebelum berangkat | 100% hangus (no refund) |

- Admin bebas kustomisasi persentase, range hari, dan biaya flat
- Kebijakan ini otomatis masuk ke variabel `{{ketentuan_refund}}` di template kontrak

### 23.3 Alur Pembatalan — Detail Flow

#### Step 1: Inisiasi Pembatalan

- **Jamaah minta batal**: admin buka profil jamaah → klik "Proses Pembatalan"
- **Travel terpaksa batal** (jamaah tidak lolos syarat visa, dll.): admin inisiasi dengan catatan alasan

Admin isi form inisiasi:
- Alasan pembatalan (pilihan: Permintaan Jamaah / Tidak Lolos Dokumen / Force Majeure / Lainnya) + keterangan bebas
- Siapa yang meminta batal: Jamaah / Travel
- Tanggal permintaan pembatalan

#### Step 2: Kalkulasi Refund Otomatis

Sistem menghitung secara otomatis:

```
KALKULASI REFUND OTOMATIS
────────────────────────────────────────────────────────
Total yang sudah dibayar jamaah       Rp 25.000.000
Harga paket (dari invoice)            Rp 29.000.000
Sisa tagihan yang belum dibayar       Rp  4.000.000

Hari menuju keberangkatan             45 hari
Kebijakan yang berlaku                Potongan 50%

Potongan (50% × Rp 29.000.000)        Rp 14.500.000
Biaya administrasi tambahan           Rp    500.000
──────────────────────────────────────────────────
Total potongan                        Rp 15.000.000

Refund ke jamaah = Dibayar − Total Potongan
                = Rp 25.000.000 − Rp 15.000.000
                = Rp 10.000.000

Sisa tagihan Rp 4.000.000 → DIHAPUS (tidak ditagih)
────────────────────────────────────────────────────────
```

Admin bisa **override manual** kalkulasi jika ada pertimbangan khusus, wajib isi alasan override (tercatat di audit log).

#### Step 3: Review & Persetujuan Owner

- Jika nominal refund di atas threshold (misal Rp 5 juta, bisa dikonfigurasi), sistem otomatis eskalasi ke Owner
- Owner menerima notifikasi in-app + email
- Owner bisa: **Approve** / **Tolak** / **Minta Revisi Kalkulasi**
- Jika refund kecil (di bawah threshold), admin langsung bisa approve sendiri

#### Step 4: Komunikasi ke Jamaah

Setelah diapprove, sistem generate **Surat Konfirmasi Pembatalan** (PDF) berisi:
- Konfirmasi pembatalan resmi diterima
- Rincian kalkulasi potongan (transparan, tidak ada yang disembunyikan)
- Jumlah refund yang akan dikembalikan
- Instruksi: jamaah isi rekening tujuan refund via form link
- Estimasi waktu proses refund (admin input: misal 7–14 hari kerja)

Admin kirim dokumen ke jamaah via WA atau email.

#### Step 5: Input Rekening & Proses Transfer

- Jamaah mengisi rekening via link form sederhana (nama bank, nomor rekening, nama pemilik)
- Admin terima data rekening → lakukan transfer manual di bank
- Admin catat di sistem: tanggal transfer, nominal, upload bukti

#### Step 6: Closing Pembatalan

Setelah transfer dikonfirmasi:
- Status jamaah: **"Batal — Refund Selesai"** atau **"Batal — No Refund"**
- Kursi yang dibatalkan **otomatis kembali ke kuota paket** (available kembali)
- Jurnal keuangan otomatis dicatat:
  - Pengembalian dana: keluar dari kas
  - Koreksi pendapatan: revenue dikoreksi sebesar harga paket dikurangi potongan
- Profil jamaah tetap tersimpan untuk histori — tidak dihapus

### 23.4 Pembatalan Seluruh Paket (Force Majeure)

Jika travel membatalkan satu paket secara keseluruhan:
- Admin trigger "Batalkan Paket" di halaman paket
- Input alasan + estimasi biaya vendor yang sudah terlanjur keluar dan tidak bisa di-refund (tiket, visa)
- Sistem generate daftar semua jamaah + kalkulasi refund masing-masing (proporsional)
- Owner approve → proses per jamaah berjalan paralel

### 23.5 Status Pembatalan

| Status | Keterangan |
|--------|-----------|
| `Draft` | Baru diinisiasi, kalkulasi belum final |
| `Menunggu Approval` | Menunggu owner approve |
| `Approved` | Disetujui, menunggu data rekening jamaah |
| `Diproses` | Transfer sudah dilakukan, menunggu konfirmasi |
| `Selesai — Refund` | Refund selesai, kasus closed |
| `Selesai — No Refund` | Hangus sesuai kebijakan, kasus closed |
| `Ditolak` | Owner tolak, kembali ke negosiasi |

### 23.6 Laporan Pembatalan

- Daftar semua pembatalan per periode dengan status masing-masing
- Total refund yang sudah dibayarkan vs yang masih diproses
- Analisis alasan pembatalan terbanyak (insight untuk improvement paket)
- Dampak ke revenue per paket

---

## 24. Modul 10 — Persediaan (Inventory) Travel

### 24.1 Deskripsi

Travel umroh umumnya menyediakan perlengkapan fisik kepada jamaah: koper, tas kabin, kain ihram, mukena, seragam baju, buku panduan, dan lainnya. Modul ini mengelola stok perlengkapan layaknya modul inventory di software akuntansi (Accurate, Zahir), dengan pengurangan stok otomatis berbasis distribusi ke jamaah.

### 24.2 Master Item Persediaan

Admin mendefinisikan daftar item yang dikelola stoknya:

| Kode Item | Nama Item | Satuan | Kategori | Dikembalikan? |
|-----------|-----------|--------|----------|--------------|
| KPR-L | Koper Besar (L) | Unit | Koper | Tidak |
| KPR-M | Koper Medium (M) | Unit | Koper | Tidak |
| TKB-STD | Tas Kabin Standar | Unit | Tas | Tidak |
| IHR-S | Kain Ihram Size S | Set | Ihram | Tidak |
| IHR-M | Kain Ihram Size M | Set | Ihram | Tidak |
| IHR-L | Kain Ihram Size L | Set | Ihram | Tidak |
| IHR-XL | Kain Ihram Size XL | Set | Ihram | Tidak |
| MKN-S | Mukena Size S | Set | Mukena | Tidak |
| MKN-M | Mukena Size M | Set | Mukena | Tidak |
| MKN-L | Mukena Size L | Set | Mukena | Tidak |
| BJU-S | Seragam Baju Size S | Pcs | Seragam | Tidak |
| BJU-M | Seragam Baju Size M | Pcs | Seragam | Tidak |
| BJU-L | Seragam Baju Size L | Pcs | Seragam | Tidak |
| BKP-STD | Buku Panduan | Eksemplar | Lainnya | Tidak |
| ID-CARD | ID Card Jamaah | Lembar | Lainnya | Ya |

Setiap item memiliki:
- Stok awal
- Harga beli rata-rata / HPP (auto-update dengan metode moving average)
- Stok minimum alert (notifikasi jika stok di bawah batas ini)
- Flag: dikembalikan setelah trip atau diberikan permanen

### 24.3 Penerimaan Stok (Stock In)

Setiap pembelian atau penerimaan barang dicatat:
- Tanggal terima
- Vendor / supplier (dari master vendor)
- Item & kuantitas per item
- Harga beli per unit (sistem update HPP rata-rata bergerak / moving average)
- Nomor faktur vendor + upload faktur

Stok otomatis bertambah setelah penerimaan dikonfirmasi admin.

### 24.4 Konfigurasi Bundle Perlengkapan per Paket

Saat setup paket, admin mendefinisikan perlengkapan yang diberikan per jamaah berdasarkan gender:

```
BUNDLE PAKET — Umroh Reguler Feb 2026
─────────────────────────────────────────────
Jamaah Pria:
  ✓ Koper Besar (L)              × 1
  ✓ Tas Kabin Standar            × 1
  ✓ Kain Ihram (ukuran sesuai)   × 1
  ✓ Seragam Baju (ukuran sesuai) × 1
  ✓ Buku Panduan                 × 1
  ✓ ID Card                      × 1

Jamaah Wanita:
  ✓ Koper Besar (L)              × 1
  ✓ Tas Kabin Standar            × 1
  ✓ Mukena (ukuran sesuai)       × 1
  ✓ Seragam Baju (ukuran sesuai) × 1
  ✓ Buku Panduan                 × 1
  ✓ ID Card                      × 1
```

Bundle bisa dikustomisasi per paket (paket VIP bisa berbeda spesifikasi dari reguler).

### 24.5 Ukuran Jamaah

Di profil setiap jamaah, admin input ukuran perlengkapan:
- Ukuran ihram / mukena: S / M / L / XL / XXL
- Ukuran seragam baju: S / M / L / XL / XXL

Jika jamaah belum diisi ukurannya, muncul alert di checklist persiapan trip.

### 24.6 Proyeksi Kebutuhan Stok Otomatis

Setelah bundle dikonfigurasi dan jamaah terdaftar, sistem otomatis kalkulasi kebutuhan total:

```
PROYEKSI KEBUTUHAN STOK
Paket: Umroh Reguler Feb 2026 | 50 Jamaah (28 Pria, 22 Wanita)

Item                     Butuh   Stok Kini   Selisih   Status
──────────────────────────────────────────────────────────────
Koper Besar (L)             50          65       +15   ✓ Cukup
Tas Kabin Standar           50          42        -8   ⚠ Kurang
Kain Ihram S                 4          10        +6   ✓ Cukup
Kain Ihram M                12          15        +3   ✓ Cukup
Kain Ihram L                 8           5        -3   ⚠ Kurang
Kain Ihram XL                4           6        +2   ✓ Cukup
Mukena S                     6           8        +2   ✓ Cukup
Mukena M                    10           7        -3   ⚠ Kurang
Mukena L                     6           9        +3   ✓ Cukup
Seragam S                   10          12        +2   ✓ Cukup
Seragam M                   24          20        -4   ⚠ Kurang
Seragam L                   16          18        +2   ✓ Cukup
Buku Panduan                50          60       +10   ✓ Cukup
ID Card                     50         100       +50   ✓ Cukup

⚠ 4 item memerlukan pengadaan sebelum keberangkatan
```

Alert otomatis muncul di dashboard jika ada item yang kurang dari kebutuhan trip.

### 24.7 Distribusi Perlengkapan & Stock Out Otomatis

Ini fitur kunci modul: **pengurangan stok otomatis saat distribusi dikonfirmasi**.

**Alur Distribusi:**

```
Admin buka Paket → Tab Persediaan → "Distribusi Perlengkapan"

Tabel jamaah × item:
┌──────────────────┬────────────┬──────────────┬───────────────┐
│ Nama Jamaah      │ Koper L    │ Ihram M      │ Buku Panduan  │
├──────────────────┼────────────┼──────────────┼───────────────┤
│ Ahmad Fauzi      │ ○ Belum    │ ○ Belum      │ ✓ Diserahkan  │
│ Siti Rahayu      │ ✓ Diserahkan│ —           │ ✓ Diserahkan  │
│ Budi Santoso     │ ○ Belum    │ ✓ Diserahkan │ ✓ Diserahkan  │
└──────────────────┴────────────┴──────────────┴───────────────┘
[Distribusi Massal — Semua Jamaah Lunas] [Export Checklist PDF]
```

Saat admin centang "Diserahkan" per item per jamaah:
- Stok item **berkurang 1 secara real-time**
- Timestamp distribusi tersimpan (siapa yang distribute, kapan)
- Tidak bisa di-undo tanpa approval (untuk cegah human error)

**Distribusi Massal**: Admin klik "Distribusi Massal" → sistem centang semua item untuk semua jamaah berstatus Lunas sekaligus → satu konfirmasi → stok semua item berkurang sesuai bundle.

### 24.8 Return Item

Untuk item yang dikembalikan setelah trip (ID card, kartu penginapan, dll.):
- Admin tandai "Item Dikembalikan" per jamaah
- Stok bertambah kembali
- Kondisi item dicatat: Baik / Rusak / Hilang

### 24.9 Kartu Stok

Untuk setiap item, tersedia Kartu Stok lengkap:

```
KARTU STOK: Koper Besar (L)
─────────────────────────────────────────────────────────────────
Tgl           Keterangan                   Masuk  Keluar  Saldo
─────────────────────────────────────────────────────────────────
01 Jan 2025   Saldo Awal                               —      0
15 Jan 2025   Terima — Vendor Koper ABC       80       —     80
10 Feb 2025   Distribusi — Umroh Feb 2026      —      50     30
20 Feb 2025   Terima — Vendor Koper ABC       40       —     70
─────────────────────────────────────────────────────────────────
HPP Rata-rata: Rp 450.000/unit | Nilai Stok: Rp 31.500.000
```

### 24.10 Laporan Persediaan

- **Laporan Stok Saat Ini**: semua item, saldo, nilai stok, item di bawah minimum
- **Laporan Mutasi per Periode**: semua pergerakan masuk/keluar
- **Laporan Distribusi per Paket**: siapa dapat apa, lengkap atau belum
- **Valuasi Stok Total**: untuk keperluan neraca keuangan
- **HPP Perlengkapan per Trip**: total biaya perlengkapan yang sudah didistribusikan

### 24.11 Integrasi dengan P&L Trip

Saat distribusi perlengkapan selesai untuk satu trip, sistem otomatis menghitung dan mencatat HPP perlengkapan ke laporan P&L trip:

```
Total item terdistribusi × HPP rata-rata masing-masing item
= Biaya Perlengkapan Trip
→ Masuk ke komponen Pengeluaran Operasional di P&L
```

Ini membuat laporan P&L trip menjadi lebih akurat — biaya perlengkapan masuk secara riil berdasarkan distribusi aktual, bukan estimasi.

---

## 25. Modul 11 — Penggajian (Payroll)

### 25.1 Deskripsi

Mengelola penggajian karyawan tetap travel dan honor muthawwif/freelance per trip. Fokus pada kebutuhan PPIU skala kecil-menengah yang selama ini menggaji manual tanpa pencatatan yang rapi.

### 25.2 Master Data Karyawan

| Data | Detail |
|------|--------|
| Identitas | Nama, NIK, nomor HP, alamat |
| Jabatan | Admin, CS, Marketing, Muthawwif, Supir, dll. |
| Tipe | Karyawan Tetap / Kontrak / Freelance per Trip |
| Tanggal bergabung | Untuk perhitungan masa kerja |
| Rekening gaji | Bank, nomor rekening, nama pemilik |
| NPWP | Untuk keperluan PPh 21 |
| Status PTKP | TK/0, K/0, K/1, K/2, K/3 |

### 25.3 Komponen Gaji

**Pendapatan Tetap:**
- Gaji pokok
- Tunjangan transport, makan, komunikasi, jabatan

**Pendapatan Variabel:**
- Bonus kehadiran
- Lembur (jam × tarif per jam)
- Bonus performa (input manual)
- Insentif trip (untuk karyawan yang handle trip tertentu)

**Potongan:**
- BPJS Ketenagakerjaan — iuran karyawan 2%
- BPJS Kesehatan — iuran karyawan 1%
- PPh 21 (dihitung otomatis berdasarkan PTKP, metode gross/netto)
- Cicilan kasbon / pinjaman
- Potongan lain-lain (manual)

Iuran **perusahaan** (JKK, JKM, JHT 3.7%, BPJS Kesehatan 4%) juga dihitung dan dilaporkan terpisah (tidak dipotong dari gaji karyawan, tapi menjadi beban travel).

### 25.4 Proses Penggajian Bulanan

```
Buka Periode Gaji (misal: Januari 2025)
  → Sistem generate slip gaji semua karyawan aktif (draft)
  → Admin input variabel bulan ini per karyawan:
      - Kehadiran (jika ada potongan absen)
      - Lembur (jam)
      - Bonus
      - Kasbon yang dicairkan bulan ini
  → Review total gaji bersih semua karyawan
  → Owner approve periode
  → Export Rekap Transfer (Excel): nama, bank, rekening, nominal
  → Admin transfer di internet banking menggunakan rekap
  → Tandai "Sudah Ditransfer" per karyawan (atau sekaligus)
  → Periode dikunci — tidak bisa diubah
```

### 25.5 Contoh Slip Gaji

```
SLIP GAJI — Januari 2025
Karyawan  : Siti Aminah
Jabatan   : Staff Admin
Periode   : 1 – 31 Januari 2025

PENDAPATAN
  Gaji Pokok                    Rp  4.000.000
  Tunjangan Transport           Rp    500.000
  Tunjangan Makan               Rp    400.000
  Bonus Kehadiran               Rp    200.000
  ────────────────────────────────────────────
  Total Pendapatan              Rp  5.100.000

POTONGAN
  BPJS Ketenagakerjaan (2%)     Rp    100.000
  BPJS Kesehatan (1%)           Rp     50.000
  PPh 21 (Metode Netto)         Rp     85.000
  Cicilan Kasbon                Rp    300.000
  ────────────────────────────────────────────
  Total Potongan                Rp    535.000

GAJI BERSIH DITERIMA            Rp  4.565.000
Rekening: BCA 1234567890 a.n. Siti Aminah
```

### 25.6 Honor Muthawwif & Freelance per Trip

Untuk muthawwif atau freelancer yang dibayar per trip:
- Tipe karyawan: Freelance per Trip
- Saat trip selesai, generate honor: pilih karyawan → pilih trip → input nominal
- Bisa tambah: uang saku harian selama di Saudi (jumlah hari × tarif per hari)
- Sistem generate kwitansi honor → admin transfer → tandai lunas
- Honor tercatat sebagai biaya operasional trip → masuk ke P&L trip tersebut

### 25.7 Kasbon & Pinjaman Karyawan

- Admin catat kasbon: nama karyawan, tanggal, nominal, keperluan
- Tentukan cicilan: berapa kali, nominal per bulan
- Sistem otomatis masukkan cicilan ke potongan gaji bulan berikutnya sampai lunas
- Saldo kasbon sisa selalu terlihat di profil karyawan

### 25.8 Laporan Payroll

| Laporan | Keterangan |
|---------|-----------|
| Slip Gaji | PDF per karyawan per bulan — kirim via email |
| Rekap Penggajian Bulanan | Total biaya gaji per bulan per jabatan |
| Laporan PPh 21 | Rekapitulasi pajak per karyawan per tahun (persiapan SPT) |
| Laporan Iuran BPJS | Iuran karyawan + perusahaan — untuk setoran ke BPJS |
| Biaya SDM per Trip | Honor muthawwif & freelance masuk ke P&L trip |

---

## 26. Keputusan & Decisions Log

| # | Pertanyaan | Keputusan |
|---|-----------|-----------|
| 1 | E-kontrak digital? | **Masuk v2 — Phase 3** |
| 2 | Workflow refund & pembatalan? | **Masuk v2 — Phase 3** |
| 3 | Integrasi rekening bank? | **Defer ke v3** — terlalu kompleks, input manual dulu |
| 4 | Modul penggajian? | **Masuk v2 — Phase 4** |
| 5 | Bahasa Inggris? | **Defer** — prioritas Indonesia dulu |

---

## 27. Open Questions yang Tersisa

1. **E-sign legally binding?** Saat ini e-kontrak bersifat administratif. Jika travel butuh kekuatan hukum penuh, perlu integrasi PrivyID/Tanda (~Rp 2.000–5.000/kontrak). Pertimbangkan sebagai add-on berbayar di v3.

2. **Apakah perlu fitur antrian nomor (ticketing) untuk customer service?** Agar jamaah bisa submit pertanyaan/komplain secara formal. Pertimbangkan di v3.

3. **Bagaimana handle jamaah yang ikut umroh lebih dari sekali dalam setahun?** Perlu definisi: apakah komisi agen tetap berlaku untuk repeat customer yang sudah ada di database? Perlu kebijakan per agen.

---

*Dokumen ini adalah PRD hidup — akan diupdate seiring dengan feedback dari user testing dan pengembangan produk.*

*Version: 2.1 — Go Microservices, E-Kontrak, Refund, Inventory, Payroll, Self-Hosted Infra | Last Updated: 2025*

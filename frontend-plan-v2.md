# Frontend Plan — Jamaah.in v2.1
## 12-Modul Admin System — Svelte 5 SPA

---

## 0. Stack & Prinsip

**Stack saat ini (tetap digunakan):** Svelte 5 SPA, Vite, no SvelteKit, ApiService pattern, manual page routing via `currentPage` state di `App.svelte`.

> PRD v2 menyebut SvelteKit + TailwindCSS sebagai target akhir, tapi karena backend v2 belum selesai dan kamu sedang kerja di backend sekarang, kita bangun modul baru **di dalam SPA yang sudah ada** dulu. Migrasi ke SvelteKit bisa dilakukan setelah backend Go microservices siap.

**Design system:**
- Primary blue: `#2563eb` / `#1d4ed8`
- Gold accent: `#f59e0b` / `#d97706`
- Emerald: `#10b981` (logo `.in`)
- Slate neutrals: `#0f172a`, `#1e293b`, `#475569`, `#94a3b8`
- Font: Plus Jakarta Sans (sudah ada di CSS)
- Border radius: 12–16px (card), 8px (badge/chip), 6px (button)
- Shadow: `0 4px 6px -1px rgba(0,0,0,0.07)`

---

## 1. Navigasi & Routing

### 1.1 Penambahan Routes

Tambah page berikut ke `currentPage` state di `App.svelte`:

```js
// Existing
'dashboard' | 'scanner' | 'groups' | 'rooming' | 'manifest' | 'itinerary'
| 'inventory' | 'team' | 'profile' | 'analytics' | 'data-jamaah'

// New — Phase 1 (prioritas)
| 'packages'        // Modul 1: Manajemen Paket & Harga
| 'crm'            // Modul 2: CRM & Pipeline Jamaah
| 'invoices'       // Modul 3: Invoice & Pembayaran
| 'finance'        // Modul 4: Laporan Keuangan & P&L

// New — Phase 2
| 'vendors'        // Modul 5: Vendor & Biaya Ops
| 'agents'         // Modul 6: Komisi Agen
| 'documents'      // Modul 7: Dokumen & Paspor (upgrade dari modul manifest lama)

// New — Phase 3
| 'contracts'      // Modul 8: E-Kontrak Digital
| 'cancellations'  // Modul 9: Pembatalan & Refund
| 'stock'          // Modul 10: Persediaan
| 'payroll'        // Modul 11: Penggajian
```

### 1.2 Sidebar (`Sidebar.svelte`)

Grup navigasi baru:

```
── UTAMA
   Dashboard
   AI Scanner (existing)

── OPERASIONAL
   Paket & Harga          [packages]
   CRM & Jamaah           [crm]
   Invoice & Pembayaran   [invoices]
   Dokumen & Paspor       [documents]

── KEUANGAN
   Laporan Keuangan       [finance]   (Owner/Finance only)
   Vendor & Biaya         [vendors]   (Owner/Finance only)
   Komisi Agen            [agents]    (Owner only)

── ADVANCED (Pro/Business only)
   E-Kontrak              [contracts]
   Pembatalan & Refund    [cancellations]
   Persediaan             [stock]
   Penggajian             [payroll]

── PENGATURAN
   Tim & Organisasi       [team]
   Profil Saya            [profile]
```

Role-based visibility: semua item Keuangan dan Advanced harus dicek dengan `userRole` dari `ApiService.getCurrentUser()`.

---

## 2. Modul 1 — Paket & Harga (`PackagesPage.svelte`)

### 2.1 Layout

```
PackagesPage
├── PackageListPanel (kiri, list semua paket)
│   ├── StatusFilterTabs (All / Draft / Open / Full / Closed / Done)
│   ├── PackageCard (per paket: nama, tanggal, kuota, status badge)
│   └── [+ Buat Paket Baru] button
└── PackageDetailPanel (kanan, slide-in atau separate page)
    ├── PackageHeader (nama, status toggle, publish toggle)
    ├── PackageBasicInfo (tanggal, maskapai, durasi)
    ├── PackageHotels (Makkah + Madinah card)
    ├── PricingTiers (tabel quad/triple/double/single + early bird)
    ├── CostBreakdown (komponen HPP + margin otomatis)
    └── PackageActions (Preview publik, Edit, Hapus)
```

### 2.2 Komponen Kunci

**`PackageCard.svelte`**
```svelte
<!-- Props: package { id, name, departure_date, total_seats, filled_seats, status } -->
<div class="card">
  <StatusBadge {status} />
  <h3>{package.name}</h3>
  <p>{formatDate(package.departure_date)}</p>
  <QuotaBar filled={package.filled_seats} total={package.total_seats} />
</div>
```

**`PricingTiers.svelte`**
Tabel editable dengan 4 baris (Quad/Triple/Double/Single). Setiap sel input nominal IDR dengan format `Rp X.XXX.XXX`. Tambah row "Early Bird" optional dengan date picker expiry.

**`CostBreakdown.svelte`**
List item komponen biaya (tiket, hotel makkah, hotel madinah, visa, bus, muthawwif, perlengkapan, lain-lain). Auto-hitung total HPP dan margin per jamaah. Tampilkan proyeksi profit trip = margin × kuota.

**`PackageForm.svelte`** (untuk create/edit)
Wizard 3 step:
1. Info Dasar (nama, jenis, tanggal, maskapai, hotel)
2. Harga & HPP (pricing tiers + cost breakdown)
3. Review & Publish

### 2.3 API calls yang perlu (`apiDomains/packageApi.js`)
```js
listPackages({ status, page, limit })
getPackage(id)
createPackage(data)
updatePackage(id, data)
deletePackage(id)
togglePublish(id, isPublic)
getPackageStats(id)           // kuota, filled, projected profit
```

---

## 3. Modul 2 — CRM & Pipeline (`CRMPage.svelte`)

### 3.1 Layout

Dua view yang bisa di-switch:

**View A — Kanban Pipeline**
```
CRMPage (view=kanban)
├── PackageFilter (pilih trip / semua)
├── PipelineBoard
│   ├── KanbanColumn x8 (Prospek, Survey, Booking, DP, Cicilan, Lunas, Berangkat, Selesai)
│   │   └── JamaahCard (nama, foto, paket, sisa tagihan, alert paspor)
│   └── drag-n-drop (Svelte `use:draggable` atau library sederhana)
└── [+ Tambah Jamaah] FAB button
```

**View B — Tabel List**
```
CRMPage (view=table)
├── SearchBar + FilterBar (status, paket, tanggal daftar)
├── JamaahTable
│   └── Row: foto | nama | paket | tipe kamar | status | sisa tagihan | aksi
└── Pagination
```

### 3.2 Jamaah Detail Drawer

Saat klik jamaah, slide drawer dari kanan (bukan navigasi halaman baru):

```
JamaahDrawer
├── DrawerHeader (nama + status badge + close button)
├── TabBar: [Profil] [Dokumen] [Invoice] [Histori] [Catatan]
│
├── Tab Profil
│   ├── IdentitySection (NIK, paspor, TTL, alamat, gol. darah)
│   ├── ContactSection (HP/WA, email, kontak darurat)
│   └── TripSection (mahram, sumber lead, histori trip)
│
├── Tab Dokumen
│   └── DocumentChecklist (lihat Modul 7)
│
├── Tab Invoice
│   └── InvoiceSummary + PaymentHistory + [+ Tambah Pembayaran]
│
├── Tab Histori
│   └── ActivityLog (semua perubahan status + catatan)
│
└── Tab Catatan
    └── NoteList + AddNoteForm
```

**Quick Actions bar** (selalu visible di bawah drawer):
- Buka WA → `wa.me/62{phone}?text={template}`
- Generate Invoice PDF
- Ubah Status Pipeline
- Upload Dokumen

### 3.3 `JamaahForm.svelte` (Tambah/Edit Jamaah)

Modal besar dengan 2 cara input:
1. **Manual** — form fields: nama, NIK, paspor, kontak, dll.
2. **Via AI Scanner** — klik "Scan Dokumen", upload KTP/paspor, data ter-populate otomatis, user verifikasi sebelum simpan.

Setelah simpan profil: langsung tawarkan "Pilih paket & buat invoice?" (satu flow).

### 3.4 API calls (`apiDomains/crmApi.js`)
```js
listJamaah({ status, package_id, search, page })
getJamaah(id)
createJamaah(data)
updateJamaah(id, data)
updateJamaahStatus(id, status)
addJamaahNote(id, note)
getJamaahHistory(id)
searchJamaahByNIKorPassport(query)   // detect repeat customer
```

---

## 4. Modul 3 — Invoice & Pembayaran (`InvoicesPage.svelte`)

### 4.1 Layout

```
InvoicesPage
├── SummaryBar (total tagihan aktif, total overdue, kas masuk hari ini)
├── FilterBar (paket, status invoice, tanggal)
├── InvoiceTable
│   └── Row: nomor invoice | nama jamaah | total | terbayar | sisa | status | aksi
└── InvoiceDetail (slide drawer atau modal)
```

### 4.2 `InvoiceDetail.svelte`

```
InvoiceDetail
├── InvoiceHeader (nomor, tanggal terbit, jatuh tempo)
├── JamaahInfo (nama, paket, tipe kamar)
├── BillingSection
│   ├── Harga paket (snapshot)
│   ├── Diskon
│   ├── Biaya tambahan
│   └── Total Tagihan
├── PaymentSchemeCard
│   └── (DP+Pelunasan / Cicilan Bebas / Lunas)
├── PaymentHistoryTable
│   └── Row: tanggal | nominal | metode | bukti | catatan | status
├── PaymentProgress (progress bar: terbayar / total)
└── ActionBar
    ├── [+ Rekam Pembayaran]
    ├── [Generate PDF Invoice]
    └── [Kirim WA]
```

### 4.3 `RecordPaymentModal.svelte`

Form input pembayaran:
- Tanggal bayar (date picker)
- Nominal (input IDR)
- Metode (Transfer Bank / QRIS / Tunai / Cek / Giro)
- Bank tujuan + nomor referensi
- Upload bukti bayar (drag-drop atau file picker)
- Catatan opsional

Setelah simpan: auto-refresh invoice, tampilkan konfirmasi "Generate kwitansi?" → klik → download PDF.

### 4.4 `CreateInvoiceForm.svelte`

Wizard 3 step:
1. Pilih Jamaah (search dari CRM atau buat baru)
2. Konfigurasi: harga snapshot, diskon, biaya tambahan, pilih skema pembayaran
3. Preview Invoice → Simpan & Kirim

### 4.5 API calls (`apiDomains/invoiceApi.js`)
```js
listInvoices({ package_id, status, overdue, page })
getInvoice(id)
createInvoice(data)
updateInvoice(id, data)
recordPayment(invoice_id, payment_data)
generateInvoicePDF(id)              // returns blob URL
generateReceiptPDF(payment_id)      // per-payment receipt
getOverdueSummary()                 // dashboard widget data
getDailyCashReport(date)
```

---

## 5. Modul 4 — Laporan Keuangan (`FinancePage.svelte`)

### 5.1 Layout

```
FinancePage
├── PeriodSelector (bulan ini / tahun ini / custom range)
├── SummaryCards (4 kartu)
│   ├── Total Pemasukan
│   ├── Total Pengeluaran Vendor
│   ├── Gross Profit
│   └── Total Piutang Aktif
├── TabBar: [P&L per Trip] [Piutang Aging] [Arus Kas] [Kas Harian]
│
├── Tab P&L per Trip
│   ├── TripSelector (dropdown paket)
│   └── PLTable (pendapatan, pengeluaran detail, laba kotor, margin %)
│       + Comparison: Proyeksi vs Aktual
│
├── Tab Piutang Aging
│   └── AgingTable (0-30 / 31-60 / 61-90 / >90 hari)
│       dengan drill-down per jamaah
│
├── Tab Arus Kas
│   └── CashFlowChart (proyeksi kas masuk dari cicilan + grafik 6 bulan)
│
└── Tab Kas Harian
    └── DailyCashTable (dikelompok per metode bayar, per rekening)
```

### 5.2 Komponen Chart

Gunakan library ringan: **Chart.js** via `chart.js/auto` (sudah mungkin ada, cek `package.json`). Kalau belum ada, tambahkan. Target chart:
- Line chart: pendapatan 6 bulan terakhir
- Bar chart: P&L per trip (pendapatan vs pengeluaran)
- Donut chart: komposisi pembayaran per metode

### 5.3 Export

Semua tab punya tombol "Export Excel" yang memanggil endpoint `/finance/export?type=...` dan trigger download.

---

## 6. Modul 5 — Vendor & Biaya Ops (`VendorsPage.svelte`)

### 6.1 Layout

```
VendorsPage
├── TabBar: [Master Vendor] [Tagihan per Trip]
│
├── Tab Master Vendor
│   ├── VendorList (tabel: nama, tipe, kontak, rekening)
│   └── VendorForm (modal: nama, tipe, NPWP, alamat, kontak, rekening)
│
└── Tab Tagihan per Trip
    ├── TripFilter (pilih paket)
    ├── VendorBillList (tagihan vendor untuk trip tersebut)
    │   └── Row: vendor | deskripsi | nominal | jatuh tempo | status hutang
    ├── [+ Tambah Tagihan Vendor] button
    └── VendorBillDetail (drawer: histori bayar, sisa hutang)
```

---

## 7. Modul 6 — Komisi Agen (`AgentsPage.svelte`)

### 7.1 Layout

```
AgentsPage
├── TabBar: [Master Agen] [Komisi] [Rekap Pembayaran]
│
├── Tab Master Agen
│   ├── AgentList (tabel + search)
│   └── AgentForm (modal)
│
├── Tab Komisi
│   ├── PackageFilter
│   └── CommissionTable
│       └── Row: agen | jamaah yang direferral | nominal komisi | status | aksi
│
└── Tab Rekap Pembayaran
    ├── PeriodFilter
    └── CommissionPaymentList
        └── Row: agen | total komisi | dibayar | belum dibayar | [Catat Pembayaran]
```

---

## 8. Modul 7 — Dokumen & Paspor (`DocumentsPage.svelte`)

Upgrade dari halaman manifest lama. Fokus pada checklist per jamaah per trip.

### 8.1 Layout

```
DocumentsPage
├── TripSelector (pilih paket/trip)
├── DocumentSummaryBar (lengkap X / kurang Y / paspor expiring Z)
├── JamaahDocList
│   └── JamaahDocRow: nama | checklist mini (ikon per dokumen) | status overall | aksi
└── JamaahDocDetail (drawer)
    ├── ChecklistSection (per dokumen: status + upload + tanggal terima)
    ├── PassportAlert (warning kuning/merah jika expired < 90/30 hari)
    └── DocumentPreview (thumbnail klik untuk fullscreen)
```

**`DocumentChecklist.svelte`** (reusable, dipakai juga di JamaahDrawer Tab Dokumen):
```svelte
<!-- Status per item: belum | diterima | diproses | selesai -->
<!-- Badge + upload button + date stamp per dokumen -->
```

---

## 9. Dashboard Upgrade (`Dashboard.svelte`)

Dashboard perlu diupgrade jadi **role-aware**:

### Owner Dashboard
```
Dashboard (role=owner)
├── SummaryCards (Pemasukan bulan ini, Piutang aktif, Hutang vendor, Gross Profit)
├── AlertsPanel (jamaah overdue hari ini, paspor expiring, dokumen kurang)
├── RevenueChart (line chart 6 bulan)
├── ActiveTripsGrid (card per trip aktif: progress pembayaran jamaah)
└── QuickActions: [Buat Paket] [Tambah Jamaah] [Rekam Pembayaran]
```

### Admin/CS Dashboard
```
Dashboard (role=admin|cs)
├── FollowUpList (jamaah yang perlu dihubungi: overdue, dokumen kurang)
├── IncomingRegistrations (dari link self-service)
├── TripCountdown (H- keberangkatan trip terdekat)
└── QuickActions: [Tambah Jamaah] [Buat Invoice] [Rekam Pembayaran]
```

---

## 10. Komponen Shared Baru

Semua komponen ini dipakai lintas modul, taruh di `src/lib/components/`:

| Komponen | Deskripsi |
|----------|-----------|
| `StatusBadge.svelte` | Badge dengan warna per status (Draft/Open/Full dll) |
| `IDRInput.svelte` | Input nominal IDR dengan auto-format `Rp X.XXX.XXX` |
| `DatePicker.svelte` | Wrapper input date, format Indonesia |
| `DataTable.svelte` | Tabel generik: sortable, pagination, loading skeleton |
| `SlideDrawer.svelte` | Drawer panel dari kanan, dengan backdrop + close |
| `ConfirmModal.svelte` | Dialog konfirmasi hapus/aksi destructive |
| `FileUploadZone.svelte` | Drag-drop upload, preview thumbnail, progress bar |
| `EmptyState.svelte` | Ilustrasi + pesan untuk list kosong |
| `LoadingSkeleton.svelte` | Skeleton loading untuk card dan tabel |
| `ToastNotification.svelte` | Toast sukses/error/info (global via Svelte store) |
| `QuotaBar.svelte` | Progress bar untuk kuota jamaah (filled/total) |
| `CurrencyDisplay.svelte` | Format IDR dengan warna (hijau=lunas, merah=overdue) |

### `toast.js` — Global Toast Store
```js
// src/lib/stores/toast.js
import { writable } from 'svelte/store';
export const toasts = writable([]);
export function addToast(message, type = 'success', duration = 3000) { ... }
```

---

## 11. API Domain Modules Baru

Buat file baru di `src/lib/services/apiDomains/`:

```
packageApi.js         // Modul 1
crmApi.js             // Modul 2
invoiceApi.js         // Modul 3
financeApi.js         // Modul 4
vendorApi.js          // Modul 5
agentApi.js           // Modul 6
documentApi.js        // Modul 7 (berbeda dari documentExcelApi.js yang lama)
contractApi.js        // Modul 8
cancellationApi.js    // Modul 9
stockApi.js           // Modul 10
payrollApi.js         // Modul 11
```

Register ke `ApiService` di `api.js` dengan pattern yang sama seperti existing domains.

---

## 12. State Management

Tidak perlu store global yang besar. Gunakan pola:

1. **Page-local state** (`let` di dalam page component) untuk filter, selected item, drawer open/close.
2. **ApiService + TTL cache** untuk data dari server (sudah ada pattern-nya).
3. **Svelte store** hanya untuk:
   - `currentUser` (auth info + role)
   - `toasts` (notifikasi global)
   - `activePackage` (trip yang sedang dipilih — dipakai lintas modul CRM, Invoice, Dokumen)

```js
// src/lib/stores/app.js
import { writable, derived } from 'svelte/store';

export const currentUser = writable(null);
export const activePackageId = writable(null);
export const toasts = writable([]);
```

---

## 13. Permission Guard Pattern

Setiap page yang role-restricted pakai wrapper:

```svelte
<!-- Di dalam page component -->
<script>
  import { currentUser } from '$lib/stores/app.js';
  import AccessDenied from '$lib/components/AccessDenied.svelte';

  $: canAccess = $currentUser?.role === 'owner' || $currentUser?.role === 'finance';
</script>

{#if canAccess}
  <!-- page content -->
{:else}
  <AccessDenied />
{/if}
```

Untuk fitur Pro/Business: gunakan `ProGateScreen.svelte` yang sudah ada.

---

## 14. Urutan Implementasi (Frontend)

Ikuti fase backend:

### Phase 1 — Koordinasi dengan Backend (sekarang)
1. Buat komponen shared dulu: `IDRInput`, `DataTable`, `SlideDrawer`, `ToastNotification`, `StatusBadge`
2. Setup `src/lib/stores/app.js`
3. Update `Sidebar.svelte` dengan struktur navigasi baru
4. Dashboard upgrade: tambah summary cards dan alert panel (data dari endpoint yang sudah ada)

### Phase 2 — Saat Backend Siap
5. `PackagesPage.svelte` + `packageApi.js`
6. `CRMPage.svelte` + `crmApi.js` + `JamaahDrawer.svelte`
7. `InvoicesPage.svelte` + `invoiceApi.js` + `RecordPaymentModal.svelte`
8. `FinancePage.svelte` + `financeApi.js`

### Phase 3 — Operasional
9. `VendorsPage.svelte` + `vendorApi.js`
10. `AgentsPage.svelte` + `agentApi.js`
11. `DocumentsPage.svelte` + `documentApi.js`

### Phase 4 — Advanced
12. Modul lanjutan (contracts, cancellations, stock, payroll)

---

## 15. Catatan Teknis Penting

- **Drawer vs Page**: Untuk detail jamaah/invoice/vendor, gunakan `SlideDrawer` bukan navigasi halaman baru. Ini lebih cepat dan mempertahankan konteks list di belakangnya.
- **PDF download**: Backend generate PDF dan return blob atau URL. Frontend tinggal `window.open(url)` atau trigger download via `<a href=blob download>`.
- **WA integration**: Tidak ada API blast. Semua WA pakai `window.open('https://wa.me/62{phone}?text={encodeURIComponent(template)}')`.
- **IDR formatting**: Semua tampilan nominal menggunakan `Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 })`.
- **Optimistic UI**: Untuk update status pipeline (drag kanban), update UI dulu, rollback jika API gagal.
- **Image preview**: Untuk dokumen jamaah (KTP, paspor foto), gunakan `object-URL` dari blob — jangan expose signed URL di console.

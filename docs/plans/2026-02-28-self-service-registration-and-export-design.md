# Design: Self-Service Jamaah Onboarding & Multi-Format Export

> **Status:** Approved
> **Date:** 2026-02-28
> **Author:** Claude (Brainstorming Session)

---

## Overview

Two new features to reduce travel agency workflow:

1. **Self-Service Jamaah Onboarding (Drop-Link)** - Allow jamaah to self-register via shared link
2. **Multi-Format Manifest Export** - Export data to any Excel template format

---

## Feature 1: Self-Service Jamaah Onboarding

### Problem
Travel agency staff must manually collect and upload all jamaah documents (batch upload max 50 files). This is time-consuming and error-prone.

### Solution
Generate a registration link per group that can be shared via WhatsApp. Jamaah upload their own documents directly.

### User Flow

```
TRAVEL AGENCY (Admin):
1. Buka halaman Group → Klik "Generate Registration Link"
2. Set expiry date (default: 30 hari)
3. Copy link: jamaah.in/reg/{token}
4. Share ke WhatsApp group jamaah

JAMAAH:
1. Buka link di HP
2. Input No HP (wajib) - untuk auto-register di database
3. Upload KTP (wajib) → OCR otomatis via Gemini
4. Upload Paspor (opsional) - travel bisa input nanti
5. Upload Visa (opsional) - travel bisa input nanti
6. Klik "Kirim Data"
7. Lihat konfirmasi "Data berhasil dikirim, menunggu review"

TRAVEL AGENCY (Review):
1. Buka Group → Tab "Pending Review"
2. Lihat list jamaah dengan status Pending
3. Review data → Approve, Edit, atau Reject
4. Setelah approve → masuk ke member list grup
```

### Data Model

```python
# Tabel baru: registration_links
class RegistrationLink:
    id: int (PK)
    group_id: int (FK to groups)
    token: str (unique, URL-safe, 32 chars)
    expires_at: datetime
    created_by: int (FK to users)
    created_at: datetime
    is_active: bool (default: True)

# Tabel baru: pending_members
class PendingMember:
    id: int (PK)
    group_id: int (FK to groups)
    phone_number: str (wajib)
    status: str (pending/approved/rejected)
    submitted_at: datetime
    reviewed_at: datetime (nullable)
    reviewed_by: int (FK to users, nullable)
    
    # 32 kolom data hasil OCR (sama seperti GroupMember)
    title: str
    nama: str
    nama_ayah: str
    jenis_identitas: str
    no_identitas: str
    # ... 27 more columns
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/groups/{id}/registration-link` | JWT | Generate registration link |
| GET | `/groups/{id}/registration-link` | JWT | Get link info + QR code |
| DELETE | `/groups/{id}/registration-link` | JWT | Revoke/deactivate link |
| GET | `/public/register/{token}` | None | Get registration page info |
| POST | `/public/register/{token}` | None | Jamaah submit data |
| GET | `/groups/{id}/pending` | JWT | List pending members |
| POST | `/groups/{id}/pending/{mid}/approve` | JWT | Approve pending member |
| POST | `/groups/{id}/pending/{mid}/reject` | JWT | Reject pending member |
| PUT | `/groups/{id}/pending/{mid}` | JWT | Edit pending member data |

### Frontend Components

1. **RegistrationLinkModal.svelte** - Modal untuk generate/manage link
2. **PublicRegistrationPage.svelte** - Halaman publik untuk jamaah
3. **PendingMembersTable.svelte** - Table review untuk admin

### Business Rules

- Link expiry: Default 30 hari, max 90 hari
- Anti-duplicate: No HP yang sama tidak bisa submit 2x ke grup yang sama
- Rate limiting: Max 10 submission per IP per jam (anti-spam)
- Pro feature: Only Pro users can generate registration links

---

## Feature 2: Multi-Format Manifest Export

### Problem
Travel agencies need to export data in various formats:
- Siskopatuh (current, 15 columns)
- Nusuk platform format
- Airline manifests (Saudia, Garuda, etc.)
- Custom formats from other systems

### Solution
Allow users to upload any Excel template, auto-detect column headers, and map to 32-column data.

### User Flow

```
TRAVEL AGENCY:
1. Buka Group → Klik "Export" → "Custom Template"
2. Upload Excel template (format apapun)
3. System auto-detect header row → show mapping preview:

   Template Column    →    Jamaah.in Field
   ─────────────────────────────────────────
   "Nama Lengkap"     →    nama
   "No Passport"      →    no_paspor
   "Tanggal Lahir"    →    tanggal_lahir
   "Alamat"           →    alamat
   ...                →    ...

4. User adjust mapping jika perlu (dropdown per column)
5. Klik "Export" → Download Excel dengan format template
6. Opsi: "Save as Template" untuk reuse nanti
```

### Data Model

```python
# Tabel baru: export_templates
class ExportTemplate:
    id: int (PK)
    user_id: int (FK to users)
    org_id: int (FK to organizations, nullable)
    name: str (e.g., "Saudia Manifest", "Nusuk Format")
    file_path: str (path ke uploaded template)
    column_mapping: JSONB
    # Contoh: {"A": "nama", "B": "no_paspor", "C": "tanggal_lahir"}
    header_row: int (default: 1)
    data_start_row: int (default: 2)
    created_at: datetime
    is_default: bool (default: False)
```

### API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/export-templates/upload` | JWT | Upload template + auto-detect |
| GET | `/export-templates` | JWT | List saved templates |
| GET | `/export-templates/{id}` | JWT | Get template detail |
| PUT | `/export-templates/{id}` | JWT | Update template mapping |
| DELETE | `/export-templates/{id}` | JWT | Delete template |
| POST | `/groups/{id}/export-custom` | JWT | Export with template |

### Auto-Mapping Logic

```python
HEADER_MAPPINGS = {
    # Indonesian variations
    "nama": "nama",
    "nama lengkap": "nama",
    "nama jamaah": "nama",
    "no. identitas": "no_identitas",
    "nik": "no_identitas",
    "no ktp": "no_identitas",
    "no paspor": "no_paspor",
    "nomor paspor": "no_paspor",
    "passport no": "no_paspor",
    "no passport": "no_paspor",
    "tanggal lahir": "tanggal_lahir",
    "tgl lahir": "tanggal_lahir",
    "dob": "tanggal_lahir",
    "date of birth": "tanggal_lahir",
    "tempat lahir": "tempat_lahir",
    "alamat": "alamat",
    "alamat lengkap": "alamat",
    "provinsi": "provinsi",
    "kabupaten": "kabupaten",
    "kecamatan": "kecamatan",
    "kelurahan": "kelurahan",
    "no telepon": "no_telepon",
    "no hp": "no_hp",
    "phone": "no_hp",
    "jenis kelamin": "jenis_kelamin",
    "gender": "jenis_kelamin",
    "jk": "jenis_kelamin",
    # ... more mappings
}

def auto_detect_mapping(headers: list[str]) -> dict:
    """Auto-detect column mapping from header names."""
    mapping = {}
    for col_idx, header in enumerate(headers):
        header_lower = header.lower().strip()
        if header_lower in HEADER_MAPPINGS:
            mapping[col_idx] = HEADER_MAPPINGS[header_lower]
    return mapping
```

### Frontend Components

1. **ExportTemplateModal.svelte** - Modal untuk upload & mapping
2. **ColumnMappingEditor.svelte** - UI untuk adjust mapping
3. **TemplateLibrary.svelte** - List saved templates

---

## Implementation Priority

### Phase 1: Self-Service Registration (High Priority)
1. Backend: RegistrationLink model + endpoints
2. Backend: PendingMember model + endpoints
3. Frontend: PublicRegistrationPage
4. Frontend: RegistrationLinkModal
5. Frontend: PendingMembersTable

### Phase 2: Multi-Format Export (Medium Priority)
1. Backend: ExportTemplate model + endpoints
2. Backend: Auto-mapping logic
3. Backend: Export with template logic
4. Frontend: ExportTemplateModal
5. Frontend: ColumnMappingEditor

---

## Success Metrics

### Self-Service Registration
- % of jamaah who self-register vs manual entry
- Time saved per jamaah registration
- Travel agency satisfaction score

### Multi-Format Export
- Number of custom templates created
- Time saved per export
- Error rate in exported files

---

## Open Questions

1. **WhatsApp Integration:** Should we send confirmation to jamaah via WhatsApp after they submit?
2. **Bulk Approval:** Should admins be able to approve multiple pending members at once?
3. **Template Sharing:** Should templates be shareable within organization (team feature)?

---

*Design document generated from brainstorming session - 28 February 2026*

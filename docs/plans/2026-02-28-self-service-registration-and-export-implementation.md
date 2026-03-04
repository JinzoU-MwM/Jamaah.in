# Self-Service Registration & Multi-Format Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add self-service jamaah registration via shared links and custom Excel template export.

**Architecture:** 
- New public registration page accessible via unique token URLs
- Pending members table for admin review before approval
- Template upload with auto-mapping for flexible Excel exports

**Tech Stack:** FastAPI, SQLAlchemy, Svelte 5, openpyxl, Gemini OCR API

---

## Phase 1: Self-Service Registration Backend

### Task 1.1: Create RegistrationLink Model

**Files:**
- Create: `backend/app/models/registration.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the model**

```python
# backend/app/models/registration.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base
import secrets

class RegistrationLink(Base):
    __tablename__ = "registration_links"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(64), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    group = relationship("Group", back_populates="registration_links")
    creator = relationship("User")

    @staticmethod
    def generate_token():
        return secrets.token_urlsafe(32)
```

**Step 2: Export from __init__.py**

Add to `backend/app/models/__init__.py`:
```python
from backend.app.models.registration import RegistrationLink
```

**Step 3: Update Group model relationship**

Add to `backend/app/models/group.py` in the Group class:
```python
registration_links = relationship("RegistrationLink", back_populates="group", cascade="all, delete-orphan")
```

**Step 4: Commit**

```bash
git add backend/app/models/registration.py backend/app/models/__init__.py backend/app/models/group.py
git commit -m "feat: add RegistrationLink model for self-service registration"
```

---

### Task 1.2: Create PendingMember Model

**Files:**
- Create: `backend/app/models/pending_member.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the model**

```python
# backend/app/models/pending_member.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class PendingMember(Base):
    __tablename__ = "pending_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 32 columns matching GroupMember (simplified for plan)
    title = Column(String(10))
    nama = Column(String(100))
    nama_ayah = Column(String(100))
    jenis_identitas = Column(String(20))
    no_identitas = Column(String(20))
    nama_paspor = Column(String(100))
    no_paspor = Column(String(20))
    tanggal_paspor = Column(String(20))
    kota_paspor = Column(String(50))
    tempat_lahir = Column(String(50))
    tanggal_lahir = Column(String(20))
    alamat = Column(Text)
    provinsi = Column(String(50))
    kabupaten = Column(String(50))
    kecamatan = Column(String(50))
    kelurahan = Column(String(50))
    no_telepon = Column(String(20))
    no_hp = Column(String(20))
    kewarganegaraan = Column(String(10))
    status_pernikahan = Column(String(20))
    pendidikan = Column(String(30))
    pekerjaan = Column(String(50))
    provider_visa = Column(String(50))
    no_visa = Column(String(30))
    tanggal_visa = Column(String(20))
    tanggal_visa_akhir = Column(String(20))
    asuransi = Column(String(50))
    no_polis = Column(String(30))
    tanggal_input_polis = Column(String(20))
    tanggal_awal_polis = Column(String(20))
    tanggal_akhir_polis = Column(String(20))
    no_bpjs = Column(String(20))

    # Relationships
    group = relationship("Group", back_populates="pending_members")
    reviewer = relationship("User")
```

**Step 2: Export from __init__.py**

Add to `backend/app/models/__init__.py`:
```python
from backend.app.models.pending_member import PendingMember
```

**Step 3: Update Group model**

Add to Group class in `backend/app/models/group.py`:
```python
pending_members = relationship("PendingMember", back_populates="group", cascade="all, delete-orphan")
```

**Step 4: Commit**

```bash
git add backend/app/models/pending_member.py backend/app/models/__init__.py backend/app/models/group.py
git commit -m "feat: add PendingMember model for registration review"
```

---

### Task 1.3: Create Alembic Migration

**Files:**
- Create: Migration file (auto-generated)

**Step 1: Generate migration**

```bash
cd backend
alembic revision --autogenerate -m "add registration_link and pending_member tables"
```

**Step 2: Review migration file**

Check the generated file in `backend/alembic/versions/` for correctness.

**Step 3: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: add migration for registration tables"
```

---

### Task 1.4: Create Registration Router

**Files:**
- Create: `backend/app/routers/registration_router.py`
- Modify: `backend/main.py`

**Step 1: Write the router**

```python
# backend/app/routers/registration_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.group import Group
from backend.app.models.registration import RegistrationLink
from backend.app.models.pending_member import PendingMember
from backend.app.services.gemini_ocr import extract_document_data
from pydantic import BaseModel

router = APIRouter(prefix="/registration", tags=["registration"])

# --- Schemas ---
class GenerateLinkRequest(BaseModel):
    group_id: int
    expires_in_days: int = 30

class GenerateLinkResponse(BaseModel):
    link: str
    token: str
    expires_at: str

class PublicRegistrationRequest(BaseModel):
    phone_number: str
    # Files will be uploaded separately

# --- Admin Endpoints ---
@router.post("/generate", response_model=GenerateLinkResponse)
def generate_link(
    req: GenerateLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a registration link for a group."""
    group = db.query(Group).filter(Group.id == req.group_id).first()
    if not group:
        raise HTTPException(404, "Group not found")
    
    # Check ownership
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    # Generate token
    token = RegistrationLink.generate_token()
    expires_at = datetime.utcnow() + timedelta(days=req.expires_in_days)
    
    link = RegistrationLink(
        group_id=req.group_id,
        token=token,
        expires_at=expires_at,
        created_by=current_user.id,
    )
    db.add(link)
    db.commit()
    
    return GenerateLinkResponse(
        link=f"https://jamaah.in/reg/{token}",
        token=token,
        expires_at=expires_at.isoformat(),
    )

@router.get("/link/{group_id}")
def get_link_info(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get registration link info for a group."""
    link = db.query(RegistrationLink).filter(
        RegistrationLink.group_id == group_id,
        RegistrationLink.is_active == True,
    ).first()
    
    if not link:
        return {"active": False}
    
    return {
        "active": True,
        "token": link.token,
        "link": f"https://jamaah.in/reg/{link.token}",
        "expires_at": link.expires_at.isoformat(),
        "is_expired": datetime.utcnow() > link.expires_at,
    }

@router.delete("/link/{group_id}")
def revoke_link(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke registration link."""
    link = db.query(RegistrationLink).filter(
        RegistrationLink.group_id == group_id,
        RegistrationLink.is_active == True,
    ).first()
    
    if link:
        link.is_active = False
        db.commit()
    
    return {"success": True}

# --- Public Endpoints ---
@router.get("/public/{token}")
def get_registration_info(token: str, db: Session = Depends(get_db)):
    """Get registration page info."""
    link = db.query(RegistrationLink).filter(
        RegistrationLink.token == token,
        RegistrationLink.is_active == True,
    ).first()
    
    if not link:
        raise HTTPException(404, "Registration link not found")
    
    if datetime.utcnow() > link.expires_at:
        raise HTTPException(410, "Registration link has expired")
    
    group = db.query(Group).filter(Group.id == link.group_id).first()
    
    return {
        "group_name": group.name,
        "group_id": group.id,
        "expires_at": link.expires_at.isoformat(),
    }

@router.post("/public/{token}")
async def submit_registration(
    token: str,
    phone_number: str,
    db: Session = Depends(get_db),
):
    """Submit registration data."""
    link = db.query(RegistrationLink).filter(
        RegistrationLink.token == token,
        RegistrationLink.is_active == True,
    ).first()
    
    if not link:
        raise HTTPException(404, "Registration link not found")
    
    if datetime.utcnow() > link.expires_at:
        raise HTTPException(410, "Registration link has expired")
    
    # Check for duplicate phone number
    existing = db.query(PendingMember).filter(
        PendingMember.group_id == link.group_id,
        PendingMember.phone_number == phone_number,
    ).first()
    
    if existing:
        raise HTTPException(400, "This phone number has already registered")
    
    # Create pending member (simplified - actual OCR will be added)
    pending = PendingMember(
        group_id=link.group_id,
        phone_number=phone_number,
        status="pending",
    )
    db.add(pending)
    db.commit()
    
    return {"success": True, "message": "Data berhasil dikirim, menunggu review"}
```

**Step 2: Register router in main.py**

Add to `backend/main.py`:
```python
from backend.app.routers.registration_router import router as registration_router
app.include_router(registration_router)
```

**Step 3: Commit**

```bash
git add backend/app/routers/registration_router.py backend/main.py
git commit -m "feat: add registration router with generate/submit endpoints"
```

---

### Task 1.5: Add Pending Members Review Endpoints

**Files:**
- Modify: `backend/app/routers/registration_router.py`

**Step 1: Add review endpoints**

Add to `backend/app/routers/registration_router.py`:

```python
@router.get("/pending/{group_id}")
def list_pending(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending members for review."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group or group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    pending = db.query(PendingMember).filter(
        PendingMember.group_id == group_id,
        PendingMember.status == "pending",
    ).all()
    
    return {"pending": [
        {
            "id": p.id,
            "phone_number": p.phone_number,
            "submitted_at": p.submitted_at.isoformat(),
            "nama": p.nama,
            "no_identitas": p.no_identitas,
            "no_paspor": p.no_paspor,
        }
        for p in pending
    ]}

@router.post("/pending/{pending_id}/approve")
def approve_pending(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending member."""
    pending = db.query(PendingMember).filter(PendingMember.id == pending_id).first()
    if not pending:
        raise HTTPException(404, "Pending member not found")
    
    group = db.query(Group).filter(Group.id == pending.group_id).first()
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    # Create GroupMember from PendingMember
    from backend.app.models.group import GroupMember
    member = GroupMember(
        group_id=pending.group_id,
        title=pending.title,
        nama=pending.nama,
        nama_ayah=pending.nama_ayah,
        jenis_identitas=pending.jenis_identitas,
        no_identitas=pending.no_identitas,
        nama_paspor=pending.nama_paspor,
        no_paspor=pending.no_paspor,
        tanggal_paspor=pending.tanggal_paspor,
        kota_paspor=pending.kota_paspor,
        tempat_lahir=pending.tempat_lahir,
        tanggal_lahir=pending.tanggal_lahir,
        alamat=pending.alamat,
        provinsi=pending.provinsi,
        kabupaten=pending.kabupaten,
        kecamatan=pending.kecamatan,
        kelurahan=pending.kelurahan,
        no_telepon=pending.no_telepon or pending.phone_number,
        no_hp=pending.no_hp,
        kewarganegaraan=pending.kewarganegaraan,
        status_pernikahan=pending.status_pernikahan,
        pendidikan=pending.pendidikan,
        pekerjaan=pending.pekerjaan,
        provider_visa=pending.provider_visa,
        no_visa=pending.no_visa,
        tanggal_visa=pending.tanggal_visa,
        tanggal_visa_akhir=pending.tanggal_visa_akhir,
        asuransi=pending.asuransi,
        no_polis=pending.no_polis,
        tanggal_input_polis=pending.tanggal_input_polis,
        tanggal_awal_polis=pending.tanggal_awal_polis,
        tanggal_akhir_polis=pending.tanggal_akhir_polis,
        no_bpjs=pending.no_bpjs,
    )
    db.add(member)
    
    # Update pending status
    pending.status = "approved"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = current_user.id
    
    db.commit()
    
    return {"success": True, "member_id": member.id}

@router.post("/pending/{pending_id}/reject")
def reject_pending(
    pending_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending member."""
    pending = db.query(PendingMember).filter(PendingMember.id == pending_id).first()
    if not pending:
        raise HTTPException(404, "Pending member not found")
    
    group = db.query(Group).filter(Group.id == pending.group_id).first()
    if group.user_id != current_user.id:
        raise HTTPException(403, "Not authorized")
    
    pending.status = "rejected"
    pending.reviewed_at = datetime.utcnow()
    pending.reviewed_by = current_user.id
    db.commit()
    
    return {"success": True}
```

**Step 2: Commit**

```bash
git add backend/app/routers/registration_router.py
git commit -m "feat: add pending member review endpoints (approve/reject)"
```

---

## Phase 2: Self-Service Registration Frontend

### Task 2.1: Create PublicRegistrationPage Component

**Files:**
- Create: `frontend-svelte/src/lib/pages/PublicRegistrationPage.svelte`

**Step 1: Write the component**

```svelte
<script>
  import { onMount } from "svelte";
  import { Camera, Upload, Check, Loader2, AlertCircle } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let { token } = $props();

  let loading = $state(true);
  let error = $state("");
  let groupInfo = $state(null);
  
  let phone = $state("");
  let files = $state([]);
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
    if (!phone || files.length === 0) return;
    
    submitting = true;
    try {
      // Upload files and submit
      const formData = new FormData();
      formData.append("phone_number", phone);
      files.forEach((f) => formData.append("files", f));
      
      await ApiService.submitRegistration(token, formData);
      submitted = true;
    } catch (e) {
      error = e.message || "Gagal mengirim data";
    } finally {
      submitting = false;
    }
  }

  function handleFileChange(e) {
    files = Array.from(e.target.files);
  }
</script>

<div class="registration-page">
  {#if loading}
    <div class="loading">
      <Loader2 class="w-8 h-8 animate-spin" />
      <p>Memuat...</p>
    </div>
  {:else if error}
    <div class="error">
      <AlertCircle class="w-12 h-12 text-red-500" />
      <h2>Oops!</h2>
      <p>{error}</p>
    </div>
  {:else if submitted}
    <div class="success">
      <Check class="w-16 h-16 text-emerald-500" />
      <h2>Data Terkirim!</h2>
      <p>Data Anda sedang dalam proses review oleh tim travel.</p>
    </div>
  {:else}
    <div class="form-container">
      <h1>Pendaftaran Jamaah</h1>
      <p class="group-name">{groupInfo?.group_name}</p>
      
      <form onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
        <div class="field">
          <label>Nomor WhatsApp</label>
          <input
            type="tel"
            bind:value={phone}
            placeholder="08xxxxxxxxxx"
            required
          />
        </div>
        
        <div class="field">
          <label>Upload KTP/KK (Wajib)</label>
          <div class="upload-area">
            <input
              type="file"
              accept="image/*"
              onchange={handleFileChange}
              required
            />
            <Upload class="w-8 h-8" />
            <span>Klik atau foto KTP/KK Anda</span>
          </div>
        </div>
        
        <div class="field">
          <label>Upload Paspor (Opsional)</label>
          <div class="upload-area">
            <input type="file" accept="image/*" />
            <Upload class="w-8 h-8" />
            <span>Klik atau foto Paspor</span>
          </div>
        </div>
        
        <button type="submit" disabled={submitting || !phone || files.length === 0}>
          {#if submitting}
            <Loader2 class="w-5 h-5 animate-spin" />
            Memproses...
          {:else}
            Kirim Data
          {/if}
        </button>
      </form>
    </div>
  {/if}
</div>

<style>
  .registration-page {
    min-height: 100vh;
    background: linear-gradient(135deg, #f0fdf4, #ecfeff);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .loading, .error, .success {
    text-align: center;
    padding: 2rem;
  }
  
  .form-container {
    background: white;
    border-radius: 1rem;
    padding: 2rem;
    max-width: 400px;
    width: 100%;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }
  
  h1 {
    font-size: 1.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 0.5rem;
  }
  
  .group-name {
    text-align: center;
    color: #64748b;
    margin-bottom: 1.5rem;
  }
  
  .field {
    margin-bottom: 1.25rem;
  }
  
  label {
    display: block;
    font-weight: 500;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
  
  input[type="tel"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.5rem;
    font-size: 1rem;
  }
  
  .upload-area {
    border: 2px dashed #cbd5e1;
    border-radius: 0.5rem;
    padding: 2rem;
    text-align: center;
    position: relative;
  }
  
  .upload-area input {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
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
  }
  
  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
```

**Step 2: Add API methods**

Add to `frontend-svelte/src/lib/services/api.js`:
```javascript
async getRegistrationInfo(token) {
  const res = await fetch(`${API_BASE}/registration/public/${token}`);
  if (!res.ok) throw new Error((await res.json()).detail || "Failed");
  return res.json();
}

async submitRegistration(token, formData) {
  const res = await fetch(`${API_BASE}/registration/public/${token}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Failed");
  return res.json();
}
```

**Step 3: Commit**

```bash
git add frontend-svelte/src/lib/pages/PublicRegistrationPage.svelte frontend-svelte/src/lib/services/api.js
git commit -m "feat: add public registration page for self-service jamaah onboarding"
```

---

### Task 2.2: Create RegistrationLinkModal Component

**Files:**
- Create: `frontend-svelte/src/lib/components/RegistrationLinkModal.svelte`

**Step 1: Write the component**

```svelte
<script>
  import { X, Copy, Check, QrCode, Loader2 } from "lucide-svelte";
  import { ApiService } from "../services/api";

  let { groupId, onClose } = $props();

  let link = $state(null);
  let loading = $state(false);
  let copied = $state(false);

  onMount(async () => {
    loading = true;
    try {
      const res = await ApiService.getRegistrationLink(groupId);
      if (res.active) {
        link = res;
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  });

  async function generateLink() {
    loading = true;
    try {
      const res = await ApiService.generateRegistrationLink(groupId, 30);
      link = res;
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  async function copyLink() {
    await navigator.clipboard.writeText(link.link);
    copied = true;
    setTimeout(() => (copied = false), 2000);
  }

  async function revokeLink() {
    await ApiService.revokeRegistrationLink(groupId);
    link = null;
  }
</script>

<div class="modal-overlay" onclick={onClose}>
  <div class="modal" onclick={(e) => e.stopPropagation()}>
    <div class="modal-header">
      <h3>Link Pendaftaran Jamaah</h3>
      <button type="button" onclick={onClose}>
        <X class="w-5 h-5" />
      </button>
    </div>

    <div class="modal-body">
      {#if loading}
        <div class="loading">
          <Loader2 class="w-6 h-6 animate-spin" />
        </div>
      {:else if link}
        <div class="link-info">
          <label>Link Pendaftaran</label>
          <div class="link-box">
            <input type="text" value={link.link} readonly />
            <button type="button" onclick={copyLink}>
              {#if copied}
                <Check class="w-4 h-4" />
              {:else}
                <Copy class="w-4 h-4" />
              {/if}
            </button>
          </div>
          <p class="expires">Berlaku hingga: {new Date(link.expires_at).toLocaleDateString('id-ID')}</p>
          
          <button type="button" class="revoke" onclick={revokeLink}>
            Nonaktifkan Link
          </button>
        </div>
      {:else}
        <div class="no-link">
          <p>Belum ada link pendaftaran untuk grup ini.</p>
          <button type="button" onclick={generateLink}>
            Generate Link
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 100;
  }
  
  .modal {
    background: white;
    border-radius: 0.75rem;
    width: 100%;
    max-width: 480px;
  }
  
  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid #e2e8f0;
  }
  
  .modal-header h3 {
    font-weight: 600;
  }
  
  .modal-body {
    padding: 1.25rem;
  }
  
  .link-box {
    display: flex;
    gap: 0.5rem;
  }
  
  .link-box input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #e2e8f0;
    border-radius: 0.375rem;
    font-size: 0.875rem;
  }
  
  .expires {
    font-size: 0.75rem;
    color: #64748b;
    margin-top: 0.5rem;
  }
  
  .revoke {
    width: 100%;
    margin-top: 1rem;
    padding: 0.5rem;
    background: #fef2f2;
    color: #dc2626;
    border: none;
    border-radius: 0.375rem;
    cursor: pointer;
  }
  
  .no-link {
    text-align: center;
  }
  
  .no-link button {
    margin-top: 1rem;
    padding: 0.75rem 1.5rem;
    background: linear-gradient(135deg, #10b981, #059669);
    color: white;
    border: none;
    border-radius: 0.5rem;
    cursor: pointer;
  }
</style>
```

**Step 2: Add API methods**

Add to `api.js`:
```javascript
async getRegistrationLink(groupId) {
  const res = await fetch(`${API_BASE}/registration/link/${groupId}`, {
    headers: { Authorization: `Bearer ${this.token}` },
  });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

async generateRegistrationLink(groupId, expiresInDays) {
  const res = await fetch(`${API_BASE}/registration/generate`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${this.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ group_id: groupId, expires_in_days: expiresInDays }),
  });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

async revokeRegistrationLink(groupId) {
  const res = await fetch(`${API_BASE}/registration/link/${groupId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${this.token}` },
  });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}
```

**Step 3: Commit**

```bash
git add frontend-svelte/src/lib/components/RegistrationLinkModal.svelte frontend-svelte/src/lib/services/api.js
git commit -m "feat: add RegistrationLinkModal for admin to generate/manage links"
```

---

## Phase 3: Multi-Format Export Backend

### Task 3.1: Create ExportTemplate Model

**Files:**
- Create: `backend/app/models/export_template.py`
- Modify: `backend/app/models/__init__.py`

**Step 1: Write the model**

```python
# backend/app/models/export_template.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database import Base

class ExportTemplate(Base):
    __tablename__ = "export_templates"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    name = Column(String(100), nullable=False)
    file_path = Column(String(255), nullable=False)
    column_mapping = Column(JSON, nullable=False)
    header_row = Column(Integer, default=1)
    data_start_row = Column(Integer, default=2)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)

    # Relationships
    user = relationship("User")
```

**Step 2: Export and commit**

```bash
git add backend/app/models/export_template.py backend/app/models/__init__.py
git commit -m "feat: add ExportTemplate model for custom Excel exports"
```

---

### Task 3.2: Create Export Router

**Files:**
- Create: `backend/app/routers/export_router.py`
- Modify: `backend/main.py`

**Step 1: Write the router** (simplified for plan - full implementation would be longer)

```python
# backend/app/routers/export_router.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from openpyxl import load_workbook
import os

from backend.app.database import get_db
from backend.app.auth import get_current_user
from backend.app.models.user import User
from backend.app.models.export_template import ExportTemplate

router = APIRouter(prefix="/export-templates", tags=["export"])

HEADER_MAPPINGS = {
    "nama": "nama",
    "nama lengkap": "nama",
    "no paspor": "no_paspor",
    "passport no": "no_paspor",
    "tanggal lahir": "tanggal_lahir",
    "dob": "tanggal_lahir",
    # ... more mappings
}

@router.post("/upload")
async def upload_template(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload Excel template and auto-detect column mappings."""
    # Save file
    file_path = f"uploads/templates/{current_user.id}_{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Load workbook and detect headers
    wb = load_workbook(file_path)
    ws = wb.active
    
    header_row = 1
    headers = [cell.value for cell in ws[header_row] if cell.value]
    
    # Auto-detect mapping
    mapping = {}
    for idx, header in enumerate(headers):
        header_lower = str(header).lower().strip()
        if header_lower in HEADER_MAPPINGS:
            mapping[idx] = HEADER_MAPPINGS[header_lower]
    
    return {
        "file_path": file_path,
        "headers": headers,
        "auto_mapping": mapping,
    }

@router.post("/")
def save_template(
    name: str,
    file_path: str,
    column_mapping: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save a template with custom mapping."""
    template = ExportTemplate(
        user_id=current_user.id,
        name=name,
        file_path=file_path,
        column_mapping=column_mapping,
    )
    db.add(template)
    db.commit()
    
    return {"id": template.id, "name": template.name}

@router.get("/")
def list_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List saved templates."""
    templates = db.query(ExportTemplate).filter(
        ExportTemplate.user_id == current_user.id
    ).all()
    
    return {"templates": [{"id": t.id, "name": t.name} for t in templates]}
```

**Step 2: Register and commit**

```bash
git add backend/app/routers/export_router.py backend/main.py
git commit -m "feat: add export template router with upload and auto-mapping"
```

---

## Summary

This plan covers:

1. **Backend Models:** RegistrationLink, PendingMember, ExportTemplate
2. **Backend Endpoints:** Registration generation/submit/review, Template upload/export
3. **Frontend Components:** PublicRegistrationPage, RegistrationLinkModal
4. **API Service:** New methods for registration and export

**Estimated Tasks:** 10 implementation tasks
**Estimated Time:** 4-6 hours for experienced developer

---

*Plan generated: 2026-02-28*

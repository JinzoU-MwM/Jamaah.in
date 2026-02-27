"""
Group and GroupMember models for organizing jamaah data by trip/event.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Group(Base):
    """A named collection of jamaah data (e.g. 'UMROH 12 Feb 2026')."""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1, nullable=False)  # Optimistic locking

    # --- Mutawwif link sharing ---
    shared_token = Column(String(64), unique=True, index=True, nullable=True)   # UUIDv4
    shared_pin = Column(String(10), nullable=True)                               # 4-digit PIN
    shared_expires_at = Column(DateTime, nullable=True)                          # Auto-expire

    # --- Organization (Team) link ---
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    user = relationship("User", backref="groups")
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")

    @property
    def member_count(self):
        return len(self.members)


class GroupMember(Base):
    """A single jamaah data row belonging to a group — matches 32 Excel columns + operational fields."""
    __tablename__ = "group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- 32 data columns (matching ExtractedDataItem / Excel structure) ---
    title = Column(String(50), default="")
    nama = Column(String(255), default="")
    nama_ayah = Column(String(255), default="")
    jenis_identitas = Column(String(50), default="")
    no_identitas = Column(String(100), default="")
    nama_paspor = Column(String(255), default="")
    no_paspor = Column(String(100), default="")
    tanggal_paspor = Column(String(20), default="")
    kota_paspor = Column(String(100), default="")
    tempat_lahir = Column(String(100), default="")
    tanggal_lahir = Column(String(20), default="")
    alamat = Column(Text, default="")
    provinsi = Column(String(100), default="")
    kabupaten = Column(String(100), default="")
    kecamatan = Column(String(100), default="")
    kelurahan = Column(String(100), default="")
    no_telepon = Column(String(50), default="")
    no_hp = Column(String(50), default="")
    kewarganegaraan = Column(String(50), default="WNI")
    status_pernikahan = Column(String(50), default="")
    pendidikan = Column(String(100), default="")
    pekerjaan = Column(String(100), default="")
    provider_visa = Column(String(255), default="")
    no_visa = Column(String(100), default="")
    tanggal_visa = Column(String(20), default="")
    tanggal_visa_akhir = Column(String(20), default="")
    asuransi = Column(String(255), default="")
    no_polis = Column(String(100), default="")
    tanggal_input_polis = Column(String(20), default="")
    tanggal_awal_polis = Column(String(20), default="")
    tanggal_akhir_polis = Column(String(20), default="")
    no_bpjs = Column(String(100), default="")

    # --- Operational columns (internal use, NOT exported to Excel) ---
    baju_size = Column(String(10), default="")  # S/M/L/XL/XXL
    family_id = Column(String(100), default="", index=True)  # Group families together
    is_equipment_received = Column(Boolean, default=False)  # Inventory checklist
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    group = relationship("Group", back_populates="members")
    room = relationship("Room", back_populates="members")

    def to_dict(self):
        """Convert to dict matching ExtractedDataItem format (32 columns only, no operational fields)."""
        return {
            "id": self.id,
            "title": self.title or "",
            "nama": self.nama or "",
            "nama_ayah": self.nama_ayah or "",
            "jenis_identitas": self.jenis_identitas or "",
            "no_identitas": self.no_identitas or "",
            "nama_paspor": self.nama_paspor or "",
            "no_paspor": self.no_paspor or "",
            "tanggal_paspor": self.tanggal_paspor or "",
            "kota_paspor": self.kota_paspor or "",
            "tempat_lahir": self.tempat_lahir or "",
            "tanggal_lahir": self.tanggal_lahir or "",
            "alamat": self.alamat or "",
            "provinsi": self.provinsi or "",
            "kabupaten": self.kabupaten or "",
            "kecamatan": self.kecamatan or "",
            "kelurahan": self.kelurahan or "",
            "no_telepon": self.no_telepon or "",
            "no_hp": self.no_hp or "",
            "kewarganegaraan": self.kewarganegaraan or "WNI",
            "status_pernikahan": self.status_pernikahan or "",
            "pendidikan": self.pendidikan or "",
            "pekerjaan": self.pekerjaan or "",
            "provider_visa": self.provider_visa or "",
            "no_visa": self.no_visa or "",
            "tanggal_visa": self.tanggal_visa or "",
            "tanggal_visa_akhir": self.tanggal_visa_akhir or "",
            "asuransi": self.asuransi or "",
            "no_polis": self.no_polis or "",
            "tanggal_input_polis": self.tanggal_input_polis or "",
            "tanggal_awal_polis": self.tanggal_awal_polis or "",
            "tanggal_akhir_polis": self.tanggal_akhir_polis or "",
            "no_bpjs": self.no_bpjs or "",
        }

    def to_dict_full(self):
        """Convert to dict including operational fields."""
        data = self.to_dict()
        data.update({
            "baju_size": self.baju_size or "",
            "family_id": self.family_id or "",
            "is_equipment_received": self.is_equipment_received,
            "room_id": self.room_id,
        })
        return data

    @property
    def gender(self):
        """Derive gender from title."""
        if self.title and self.title.lower() in ["mr", "tuan"]:
            return "male"
        elif self.title and self.title.lower() in ["mrs", "ms", "nyonya", "nona"]:
            return "female"
        return "unknown"

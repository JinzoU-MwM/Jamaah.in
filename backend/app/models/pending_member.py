from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PendingMember(Base):
    """Pending jamaah registration from self-service registration links."""
    __tablename__ = "pending_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False
    )
    phone_number = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    submitted_at = Column(DateTime, default=utc_now)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 32 columns matching GroupMember
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

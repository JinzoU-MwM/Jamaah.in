package model

import (
	"time"

	"github.com/google/uuid"
)

type PipelineStatus string

const (
	StatusProspek  PipelineStatus = "prospek"
	StatusSurvey   PipelineStatus = "survey"
	StatusBooking  PipelineStatus = "booking"
	StatusDP       PipelineStatus = "dp"
	StatusCicilan  PipelineStatus = "cicilan"
	StatusLunas    PipelineStatus = "lunas"
	StatusBerangkat PipelineStatus = "berangkat"
	StatusSelesai   PipelineStatus = "selesai"
	StatusBatal     PipelineStatus = "batal"
)

func ValidPipelineStatuses() []string {
	return []string{"prospek", "survey", "booking", "dp", "cicilan", "lunas", "berangkat", "selesai", "batal"}
}

type LeadSource string

const (
	LeadWalkIn  LeadSource = "walk_in"
	LeadReferral LeadSource = "referral"
	LeadOnline  LeadSource = "online"
	LeadAgent   LeadSource = "agent"
)

func ValidLeadSources() []string {
	return []string{"walk_in", "referral", "online", "agent"}
}

type JamaahProfile struct {
	ID                     uuid.UUID  `json:"id" db:"id"`
	OrgID                  uuid.UUID  `json:"org_id" db:"org_id"`
	Title                  string     `json:"title" db:"title"`
	Nama                   string     `json:"nama" db:"nama"`
	NamaAyah              string     `json:"nama_ayah" db:"nama_ayah"`
	JenisIdentitas         string     `json:"jenis_identitas" db:"jenis_identitas"`
	NoIdentitas           *string    `json:"no_identitas,omitempty" db:"no_identitas"`
	NamaPaspor            string     `json:"nama_paspor" db:"nama_paspor"`
	NoPaspor              *string    `json:"no_paspor,omitempty" db:"no_paspor"`
	TanggalPaspor         *time.Time `json:"tanggal_paspor,omitempty" db:"tanggal_paspor"`
	KotaPaspor            string     `json:"kota_paspor" db:"kota_paspor"`
	TempatLahir           string     `json:"tempat_lahir" db:"tempat_lahir"`
	TanggalLahir          *time.Time `json:"tanggal_lahir,omitempty" db:"tanggal_lahir"`
	Gender                string     `json:"gender" db:"gender"`
	Alamat                string     `json:"alamat" db:"alamat"`
	Provinsi               string     `json:"provinsi" db:"provinsi"`
	Kabupaten             string     `json:"kabupaten" db:"kabupaten"`
	Kecamatan             string     `json:"kecamatan" db:"kecamatan"`
	Kelurahan             string     `json:"kelurahan" db:"kelurahan"`
	NoTelepon             string     `json:"no_telepon" db:"no_telepon"`
	NoHP                  string     `json:"no_hp" db:"no_hp"`
	Kewarganegaraan       string     `json:"kewarganegaraan" db:"kewarganegaraan"`
	StatusPernikahan      string     `json:"status_pernikahan" db:"status_pernikahan"`
	Pendidikan            string     `json:"pendidikan" db:"pendidikan"`
	Pekerjaan             string     `json:"pekerjaan" db:"pekerjaan"`
	GolonganDarah         string     `json:"golongan_darah" db:"golongan_darah"`
	ProviderVisa          string     `json:"provider_visa" db:"provider_visa"`
	NoVisa                string     `json:"no_visa" db:"no_visa"`
	TanggalVisa          *time.Time `json:"tanggal_visa,omitempty" db:"tanggal_visa"`
	TanggalVisaAkhir      *time.Time `json:"tanggal_visa_akhir,omitempty" db:"tanggal_visa_akhir"`
	Asuransi               string     `json:"asuransi" db:"asuransi"`
	NoPolis               string     `json:"no_polis" db:"no_polis"`
	TanggalInputPolis     *time.Time `json:"tanggal_input_polis,omitempty" db:"tanggal_input_polis"`
	TanggalAwalPolis      *time.Time `json:"tanggal_awal_polis,omitempty" db:"tanggal_awal_polis"`
	TanggalAkhirPolis    *time.Time `json:"tanggal_akhir_polis,omitempty" db:"tanggal_akhir_polis"`
	NoBpjs                string     `json:"no_bpjs" db:"no_bpjs"`
	Email                 string     `json:"email" db:"email"`
	ContactEmergencyName  string     `json:"contact_emergency_name" db:"contact_emergency_name"`
	ContactEmergencyPhone string     `json:"contact_emergency_phone" db:"contact_emergency_phone"`
	LeadSource            string     `json:"lead_source" db:"lead_source"`
	ReferringAgentID      *uuid.UUID `json:"referring_agent_id,omitempty" db:"referring_agent_id"`
	IhramSize             string     `json:"ihram_size" db:"ihram_size"`
	MukenaSize            string     `json:"mukena_size" db:"mukena_size"`
	BajuSize              string     `json:"baju_size" db:"baju_size"`
	CreatedAt             time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt             time.Time  `json:"updated_at" db:"updated_at"`

	Registrations []JamaahPackageRegistration `json:"registrations,omitempty" db:"-"`
	Documents     []JamaahDocument            `json:"documents,omitempty" db:"-"`
	Notes         []JamaahNote                `json:"notes,omitempty" db:"-"`
	FollowUps     []FollowUp                  `json:"follow_ups,omitempty" db:"-"`
}

type JamaahPackageRegistration struct {
	ID             uuid.UUID  `json:"id" db:"id"`
	OrgID          uuid.UUID  `json:"org_id" db:"org_id"`
	JamaahID       uuid.UUID  `json:"jamaah_id" db:"jamaah_id"`
	PackageID      uuid.UUID  `json:"package_id" db:"package_id"`
	RoomType        string     `json:"room_type" db:"room_type"`
	PriceSnapshot   int64      `json:"price_snapshot" db:"price_snapshot"`
	DiscountAmount  int64      `json:"discount_amount" db:"discount_amount"`
	CustomPrice     *int64     `json:"custom_price,omitempty" db:"custom_price"`
	PipelineStatus  string     `json:"pipeline_status" db:"pipeline_status"`
	RegisteredAt    time.Time  `json:"registered_at" db:"registered_at"`
	DPDate          *time.Time `json:"dp_date,omitempty" db:"dp_date"`
	LunasDate       *time.Time `json:"lunas_date,omitempty" db:"lunas_date"`
	BerangkatDate   *time.Time `json:"berangkat_date,omitempty" db:"berangkat_date"`
	MahramID        *uuid.UUID `json:"mahram_id,omitempty" db:"mahram_id"`
	InternalNotes   string     `json:"internal_notes" db:"internal_notes"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`
}

type JamaahNote struct {
	ID        uuid.UUID `json:"id" db:"id"`
	JamaahID  uuid.UUID `json:"jamaah_id" db:"jamaah_id"`
	OrgID     uuid.UUID `json:"org_id" db:"org_id"`
	UserID    uuid.UUID `json:"user_id" db:"user_id"`
	Content   string    `json:"content" db:"content"`
	CreatedAt time.Time `json:"created_at" db:"created_at"`
}

type FollowUp struct {
	ID          uuid.UUID  `json:"id" db:"id"`
	JamaahID    uuid.UUID  `json:"jamaah_id" db:"jamaah_id"`
	PackageID   *uuid.UUID `json:"package_id,omitempty" db:"package_id"`
	OrgID       uuid.UUID  `json:"org_id" db:"org_id"`
	UserID      uuid.UUID  `json:"user_id" db:"user_id"`
	Description string     `json:"description" db:"description"`
	DueDate     time.Time  `json:"due_date" db:"due_date"`
	IsCompleted bool       `json:"is_completed" db:"is_completed"`
	CompletedAt *time.Time `json:"completed_at,omitempty" db:"completed_at"`
	CreatedAt   time.Time  `json:"created_at" db:"created_at"`
}

type JamaahDocument struct {
	ID          uuid.UUID  `json:"id" db:"id"`
	JamaahID    uuid.UUID  `json:"jamaah_id" db:"jamaah_id"`
	PackageID   *uuid.UUID `json:"package_id,omitempty" db:"package_id"`
	OrgID       uuid.UUID  `json:"org_id" db:"org_id"`
	DocType     string     `json:"doc_type" db:"doc_type"`
	Status      string     `json:"status" db:"status"`
	FileURL     *string    `json:"file_url,omitempty" db:"file_url"`
	FileName    *string    `json:"file_name,omitempty" db:"file_name"`
	FileSize    *int64     `json:"file_size,omitempty" db:"file_size"`
	Notes       string     `json:"notes" db:"notes"`
	VerifiedBy  *uuid.UUID `json:"verified_by,omitempty" db:"verified_by"`
	VerifiedAt  *time.Time `json:"verified_at,omitempty" db:"verified_at"`
	CreatedAt   time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at" db:"updated_at"`
}

type SiskopatuhRow struct {
	Title              string `json:"title"`
	Nama               string `json:"nama"`
	NamaAyah          string `json:"nama_ayah"`
	JenisIdentitas     string `json:"jenis_identitas"`
	NoIdentitas       string `json:"no_identitas"`
	NamaPaspor        string `json:"nama_paspor"`
	NoPaspor          string `json:"no_paspor"`
	TanggalPaspor     string `json:"tanggal_paspor"`
	KotaPaspor        string `json:"kota_paspor"`
	TempatLahir       string `json:"tempat_lahir"`
	TanggalLahir      string `json:"tanggal_lahir"`
	Alamat            string `json:"alamat"`
	Provinsi          string `json:"provinsi"`
	Kabupaten         string `json:"kabupaten"`
	Kecamatan         string `json:"kecamatan"`
	Kelurahan         string `json:"kelurahan"`
	NoTelepon         string `json:"no_telepon"`
	NoHP              string `json:"no_hp"`
	Kewarganegaraan  string `json:"kewarganegaraan"`
	StatusPernikahan string `json:"status_pernikahan"`
	Pendidikan        string `json:"pendidikan"`
	Pekerjaan         string `json:"pekerjaan"`
	ProviderVisa      string `json:"provider_visa"`
	NoVisa            string `json:"no_visa"`
	TanggalVisa       string `json:"tanggal_visa"`
	TanggalVisaAkhir string `json:"tanggal_visa_akhir"`
	Asuransi          string `json:"asuransi"`
	NoPolis           string `json:"no_polis"`
	TanggalInputPolis string `json:"tanggal_input_polis"`
	TanggalAwalPolis string `json:"tanggal_awal_polis"`
	TanggalAkhirPolis string `json:"tanggal_akhir_polis"`
	NoBpjs            string `json:"no_bpjs"`
}

type CreateJamaahRequest struct {
	Title                 string  `json:"title" validate:"max=20"`
	Nama                  string  `json:"nama" validate:"required,min=2,max=255"`
	NamaAyah             string  `json:"nama_ayah,omitempty"`
	JenisIdentitas         string  `json:"jenis_identitas,omitempty"`
	NoIdentitas           string  `json:"no_identitas,omitempty"`
	NamaPaspor            string  `json:"nama_paspor,omitempty"`
	NoPaspor              string  `json:"no_paspor,omitempty"`
	TanggalPaspor         string  `json:"tanggal_paspor,omitempty"`
	KotaPaspor            string  `json:"kota_paspor,omitempty"`
	TempatLahir           string  `json:"tempat_lahir,omitempty"`
	TanggalLahir          string  `json:"tanggal_lahir,omitempty"`
	Gender                string  `json:"gender,omitempty"`
	Alamat                string  `json:"alamat,omitempty"`
	Provinsi              string  `json:"provinsi,omitempty"`
	Kabupaten             string  `json:"kabupaten,omitempty"`
	Kecamatan             string  `json:"kecamatan,omitempty"`
	Kelurahan             string  `json:"kelurahan,omitempty"`
	NoTelepon             string  `json:"no_telepon,omitempty"`
	NoHP                  string  `json:"no_hp,omitempty"`
	Kewarganegaraan       string  `json:"kewarganegaraan,omitempty"`
	StatusPernikahan      string  `json:"status_pernikahan,omitempty"`
	Pendidikan            string  `json:"pendidikan,omitempty"`
	Pekerjaan             string  `json:"pekerjaan,omitempty"`
	ProviderVisa          string  `json:"provider_visa,omitempty"`
	NoVisa                string  `json:"no_visa,omitempty"`
	Asuransi               string  `json:"asuransi,omitempty"`
	NoPolis               string  `json:"no_polis,omitempty"`
	Email                 string  `json:"email,omitempty"`
	ContactEmergencyName  string  `json:"contact_emergency_name,omitempty"`
	ContactEmergencyPhone string  `json:"contact_emergency_phone,omitempty"`
	LeadSource            string  `json:"lead_source,omitempty"`
	IhramSize             string  `json:"ihram_size,omitempty"`
	MukenaSize            string  `json:"mukena_size,omitempty"`
	BajuSize              string  `json:"baju_size,omitempty"`
}

type UpdateJamaahRequest struct {
	Title                 *string `json:"title,omitempty"`
	Nama                  *string `json:"nama,omitempty"`
	NamaAyah             *string `json:"nama_ayah,omitempty"`
	JenisIdentitas         *string `json:"jenis_identitas,omitempty"`
	NoIdentitas           *string `json:"no_identitas,omitempty"`
	NamaPaspor            *string `json:"nama_paspor,omitempty"`
	NoPaspor              *string `json:"no_paspor,omitempty"`
	TanggalPaspor         *string `json:"tanggal_paspor,omitempty"`
	KotaPaspor            *string `json:"kota_paspor,omitempty"`
	TempatLahir           *string `json:"tempat_lahir,omitempty"`
	TanggalLahir          *string `json:"tanggal_lahir,omitempty"`
	Gender                *string `json:"gender,omitempty"`
	Alamat                *string `json:"alamat,omitempty"`
	Provinsi              *string `json:"provinsi,omitempty"`
	Kabupaten             *string `json:"kabupaten,omitempty"`
	Kecamatan             *string `json:"kecamatan,omitempty"`
	Kelurahan             *string `json:"kelurahan,omitempty"`
	NoTelepon             *string `json:"no_telepon,omitempty"`
	NoHP                  *string `json:"no_hp,omitempty"`
	Kewarganegaraan       *string `json:"kewarganegaraan,omitempty"`
	StatusPernikahan      *string `json:"status_pernikahan,omitempty"`
	Pendidikan            *string `json:"pendidikan,omitempty"`
	Pekerjaan             *string `json:"pekerjaan,omitempty"`
	ProviderVisa          *string `json:"provider_visa,omitempty"`
	NoVisa                *string `json:"no_visa,omitempty"`
	Asuransi               *string `json:"asuransi,omitempty"`
	NoPolis               *string `json:"no_polis,omitempty"`
	Email                 *string `json:"email,omitempty"`
	ContactEmergencyName  *string `json:"contact_emergency_name,omitempty"`
	ContactEmergencyPhone *string `json:"contact_emergency_phone,omitempty"`
	LeadSource            *string `json:"lead_source,omitempty"`
	IhramSize             *string `json:"ihram_size,omitempty"`
	MukenaSize            *string `json:"mukena_size,omitempty"`
	BajuSize              *string `json:"baju_size,omitempty"`
}

type RegisterToPackageRequest struct {
	PackageID    uuid.UUID `json:"package_id" validate:"required"`
	RoomType     string     `json:"room_type" validate:"required,oneof=quad triple double single"`
	PriceSnapshot int64     `json:"price_snapshot" validate:"min=1"`
	DiscountAmount int64    `json:"discount_amount,omitempty"`
	CustomPrice   *int64    `json:"custom_price,omitempty"`
}

type UpdatePipelineStatusRequest struct {
	PipelineStatus string `json:"pipeline_status" validate:"required,oneof=prospek survey booking dp cicilan lunas berangkat selesai batal"`
}

type AddNoteRequest struct {
	Content string `json:"content" validate:"required"`
}

type AddFollowUpRequest struct {
	PackageID   *string `json:"package_id,omitempty"`
	Description string `json:"description" validate:"required"`
	DueDate     string `json:"due_date" validate:"required"`
}

type UploadDocumentRequest struct {
	DocType string `json:"doc_type" validate:"required,oneof=ktp kk paspor pas_foto icv visa formulir akta_nikah akta_lahir surat_mahram surat_rekomendasi other"`
	Status  string `json:"status,omitempty"`
	Notes   string `json:"notes,omitempty"`
}

type UpdateDocumentStatusRequest struct {
	Status string `json:"status" validate:"required,oneof=belum_diterima diterima diproses selesai"`
	Notes  string `json:"notes,omitempty"`
}

type DashboardAlerts struct {
	PassportExpiring90 []JamaahProfile `json:"passport_expiring_90"`
	PassportExpiring30 []JamaahProfile `json:"passport_expiring_30"`
	OverdueFollowUps   []FollowUp       `json:"overdue_follow_ups"`
	IncompleteDocs     []JamaahDocument `json:"incomplete_docs"`
}
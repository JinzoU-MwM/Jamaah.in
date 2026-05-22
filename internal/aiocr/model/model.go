package model

import (
	"time"

	"github.com/google/uuid"
)

type ScanJobStatus string

const (
	ScanStatusPending    ScanJobStatus = "pending"
	ScanStatusProcessing ScanJobStatus = "processing"
	ScanStatusCompleted  ScanJobStatus = "completed"
	ScanStatusFailed     ScanJobStatus = "failed"
)

type ScanResultStatus string

const (
	ResultStatusPending    ScanResultStatus = "pending"
	ResultStatusCompleted  ScanResultStatus = "completed"
	ResultStatusFailed     ScanResultStatus = "failed"
	ResultStatusPartial    ScanResultStatus = "partial"
)

func ValidScanJobStatuses() []string {
	return []string{"pending", "processing", "completed", "failed"}
}

type ScanJob struct {
	ID              uuid.UUID  `json:"id" db:"id"`
	OrgID           uuid.UUID  `json:"org_id" db:"org_id"`
	UserID          uuid.UUID  `json:"user_id" db:"user_id"`
	PackageID       *uuid.UUID `json:"package_id,omitempty" db:"package_id"`
	Status          string     `json:"status" db:"status"`
	TotalFiles      int        `json:"total_files" db:"total_files"`
	ProcessedFiles  int        `json:"processed_files" db:"processed_files"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`
	Results         []ScanResult `json:"results,omitempty" db:"-"`
}

type ScanResult struct {
	ID               uuid.UUID  `json:"id" db:"id"`
	ScanJobID        uuid.UUID  `json:"scan_job_id" db:"scan_job_id"`
	OrgID            uuid.UUID  `json:"org_id" db:"org_id"`
	FileName         string     `json:"file_name" db:"file_name"`
	FileURL          string     `json:"file_url" db:"file_url"`
	FileSize         *int64     `json:"file_size,omitempty" db:"file_size"`
	FileHash         string     `json:"file_hash" db:"file_hash"`
	DocType          *string    `json:"doc_type,omitempty" db:"doc_type"`
	ExtractedData    any        `json:"extracted_data,omitempty" db:"extracted_data"`
	NormalizedData   any        `json:"normalized_data,omitempty" db:"normalized_data"`
	ValidationErrors any        `json:"validation_errors,omitempty" db:"validation_errors"`
	CacheHit         *bool      `json:"cache_hit,omitempty" db:"cache_hit"`
	ModelUsed        string     `json:"model_used" db:"model_used"`
	PromptVersion    string     `json:"prompt_version" db:"prompt_version"`
	Status           string     `json:"status" db:"status"`
	ErrorMessage     *string   `json:"error_message,omitempty" db:"error_message"`
	ProcessingTimeMs *int       `json:"processing_time_ms,omitempty" db:"processing_time_ms"`
	CreatedAt        time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time  `json:"updated_at" db:"updated_at"`
}

type ExportTemplate struct {
	ID            uuid.UUID `json:"id" db:"id"`
	OrgID        uuid.UUID `json:"org_id" db:"org_id"`
	UserID       uuid.UUID `json:"user_id" db:"user_id"`
	Name         string     `json:"name" db:"name"`
	FileURL      string     `json:"file_url" db:"file_url"`
	ColumnMapping any       `json:"column_mapping" db:"column_mapping"`
	HeaderRow     int        `json:"header_row" db:"header_row"`
	DataStartRow  int        `json:"data_start_row" db:"data_start_row"`
	IsDefault     bool       `json:"is_default" db:"is_default"`
	CreatedAt     time.Time  `json:"created_at" db:"created_at"`
}

type CreateScanJobRequest struct {
	PackageID *string `json:"package_id,omitempty"`
	Files     []ScanFileInput `json:"files" validate:"required"`
}

type ScanFileInput struct {
	FileName string `json:"file_name" validate:"required"`
	FileURL  string `json:"file_url" validate:"required"`
	FileSize int64  `json:"file_size,omitempty"`
	FileHash string `json:"file_hash,omitempty"`
}

type CreateExportTemplateRequest struct {
	Name          string `json:"name" validate:"required"`
	FileURL       string `json:"file_url" validate:"required"`
	ColumnMapping any    `json:"column_mapping" validate:"required"`
	HeaderRow     int    `json:"header_row,omitempty"`
	DataStartRow  int    `json:"data_start_row,omitempty"`
	IsDefault     bool   `json:"is_default,omitempty"`
}
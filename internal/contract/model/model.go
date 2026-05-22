package model

import (
	"time"

	"github.com/google/uuid"
)

type ContractStatus string

const (
	ContractStatusSent    ContractStatus = "terkirim"
	ContractStatusSigned  ContractStatus = "ditandatangani"
	ContractStatusExpired ContractStatus = "expired"
)

type SignatureMode string

const (
	SignatureModeDraw SignatureMode = "draw"
	SignatureModeType SignatureMode = "type"
)

type ContractTemplate struct {
	ID          uuid.UUID `json:"id" db:"id"`
	OrgID       uuid.UUID `json:"org_id" db:"org_id"`
	Name        string    `json:"name" db:"name"`
	PackageType *string   `json:"package_type,omitempty" db:"package_type"`
	Content     string    `json:"content" db:"content"`
	IsActive    bool      `json:"is_active" db:"is_active"`
	CreatedAt   time.Time `json:"created_at" db:"created_at"`
	UpdatedAt   time.Time `json:"updated_at" db:"updated_at"`
}

type CreateTemplateRequest struct {
	Name        string  `json:"name"`
	PackageType *string `json:"package_type,omitempty"`
	Content     string  `json:"content"`
	IsActive    *bool   `json:"is_active,omitempty"`
}

type UpdateTemplateRequest struct {
	Name        *string `json:"name,omitempty"`
	PackageType *string `json:"package_type,omitempty"`
	Content     *string `json:"content,omitempty"`
	IsActive    *bool   `json:"is_active,omitempty"`
}

type PreviewTemplateRequest struct {
	Content string            `json:"content"`
	Data    map[string]string `json:"data"`
}

type PreviewTemplateResponse struct {
	Rendered string `json:"rendered"`
}

type ContractInstance struct {
	ID              uuid.UUID         `json:"id" db:"id"`
	OrgID           uuid.UUID         `json:"org_id" db:"org_id"`
	TemplateID      uuid.UUID         `json:"template_id" db:"template_id"`
	JamaahID        *uuid.UUID        `json:"jamaah_id,omitempty" db:"jamaah_id"`
	PackageID       *uuid.UUID        `json:"package_id,omitempty" db:"package_id"`
	TemplateName    string            `json:"template_name" db:"template_name"`
	PackageType     *string           `json:"package_type,omitempty" db:"package_type"`
	RecipientName   string            `json:"recipient_name" db:"recipient_name"`
	RecipientPhone  *string           `json:"recipient_phone,omitempty" db:"recipient_phone"`
	RecipientEmail  *string           `json:"recipient_email,omitempty" db:"recipient_email"`
	PublicToken     string            `json:"public_token" db:"public_token"`
	Variables       map[string]string `json:"variables" db:"-"`
	RenderedContent string            `json:"rendered_content" db:"rendered_content"`
	Status          string            `json:"status" db:"status"`
	ExpiresAt       time.Time         `json:"expires_at" db:"expires_at"`
	SignedAt        *time.Time        `json:"signed_at,omitempty" db:"signed_at"`
	SignedName      *string           `json:"signed_name,omitempty" db:"signed_name"`
	SignatureMode   *string           `json:"signature_mode,omitempty" db:"signature_mode"`
	SignatureValue  *string           `json:"signature_value,omitempty" db:"signature_value"`
	SignedIPAddress *string           `json:"signed_ip_address,omitempty" db:"signed_ip_address"`
	DocumentHash    *string           `json:"document_hash,omitempty" db:"document_hash"`
	CreatedAt       time.Time         `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time         `json:"updated_at" db:"updated_at"`
}

type CreateContractInstanceRequest struct {
	TemplateID     uuid.UUID         `json:"template_id"`
	JamaahID       *uuid.UUID        `json:"jamaah_id,omitempty"`
	PackageID      *uuid.UUID        `json:"package_id,omitempty"`
	PackageType    *string           `json:"package_type,omitempty"`
	RecipientName  string            `json:"recipient_name"`
	RecipientPhone *string           `json:"recipient_phone,omitempty"`
	RecipientEmail *string           `json:"recipient_email,omitempty"`
	Variables      map[string]string `json:"variables"`
	ExpiresInDays  *int              `json:"expires_in_days,omitempty"`
}

type ListContractInstancesRequest struct {
	Status string `json:"status,omitempty"`
}

type SignContractRequest struct {
	SignedName       string `json:"signed_name"`
	SignatureMode    string `json:"signature_mode"`
	SignatureValue   string `json:"signature_value"`
	ConsentAccepted  bool   `json:"consent_accepted"`
	ScrolledToBottom bool   `json:"scrolled_to_bottom"`
}

type PublicContractResponse struct {
	ID               uuid.UUID  `json:"id"`
	TemplateName     string     `json:"template_name"`
	RecipientName    string     `json:"recipient_name"`
	RenderedContent  string     `json:"rendered_content"`
	Status           string     `json:"status"`
	ExpiresAt        time.Time  `json:"expires_at"`
	SignedAt         *time.Time `json:"signed_at,omitempty"`
	SignedName       *string    `json:"signed_name,omitempty"`
	SignatureMode    *string    `json:"signature_mode,omitempty"`
	DocumentHash     *string    `json:"document_hash,omitempty"`
	CanSign          bool       `json:"can_sign"`
	ConsentStatement string     `json:"consent_statement"`
}

package model

import (
	"time"

	"github.com/google/uuid"
)

type InvoiceStatus string

const (
	InvoiceStatusBelumBayar InvoiceStatus = "belum_bayar"
	InvoiceStatusSebagian   InvoiceStatus = "sebagian"
	InvoiceStatusLunas      InvoiceStatus = "lunas"
	InvoiceStatusBatal      InvoiceStatus = "batal"
)

type PaymentScheme string

const (
	SchemeDPAndLunas PaymentScheme = "dp_lunas"
	SchemeCicilan    PaymentScheme = "cicilan"
	SchemeFull       PaymentScheme = "full"
)

type PaymentMethod string

const (
	MethodTransferBank PaymentMethod = "transfer_bank"
	MethodTunai        PaymentMethod = "tunai"
	MethodQRIS         PaymentMethod = "qris"
	MethodKartuKredit  PaymentMethod = "kartu_kredit"
	MethodEWallet      PaymentMethod = "e_wallet"
)

func ValidInvoiceStatuses() []string {
	return []string{"belum_bayar", "sebagian", "lunas", "batal"}
}

func ValidPaymentSchemes() []string {
	return []string{"dp_lunas", "cicilan", "full"}
}

func ValidPaymentMethods() []string {
	return []string{"transfer_bank", "tunai", "qris", "kartu_kredit", "e_wallet"}
}

type Invoice struct {
	ID              uuid.UUID  `json:"id" db:"id"`
	OrgID           uuid.UUID  `json:"org_id" db:"org_id"`
	InvoiceNumber   string     `json:"invoice_number" db:"invoice_number"`
	JamaahID        uuid.UUID  `json:"jamaah_id" db:"jamaah_id"`
	PackageID       uuid.UUID  `json:"package_id" db:"package_id"`
	RegistrationID  uuid.UUID  `json:"registration_id" db:"registration_id"`
	RoomType         string     `json:"room_type" db:"room_type"`
	PriceSnapshot   int64      `json:"price_snapshot" db:"price_snapshot"`
	DiscountAmount  int64      `json:"discount_amount" db:"discount_amount"`
	SurchargeAmount int64      `json:"surcharge_amount" db:"surcharge_amount"`
	TotalAmount     int64      `json:"total_amount" db:"total_amount"`
	AmountPaid      int64      `json:"amount_paid" db:"amount_paid"`
	AmountRemaining int64      `json:"amount_remaining" db:"amount_remaining"`
	PaymentScheme   string     `json:"payment_scheme" db:"payment_scheme"`
	Status          string     `json:"status" db:"status"`
	IssuedAt        time.Time  `json:"issued_at" db:"issued_at"`
	DueDate         *time.Time `json:"due_date,omitempty" db:"due_date"`
	CancelledAt     *time.Time `json:"cancelled_at,omitempty" db:"cancelled_at"`
	CancelledReason *string    `json:"cancelled_reason,omitempty" db:"cancelled_reason"`
	Notes           string     `json:"notes,omitempty" db:"notes"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt       time.Time  `json:"updated_at" db:"updated_at"`

	PaymentSchedules []PaymentSchedule `json:"payment_schedules,omitempty" db:"-"`
	Payments         []Payment         `json:"payments,omitempty" db:"-"`
}

type PaymentSchedule struct {
	ID             uuid.UUID  `json:"id" db:"id"`
	InvoiceID      uuid.UUID  `json:"invoice_id" db:"invoice_id"`
	InstallmentNum int        `json:"installment_num" db:"installment_num"`
	Amount         int64      `json:"amount" db:"amount"`
	DueDate        *time.Time `json:"due_date,omitempty" db:"due_date"`
	Description    *string   `json:"description,omitempty" db:"description"`
	IsPaid         bool       `json:"is_paid" db:"is_paid"`
	PaidAt         *time.Time `json:"paid_at,omitempty" db:"paid_at"`
	CreatedAt      time.Time  `json:"created_at" db:"created_at"`
}

type Payment struct {
	ID              uuid.UUID  `json:"id" db:"id"`
	OrgID           uuid.UUID  `json:"org_id" db:"org_id"`
	InvoiceID       uuid.UUID  `json:"invoice_id" db:"invoice_id"`
	Amount          int64      `json:"amount" db:"amount"`
	PaymentMethod   string     `json:"payment_method" db:"payment_method"`
	BankName        *string    `json:"bank_name,omitempty" db:"bank_name"`
	AccountNumber   *string    `json:"account_number,omitempty" db:"account_number"`
	ReferenceNumber *string    `json:"reference_number,omitempty" db:"reference_number"`
	ProofURL        *string    `json:"proof_url,omitempty" db:"proof_url"`
	Notes           string     `json:"notes,omitempty" db:"notes"`
	ReceivedBy      uuid.UUID  `json:"received_by" db:"received_by"`
	PaidAt          time.Time  `json:"paid_at" db:"paid_at"`
	CreatedAt       time.Time  `json:"created_at" db:"created_at"`
}

type CreateInvoiceRequest struct {
	JamaahID       uuid.UUID  `json:"jamaah_id" validate:"required"`
	PackageID      uuid.UUID  `json:"package_id" validate:"required"`
	RegistrationID  uuid.UUID  `json:"registration_id" validate:"required"`
	RoomType        string     `json:"room_type" validate:"required,oneof=quad triple double single"`
	PriceSnapshot   int64      `json:"price_snapshot" validate:"min=1"`
	DiscountAmount  int64      `json:"discount_amount,omitempty"`
	SurchargeAmount int64      `json:"surcharge_amount,omitempty"`
	PaymentScheme   string     `json:"payment_scheme" validate:"required,oneof=dp_lunas cicilan full"`
	DueDate         string     `json:"due_date,omitempty"`
	Notes           string     `json:"notes,omitempty"`
}

type UpdateInvoiceRequest struct {
	DiscountAmount  *int64  `json:"discount_amount,omitempty"`
	SurchargeAmount *int64  `json:"surcharge_amount,omitempty"`
	Notes           *string `json:"notes,omitempty"`
	DueDate         *string `json:"due_date,omitempty"`
}

type CancelInvoiceRequest struct {
	Reason string `json:"reason" validate:"required"`
}

type CreatePaymentScheduleRequest struct {
	Installments []ScheduleInstallment `json:"installments" validate:"required,dive"`
}

type ScheduleInstallment struct {
	Amount      int64  `json:"amount" validate:"min=1"`
	DueDate     string `json:"due_date,omitempty"`
	Description string `json:"description,omitempty"`
}

type RecordPaymentRequest struct {
	Amount          int64  `json:"amount" validate:"min=1"`
	PaymentMethod   string `json:"payment_method" validate:"required,oneof=transfer_bank tunai qris kartu_kredit e_wallet"`
	BankName        string `json:"bank_name,omitempty"`
	AccountNumber   string `json:"account_number,omitempty"`
	ReferenceNumber string `json:"reference_number,omitempty"`
	ProofURL        string `json:"proof_url,omitempty"`
	Notes           string `json:"notes,omitempty"`
	PaidAt          string `json:"paid_at,omitempty"`
}

type InvoiceSummary struct {
	TotalInvoices   int64 `json:"total_invoices"`
	TotalAmount     int64 `json:"total_amount"`
	TotalPaid       int64 `json:"total_paid"`
	TotalRemaining  int64 `json:"total_remaining"`
	OutstandingCount int64 `json:"outstanding_count"`
	OverdueCount    int64 `json:"overdue_count"`
}
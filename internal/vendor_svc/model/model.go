package model

import (
	"time"

	"github.com/google/uuid"
)

func ValidVendorTypes() []string {
	return []string{"maskapai", "hotel", "transport", "perlengkapan", "katering", "lainnya"}
}

func ValidBillStatuses() []string {
	return []string{"belum_bayar", "sebagian", "lunas"}
}

type Vendor struct {
	ID                uuid.UUID  `json:"id" db:"id"`
	OrgID             uuid.UUID  `json:"org_id" db:"org_id"`
	Name              string     `json:"name" db:"name"`
	Type              string     `json:"type" db:"type"`
	NPWP              *string    `json:"npwp,omitempty" db:"npwp"`
	Address           *string    `json:"address,omitempty" db:"address"`
	PICName           *string    `json:"pic_name,omitempty" db:"pic_name"`
	PICPhone          *string    `json:"pic_phone,omitempty" db:"pic_phone"`
	PICEmail          *string    `json:"pic_email,omitempty" db:"pic_email"`
	BankName          *string    `json:"bank_name,omitempty" db:"bank_name"`
	BankAccountNumber *string    `json:"bank_account_number,omitempty" db:"bank_account_number"`
	BankAccountName   *string    `json:"bank_account_name,omitempty" db:"bank_account_name"`
	Notes             *string    `json:"notes,omitempty" db:"notes"`
	CreatedAt         time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt         time.Time  `json:"updated_at" db:"updated_at"`
}

type CreateVendorRequest struct {
	Name              string `json:"name" validate:"required"`
	Type              string `json:"type" validate:"required"`
	NPWP              string `json:"npwp,omitempty"`
	Address           string `json:"address,omitempty"`
	PICName           string `json:"pic_name,omitempty"`
	PICPhone          string `json:"pic_phone,omitempty"`
	PICEmail          string `json:"pic_email,omitempty"`
	BankName          string `json:"bank_name,omitempty"`
	BankAccountNumber string `json:"bank_account_number,omitempty"`
	BankAccountName   string `json:"bank_account_name,omitempty"`
	Notes             string `json:"notes,omitempty"`
}

type UpdateVendorRequest struct {
	Name              *string `json:"name,omitempty"`
	Type              *string `json:"type,omitempty"`
	NPWP              *string `json:"npwp,omitempty"`
	Address           *string `json:"address,omitempty"`
	PICName           *string `json:"pic_name,omitempty"`
	PICPhone          *string `json:"pic_phone,omitempty"`
	PICEmail          *string `json:"pic_email,omitempty"`
	BankName          *string `json:"bank_name,omitempty"`
	BankAccountNumber *string `json:"bank_account_number,omitempty"`
	BankAccountName   *string `json:"bank_account_name,omitempty"`
	Notes             *string `json:"notes,omitempty"`
}

type VendorBill struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	OrgID        uuid.UUID  `json:"org_id" db:"org_id"`
	VendorID     uuid.UUID  `json:"vendor_id" db:"vendor_id"`
	PackageID    uuid.UUID  `json:"package_id" db:"package_id"`
	Description  string     `json:"description" db:"description"`
	Amount       int64      `json:"amount" db:"amount"`
	Currency     string     `json:"currency" db:"currency"`
	ExchangeRate float64    `json:"exchange_rate" db:"exchange_rate"`
	AmountIDR    int64      `json:"amount_idr" db:"amount_idr"`
	PaidAmount   int64      `json:"paid_amount" db:"paid_amount"`
	DueDate      *time.Time `json:"due_date,omitempty" db:"due_date"`
	Status       string     `json:"status" db:"status"`
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`

	VendorName *string `json:"vendor_name,omitempty" db:"vendor_name"`
}

type CreateBillRequest struct {
	VendorID     uuid.UUID `json:"vendor_id" validate:"required"`
	PackageID    uuid.UUID `json:"package_id" validate:"required"`
	Description  string    `json:"description" validate:"required"`
	Amount       int64     `json:"amount" validate:"min=1"`
	Currency     string    `json:"currency,omitempty"`
	ExchangeRate float64   `json:"exchange_rate,omitempty"`
	DueDate      string    `json:"due_date,omitempty"`
}

type UpdateBillRequest struct {
	Description  *string `json:"description,omitempty"`
	Amount       *int64  `json:"amount,omitempty"`
	Currency     *string `json:"currency,omitempty"`
	ExchangeRate *float64 `json:"exchange_rate,omitempty"`
	DueDate      *string  `json:"due_date,omitempty"`
	Status       *string  `json:"status,omitempty"`
}

type VendorPayment struct {
	ID               uuid.UUID `json:"id" db:"id"`
	OrgID            uuid.UUID `json:"org_id" db:"org_id"`
	VendorBillID     uuid.UUID `json:"vendor_bill_id" db:"vendor_bill_id"`
	VendorID         uuid.UUID `json:"vendor_id" db:"vendor_id"`
	PaymentDate      time.Time `json:"payment_date" db:"payment_date"`
	Amount           int64     `json:"amount" db:"amount"`
	Currency         string    `json:"currency" db:"currency"`
	ExchangeRate     float64   `json:"exchange_rate" db:"exchange_rate"`
	AmountIDR        int64     `json:"amount_idr" db:"amount_idr"`
	SourceAccount    *string   `json:"source_account,omitempty" db:"source_account"`
	TransferProofURL *string   `json:"transfer_proof_url,omitempty" db:"transfer_proof_url"`
	Notes            *string   `json:"notes,omitempty" db:"notes"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
}

type CreatePaymentRequest struct {
	VendorBillID     uuid.UUID `json:"vendor_bill_id" validate:"required"`
	PaymentDate      string    `json:"payment_date" validate:"required"`
	Amount           int64     `json:"amount" validate:"min=1"`
	Currency         string    `json:"currency,omitempty"`
	ExchangeRate     float64   `json:"exchange_rate,omitempty"`
	SourceAccount    string    `json:"source_account,omitempty"`
	TransferProofURL string    `json:"transfer_proof_url,omitempty"`
	Notes            string    `json:"notes,omitempty"`
}

type VendorDebtSummary struct {
	TotalBills     int64 `json:"total_bills"`
	TotalAmountIDR int64 `json:"total_amount_idr"`
	TotalPaidIDR   int64 `json:"total_paid_idr"`
	TotalOutstandingIDR int64 `json:"total_outstanding_idr"`
	ByStatus map[string]BillStatusSummary `json:"by_status"`
}

type BillStatusSummary struct {
	Count       int   `json:"count"`
	TotalAmount int64 `json:"total_amount"`
}
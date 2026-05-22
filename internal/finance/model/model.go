package model

import (
	"time"

	"github.com/google/uuid"
)

type ExpenseCategory string

const (
	CategoryTransport  ExpenseCategory = "transport"
	CategoryAccommodation ExpenseCategory = "accommodation"
	CategoryVisa       ExpenseCategory = "visa"
	CategoryInsurance  ExpenseCategory = "insurance"
	CategoryMeals      ExpenseCategory = "meals"
	CategoryGuides     ExpenseCategory = "guides"
	CategoryOthers     ExpenseCategory = "other"
)

func ValidExpenseCategories() []string {
	return []string{"transport", "accommodation", "visa", "insurance", "meals", "guides", "other"}
}

func ValidExpenseStatuses() []string {
	return []string{"belum_bayar", "sebagian", "lunas"}
}

type TripExpense struct {
	ID            uuid.UUID      `json:"id" db:"id"`
	OrgID         uuid.UUID      `json:"org_id" db:"org_id"`
	PackageID     uuid.UUID      `json:"package_id" db:"package_id"`
	Category      string         `json:"category" db:"category"`
	Description   string         `json:"description" db:"description"`
	VendorName    *string   `json:"vendor_name,omitempty" db:"vendor_name"`
	Amount        int64          `json:"amount" db:"amount"`
	Currency      string         `json:"currency" db:"currency"`
	ExchangeRate  float64        `json:"exchange_rate" db:"exchange_rate"`
	AmountIDR     int64          `json:"amount_idr" db:"amount_idr"`
	ExpenseDate   time.Time      `json:"expense_date" db:"expense_date"`
	DueDate       *time.Time     `json:"due_date,omitempty" db:"due_date"`
	Status        string         `json:"status" db:"status"`
	CreatedAt     time.Time      `json:"created_at" db:"created_at"`
	UpdatedAt     time.Time      `json:"updated_at" db:"updated_at"`
}

type CreateExpenseRequest struct {
	PackageID    uuid.UUID `json:"package_id" validate:"required"`
	Category     string    `json:"category" validate:"required"`
	Description  string    `json:"description" validate:"required"`
	VendorName   string    `json:"vendor_name,omitempty"`
	Amount       int64     `json:"amount" validate:"min=1"`
	Currency     string    `json:"currency,omitempty"`
	ExchangeRate float64   `json:"exchange_rate,omitempty"`
	ExpenseDate  string    `json:"expense_date" validate:"required"`
	DueDate      string    `json:"due_date,omitempty"`
	Status       string    `json:"status,omitempty"`
}

type UpdateExpenseRequest struct {
	Category     *string  `json:"category,omitempty"`
	Description  *string  `json:"description,omitempty"`
	VendorName   *string  `json:"vendor_name,omitempty"`
	Amount       *int64   `json:"amount,omitempty"`
	Currency     *string  `json:"currency,omitempty"`
	ExchangeRate *float64 `json:"exchange_rate,omitempty"`
	ExpenseDate  *string  `json:"expense_date,omitempty"`
	DueDate      *string  `json:"due_date,omitempty"`
	Status       *string  `json:"status,omitempty"`
}

type ExpenseSummary struct {
	TotalExpenses  int64                       `json:"total_expenses"`
	TotalAmountIDR int64                       `json:"total_amount_idr"`
	ByCategory     map[string]CategorySummary  `json:"by_category"`
	ByStatus       map[string]int64            `json:"by_status"`
}

type CategorySummary struct {
	Count       int   `json:"count"`
	TotalAmount int64 `json:"total_amount"`
}
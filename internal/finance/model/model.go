package model

import (
	"time"

	"github.com/google/uuid"
)

type ExpenseCategory string

const (
	CategoryFlight        ExpenseCategory = "flight"
	CategoryHotelMakkah   ExpenseCategory = "hotel_makkah"
	CategoryHotelMadinah  ExpenseCategory = "hotel_madinah"
	CategoryTransport     ExpenseCategory = "transport"
	CategoryAccommodation ExpenseCategory = "accommodation"
	CategoryVisa          ExpenseCategory = "visa"
	CategoryInsurance     ExpenseCategory = "insurance"
	CategoryMeals         ExpenseCategory = "meals"
	CategoryGuides        ExpenseCategory = "guides"
	CategoryGuide         ExpenseCategory = "guide"
	CategoryEquipment     ExpenseCategory = "equipment"
	CategoryCatering      ExpenseCategory = "catering"
	CategoryOthers        ExpenseCategory = "other"
)

func ValidExpenseCategories() []string {
	return []string{
		"flight",
		"hotel_makkah",
		"hotel_madinah",
		"transport",
		"accommodation",
		"visa",
		"insurance",
		"meals",
		"guides",
		"guide",
		"equipment",
		"catering",
		"other",
	}
}

func ValidExpenseStatuses() []string {
	return []string{"belum_bayar", "sebagian", "lunas"}
}

type TripExpense struct {
	ID           uuid.UUID  `json:"id" db:"id"`
	OrgID        uuid.UUID  `json:"org_id" db:"org_id"`
	PackageID    uuid.UUID  `json:"package_id" db:"package_id"`
	Category     string     `json:"category" db:"category"`
	Description  string     `json:"description" db:"description"`
	VendorName   *string    `json:"vendor_name,omitempty" db:"vendor_name"`
	Amount       int64      `json:"amount" db:"amount"`
	Currency     string     `json:"currency" db:"currency"`
	ExchangeRate float64    `json:"exchange_rate" db:"exchange_rate"`
	AmountIDR    int64      `json:"amount_idr" db:"amount_idr"`
	ExpenseDate  time.Time  `json:"expense_date" db:"expense_date"`
	DueDate      *time.Time `json:"due_date,omitempty" db:"due_date"`
	Status       string     `json:"status" db:"status"`
	CreatedAt    time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time  `json:"updated_at" db:"updated_at"`
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
	TotalExpenses  int64                      `json:"total_expenses"`
	TotalAmountIDR int64                      `json:"total_amount_idr"`
	ByCategory     map[string]CategorySummary `json:"by_category"`
	ByStatus       map[string]int64           `json:"by_status"`
}

type CategorySummary struct {
	Count       int   `json:"count"`
	TotalAmount int64 `json:"total_amount"`
}

type PackagePnL struct {
	PackageID          uuid.UUID          `json:"package_id"`
	PackageName        string             `json:"package_name"`
	TotalSeats         int                `json:"total_seats"`
	ReservedSeats      int                `json:"reserved_seats"`
	Revenue            *RevenueSummary    `json:"revenue"`
	OperatingExpenses  *ExpenseSummary    `json:"operating_expenses"`
	VendorCosts        *VendorCostSummary `json:"vendor_costs"`
	Projected          *ProjectedPnL      `json:"projected"`
	Actual             *ActualPnL         `json:"actual"`
	CostBreakdown      []CostBreakdown    `json:"cost_breakdown,omitempty"`
	DataNotes          []string           `json:"data_notes,omitempty"`
	TotalRevenue       int64              `json:"total_revenue"`
	TotalOpExpenses    int64              `json:"total_op_expenses"`
	TotalVendorCosts   int64              `json:"total_vendor_costs"`
	GrossProfit        int64              `json:"gross_profit"`
	NetProfit          int64              `json:"net_profit"`
	RevenueCollected   int64              `json:"revenue_collected"`
	RevenueOutstanding int64              `json:"revenue_outstanding"`
	VendorPaidOut      int64              `json:"vendor_paid_out"`
	VendorOutstanding  int64              `json:"vendor_outstanding"`
	CashFlow           int64              `json:"cash_flow"`
}

type ProjectedPnL struct {
	LowestPrice              int64   `json:"lowest_price"`
	HppPerPerson             int64   `json:"hpp_per_person"`
	ProjectedMarginPerPerson int64   `json:"projected_margin_per_person"`
	Revenue                  int64   `json:"revenue"`
	Expense                  int64   `json:"expense"`
	Profit                   int64   `json:"profit"`
	MarginPercent            float64 `json:"margin_percent"`
}

type ActualPnL struct {
	Revenue       int64   `json:"revenue"`
	Expense       int64   `json:"expense"`
	Profit        int64   `json:"profit"`
	MarginPercent float64 `json:"margin_percent"`
}

type CostBreakdown struct {
	Category        string `json:"category"`
	Label           string `json:"label"`
	ProjectedAmount int64  `json:"projected_amount"`
	ActualAmount    int64  `json:"actual_amount"`
	VarianceAmount  int64  `json:"variance_amount"`
}

type RevenueSummary struct {
	TotalInvoices   int   `json:"total_invoices"`
	TotalBilled     int64 `json:"total_amount"` // invoice API returns "total_amount"
	TotalPaid       int64 `json:"total_paid"`
	TotalRemaining  int64 `json:"total_remaining"`
	LunasCount      int   `json:"lunas_count"`
	SebagianCount   int   `json:"sebagian_count"`
	BelumBayarCount int   `json:"belum_bayar_count"`
	BatalCount      int   `json:"batal_count"`
}

type VendorCostSummary struct {
	TotalBills          int64                       `json:"total_bills"`
	TotalAmountIDR      int64                       `json:"total_amount_idr"`
	TotalPaidIDR        int64                       `json:"total_paid_idr"`
	TotalOutstandingIDR int64                       `json:"total_outstanding_idr"`
	ByStatus            map[string]BillStatusDetail `json:"by_status"`
}

type BillStatusDetail struct {
	Count       int   `json:"count"`
	TotalAmount int64 `json:"total_amount"`
}

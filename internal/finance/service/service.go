package service

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/finance/model"
	"github.com/jamaah-in/v2/internal/finance/repository"
)

type FinanceService struct {
	repo        *repository.FinanceRepo
	invoiceAddr string
	vendorAddr  string
	packageAddr string
	httpClient  *http.Client
}

func NewFinanceService(repo *repository.FinanceRepo, invoiceAddr, vendorAddr, packageAddr string) *FinanceService {
	return &FinanceService{
		repo:        repo,
		invoiceAddr: invoiceAddr,
		vendorAddr:  vendorAddr,
		packageAddr: packageAddr,
		httpClient: &http.Client{
			Timeout: 10 * time.Second,
		},
	}
}

func (s *FinanceService) CreateExpense(ctx context.Context, orgID uuid.UUID, req model.CreateExpenseRequest) (*model.TripExpense, error) {
	if req.Currency == "" {
		req.Currency = "IDR"
	}
	if req.ExchangeRate == 0 {
		req.ExchangeRate = 1.0
	}
	if req.Status == "" {
		req.Status = "belum_bayar"
	}

	expenseDate, err := repository.ParseDate(req.ExpenseDate)
	if err != nil {
		return nil, err
	}
	if expenseDate == nil {
		return nil, fmt.Errorf("expense_date is required")
	}

	var dueDate *time.Time
	if req.DueDate != "" {
		dueDate, err = repository.ParseDate(req.DueDate)
		if err != nil {
			return nil, err
		}
	}

	e := &model.TripExpense{
		ID:           uuid.New(),
		OrgID:        orgID,
		PackageID:    req.PackageID,
		Category:     req.Category,
		Description:  req.Description,
		VendorName:   strPtr(req.VendorName),
		Amount:       req.Amount,
		Currency:     req.Currency,
		ExchangeRate: req.ExchangeRate,
		AmountIDR:    int64(float64(req.Amount) * req.ExchangeRate),
		ExpenseDate:  *expenseDate,
		DueDate:      dueDate,
		Status:       req.Status,
	}

	if err := s.repo.CreateExpense(ctx, e); err != nil {
		return nil, err
	}
	return e, nil
}

func (s *FinanceService) GetExpense(ctx context.Context, id, orgID uuid.UUID) (*model.TripExpense, error) {
	return s.repo.GetExpenseByID(ctx, id, orgID)
}

func (s *FinanceService) UpdateExpense(ctx context.Context, id, orgID uuid.UUID, req model.UpdateExpenseRequest) (*model.TripExpense, error) {
	e, err := s.repo.GetExpenseByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}

	if req.Category != nil {
		e.Category = *req.Category
	}
	if req.Description != nil {
		e.Description = *req.Description
	}
	if req.VendorName != nil {
		e.VendorName = req.VendorName
	}
	if req.Amount != nil {
		e.Amount = *req.Amount
	}
	if req.Currency != nil {
		e.Currency = *req.Currency
	}
	if req.ExchangeRate != nil {
		e.ExchangeRate = *req.ExchangeRate
	}
	if req.ExpenseDate != nil {
		t, err := repository.ParseDate(*req.ExpenseDate)
		if err != nil {
			return nil, err
		}
		if t != nil {
			e.ExpenseDate = *t
		}
	}
	if req.DueDate != nil {
		if *req.DueDate == "" {
			e.DueDate = nil
		} else {
			t, err := repository.ParseDate(*req.DueDate)
			if err != nil {
				return nil, err
			}
			e.DueDate = t
		}
	}
	if req.Status != nil {
		e.Status = *req.Status
	}

	e.AmountIDR = int64(float64(e.Amount) * e.ExchangeRate)

	if err := s.repo.UpdateExpense(ctx, e); err != nil {
		return nil, err
	}
	return s.repo.GetExpenseByID(ctx, id, orgID)
}

func (s *FinanceService) DeleteExpense(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.DeleteExpense(ctx, id, orgID)
}

func (s *FinanceService) ListExpenses(ctx context.Context, orgID uuid.UUID, category, status string, page, limit int) ([]model.TripExpense, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListExpenses(ctx, orgID, category, status, offset, limit)
}

func (s *FinanceService) ListExpensesByPackage(ctx context.Context, orgID, packageID uuid.UUID) ([]model.TripExpense, error) {
	return s.repo.ListExpensesByPackage(ctx, orgID, packageID)
}

func (s *FinanceService) GetSummary(ctx context.Context, orgID uuid.UUID, packageID *uuid.UUID) (*model.ExpenseSummary, error) {
	return s.repo.GetSummary(ctx, orgID, packageID)
}

func (s *FinanceService) GetOverdueExpenses(ctx context.Context, orgID uuid.UUID) ([]model.TripExpense, error) {
	return s.repo.GetOverdueExpenses(ctx, orgID)
}

// --- P&L Aggregation ---

type apiResponse struct {
	Success bool            `json:"success"`
	Data    json.RawMessage `json:"data"`
}

type packageSnapshot struct {
	ID             uuid.UUID              `json:"id"`
	Name           string                 `json:"name"`
	TotalSeats     int                    `json:"total_seats"`
	ReservedSeats  int                    `json:"reserved_seats"`
	PricingTiers   []packagePricingTier   `json:"pricing_tiers"`
	CostComponents []packageCostComponent `json:"cost_components"`
}

type packagePricingTier struct {
	RoomType string `json:"room_type"`
	Price    int64  `json:"price"`
}

type packageCostComponent struct {
	Category        string `json:"category"`
	AmountPerPerson int64  `json:"amount_per_person"`
	Quantity        int    `json:"quantity"`
	TotalAmount     int64  `json:"total_amount"`
}

type vendorBillList struct {
	Items []vendorBillListItem
}

type vendorBillListItem struct {
	Description string  `json:"description"`
	AmountIDR   int64   `json:"amount_idr"`
	VendorType  *string `json:"vendor_type"`
}

func (s *FinanceService) GetPnL(ctx context.Context, orgID, packageID uuid.UUID, authToken string) (*model.PackagePnL, error) {
	pnl := &model.PackagePnL{
		PackageID: packageID,
	}

	pkg, err := s.fetchPackageSnapshot(ctx, packageID, authToken)
	if err != nil {
		return nil, fmt.Errorf("get package snapshot: %w", err)
	}
	pnl.PackageName = pkg.Name
	pnl.TotalSeats = pkg.TotalSeats
	pnl.ReservedSeats = pkg.ReservedSeats

	expenseSummary, err := s.repo.GetSummary(ctx, orgID, &packageID)
	if err != nil {
		return nil, fmt.Errorf("get expense summary: %w", err)
	}
	pnl.OperatingExpenses = expenseSummary
	pnl.TotalOpExpenses = expenseSummary.TotalAmountIDR
	expenses, err := s.repo.ListExpensesByPackage(ctx, orgID, packageID)
	if err != nil {
		return nil, fmt.Errorf("list expenses by package: %w", err)
	}

	invoiceData, err := s.fetchFromService(ctx, s.invoiceAddr, fmt.Sprintf("/api/v1/invoices/package/%s/revenue", packageID), authToken)
	if err == nil {
		var rev model.RevenueSummary
		if err := json.Unmarshal(invoiceData, &rev); err == nil {
			pnl.Revenue = &rev
			pnl.TotalRevenue = rev.TotalBilled
			pnl.RevenueCollected = rev.TotalPaid
			pnl.RevenueOutstanding = rev.TotalRemaining
		}
	}

	vendorSummaryData, err := s.fetchFromService(ctx, s.vendorAddr, fmt.Sprintf("/api/v1/vendors/bills/package/%s", packageID), authToken)
	if err == nil {
		var vcs model.VendorCostSummary
		if err := json.Unmarshal(vendorSummaryData, &vcs); err == nil {
			pnl.VendorCosts = &vcs
			pnl.TotalVendorCosts = vcs.TotalAmountIDR
			pnl.VendorPaidOut = vcs.TotalPaidIDR
			pnl.VendorOutstanding = vcs.TotalOutstandingIDR
		}
	}

	projectedRevenue, lowestPrice := projectedRevenue(pkg)
	hppPerPerson := sumProjectedPerPerson(pkg)
	projectedCategories, projectedExpense := projectedCategoryTotals(pkg)
	pnl.Projected = &model.ProjectedPnL{
		LowestPrice:              lowestPrice,
		HppPerPerson:             hppPerPerson,
		ProjectedMarginPerPerson: lowestPrice - hppPerPerson,
		Revenue:                  projectedRevenue,
		Expense:                  projectedExpense,
		Profit:                   projectedRevenue - projectedExpense,
		MarginPercent:            marginPercent(projectedRevenue-projectedExpense, projectedRevenue),
	}

	actualCategories := expenseCategoryTotals(expenses)

	vendorBills, err := s.fetchVendorBillList(ctx, packageID, authToken)
	if err == nil {
		for _, bill := range vendorBills {
			key := normalizeVendorBillCategory(bill)
			actualCategories[key] += bill.AmountIDR
		}
	}

	actualExpense := sumCategoryTotals(actualCategories)
	pnl.Actual = &model.ActualPnL{
		Revenue:       pnl.TotalRevenue,
		Expense:       actualExpense,
		Profit:        pnl.TotalRevenue - actualExpense,
		MarginPercent: marginPercent(pnl.TotalRevenue-actualExpense, pnl.TotalRevenue),
	}

	pnl.CostBreakdown = buildCostBreakdown(projectedCategories, actualCategories)
	if pnl.Revenue != nil {
		pnl.GrossProfit = pnl.TotalRevenue - actualExpense
		pnl.NetProfit = pnl.GrossProfit
		pnl.CashFlow = pnl.RevenueCollected - pnl.VendorPaidOut - pnl.TotalOpExpenses
	}

	pnl.DataNotes = []string{
		"equipment: reflects vendor procurement cost (perlengkapan bills); distributed inventory HPP requires the inventory module (Phase 3.3)",
		"cost_breakdown: vendor bill category detail is sampled up to 500 bills; summary totals are always exact",
	}

	return pnl, nil
}

func (s *FinanceService) fetchPackageSnapshot(ctx context.Context, packageID uuid.UUID, authToken string) (*packageSnapshot, error) {
	data, err := s.fetchFromService(ctx, s.packageAddr, fmt.Sprintf("/api/v1/packages/%s", packageID), authToken)
	if err != nil {
		return nil, err
	}
	var pkg packageSnapshot
	if err := json.Unmarshal(data, &pkg); err != nil {
		return nil, err
	}
	return &pkg, nil
}

func (s *FinanceService) fetchVendorBillList(ctx context.Context, packageID uuid.UUID, authToken string) ([]vendorBillListItem, error) {
	data, err := s.fetchFromService(ctx, s.vendorAddr, fmt.Sprintf("/api/v1/vendors/bills?package_id=%s&page=1&page_size=500", packageID), authToken)
	if err != nil {
		return nil, err
	}
	var bills []vendorBillListItem
	if err := json.Unmarshal(data, &bills); err == nil {
		return bills, nil
	}
	var wrapped vendorBillList
	if err := json.Unmarshal(data, &wrapped); err != nil {
		return nil, err
	}
	return wrapped.Items, nil
}

func projectedRevenue(pkg *packageSnapshot) (int64, int64) {
	lowest := int64(0)
	for i, tier := range pkg.PricingTiers {
		if i == 0 || tier.Price < lowest {
			lowest = tier.Price
		}
	}
	return lowest * int64(pkg.TotalSeats), lowest
}

func projectedCategoryTotals(pkg *packageSnapshot) (map[string]int64, int64) {
	out := make(map[string]int64)
	var total int64
	for _, component := range pkg.CostComponents {
		key := normalizeProjectedCategory(component.Category)
		perPersonAmount := component.TotalAmount
		if perPersonAmount == 0 {
			perPersonAmount = component.AmountPerPerson * int64(component.Quantity)
		}
		tripAmount := perPersonAmount * int64(pkg.TotalSeats)
		out[key] += tripAmount
		total += tripAmount
	}
	return out, total
}

func sumProjectedPerPerson(pkg *packageSnapshot) int64 {
	var total int64
	for _, component := range pkg.CostComponents {
		perPersonAmount := component.TotalAmount
		if perPersonAmount == 0 {
			perPersonAmount = component.AmountPerPerson * int64(component.Quantity)
		}
		total += perPersonAmount
	}
	return total
}

func expenseCategoryTotals(expenses []model.TripExpense) map[string]int64 {
	out := make(map[string]int64)
	for _, expense := range expenses {
		out[normalizeExpenseCategory(expense)] += expense.AmountIDR
	}
	return out
}

func sumCategoryTotals(categories map[string]int64) int64 {
	var total int64
	for _, amount := range categories {
		total += amount
	}
	return total
}

func buildCostBreakdown(projected, actual map[string]int64) []model.CostBreakdown {
	order := []string{"flight", "hotel_makkah", "hotel_madinah", "visa", "transport", "guide", "equipment", "catering", "other"}
	rows := make([]model.CostBreakdown, 0, len(order))
	for _, category := range order {
		projectedAmount := projected[category]
		actualAmount := actual[category]
		if projectedAmount == 0 && actualAmount == 0 {
			continue
		}
		rows = append(rows, model.CostBreakdown{
			Category:        category,
			Label:           categoryLabel(category),
			ProjectedAmount: projectedAmount,
			ActualAmount:    actualAmount,
			VarianceAmount:  actualAmount - projectedAmount,
		})
	}
	return rows
}

func normalizeProjectedCategory(category string) string {
	switch strings.ToLower(strings.TrimSpace(category)) {
	case "flight":
		return "flight"
	case "hotel_makkah":
		return "hotel_makkah"
	case "hotel_madinah":
		return "hotel_madinah"
	case "visa":
		return "visa"
	case "transport":
		return "transport"
	case "guide", "guides":
		return "guide"
	case "equipment":
		return "equipment"
	case "catering":
		return "catering"
	default:
		return "other"
	}
}

func normalizeExpenseCategory(expense model.TripExpense) string {
	switch strings.ToLower(strings.TrimSpace(expense.Category)) {
	case "flight":
		return "flight"
	case "hotel_makkah":
		return "hotel_makkah"
	case "hotel_madinah":
		return "hotel_madinah"
	case "accommodation":
		return normalizeHotelCategory(expense.Description)
	case "visa":
		return "visa"
	case "transport":
		return "transport"
	case "guide", "guides":
		return "guide"
	case "equipment":
		return "equipment"
	case "catering", "meals":
		return "catering"
	default:
		return "other"
	}
}

func normalizeVendorBillCategory(bill vendorBillListItem) string {
	if bill.VendorType != nil {
		switch strings.ToLower(strings.TrimSpace(*bill.VendorType)) {
		case "maskapai":
			return "flight"
		case "hotel":
			return normalizeHotelCategory(bill.Description)
		case "transport":
			return "transport"
		case "perlengkapan":
			return "equipment"
		case "katering":
			return "catering"
		default:
			return "other"
		}
	}
	return "other"
}

func normalizeHotelCategory(description string) string {
	desc := strings.ToLower(description)
	switch {
	case strings.Contains(desc, "madinah"):
		return "hotel_madinah"
	case strings.Contains(desc, "makkah"), strings.Contains(desc, "mekkah"), strings.Contains(desc, "mecca"):
		return "hotel_makkah"
	default:
		return "other"
	}
}

func categoryLabel(category string) string {
	switch category {
	case "flight":
		return "Tiket Pesawat"
	case "hotel_makkah":
		return "Hotel Makkah"
	case "hotel_madinah":
		return "Hotel Madinah"
	case "visa":
		return "Visa"
	case "transport":
		return "Transportasi"
	case "guide":
		return "Muthawwif / Guide"
	case "equipment":
		return "Perlengkapan"
	case "catering":
		return "Katering"
	default:
		return "Lain-lain"
	}
}

func marginPercent(profit, revenue int64) float64 {
	if revenue <= 0 {
		return 0
	}
	return float64(profit) * 100 / float64(revenue)
}

func (s *FinanceService) fetchFromService(ctx context.Context, addr, path, authToken string) (json.RawMessage, error) {
	url := "http://" + addr + path
	req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
	if err != nil {
		return nil, err
	}
	if authToken != "" {
		req.Header.Set("Authorization", authToken)
	}

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("service returned status %d: %s", resp.StatusCode, string(body))
	}

	var apiResp apiResponse
	if err := json.Unmarshal(body, &apiResp); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w", err)
	}

	if !apiResp.Success {
		return nil, fmt.Errorf("service returned error: %s", string(apiResp.Data))
	}

	return apiResp.Data, nil
}

func strPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

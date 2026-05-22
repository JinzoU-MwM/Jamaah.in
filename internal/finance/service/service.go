package service

import (
	"context"
	"time"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/finance/model"
	"github.com/jamaah-in/v2/internal/finance/repository"
)

type FinanceService struct {
	repo *repository.FinanceRepo
}

func NewFinanceService(repo *repository.FinanceRepo) *FinanceService {
	return &FinanceService{repo: repo}
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
		return nil, err
	}

	var dueDate *time.Time
	if req.DueDate != "" {
		dueDate, err = repository.ParseDate(req.DueDate)
		if err != nil {
			return nil, err
		}
	}

	amountIDR := int64(float64(req.Amount) * req.ExchangeRate)

	e := &model.TripExpense{
		ID:            uuid.New(),
		OrgID:         orgID,
		PackageID:     req.PackageID,
		Category:      req.Category,
		Description:   req.Description,
		VendorName:    strPtr(req.VendorName),
		Amount:        req.Amount,
		Currency:      req.Currency,
		ExchangeRate:  req.ExchangeRate,
		AmountIDR:     amountIDR,
		ExpenseDate:   *expenseDate,
		DueDate:       dueDate,
		Status:        req.Status,
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

func strPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

func (s *FinanceService) GetOverdueExpenses(ctx context.Context, orgID uuid.UUID) ([]model.TripExpense, error) {
	return s.repo.GetOverdueExpenses(ctx, orgID)
}
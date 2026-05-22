package service

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/invoice/model"
	"github.com/jamaah-in/v2/internal/invoice/repository"
)

type InvoiceService struct {
	repo *repository.InvoiceRepo
}

func NewInvoiceService(repo *repository.InvoiceRepo) *InvoiceService {
	return &InvoiceService{repo: repo}
}

func (s *InvoiceService) CreateInvoice(ctx context.Context, orgID, userID uuid.UUID, req model.CreateInvoiceRequest) (*model.Invoice, error) {
	totalAmount := req.PriceSnapshot - req.DiscountAmount + req.SurchargeAmount
	if totalAmount < 0 {
		totalAmount = 0
	}

	inv := &model.Invoice{
		ID:              uuid.New(),
		OrgID:           orgID,
		InvoiceNumber:   repository.GenerateInvoiceNumber(orgID),
		JamaahID:        req.JamaahID,
		PackageID:       req.PackageID,
		RegistrationID:  req.RegistrationID,
		RoomType:         req.RoomType,
		PriceSnapshot:   req.PriceSnapshot,
		DiscountAmount:  req.DiscountAmount,
		SurchargeAmount: req.SurchargeAmount,
		TotalAmount:     totalAmount,
		AmountPaid:      0,
		AmountRemaining: totalAmount,
		PaymentScheme:   req.PaymentScheme,
		Status:          string(model.InvoiceStatusBelumBayar),
		Notes:           req.Notes,
	}

	if req.DueDate != "" {
		t, err := parseDate(req.DueDate)
		if err != nil {
			return nil, fmt.Errorf("due_date: %w", err)
		}
		inv.DueDate = t
	}

	if err := s.repo.CreateInvoice(ctx, inv); err != nil {
		return nil, err
	}
	return inv, nil
}

func (s *InvoiceService) GetInvoice(ctx context.Context, id, orgID uuid.UUID) (*model.Invoice, error) {
	inv, err := s.repo.GetInvoiceByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}
	schedules, _ := s.repo.GetPaymentSchedules(ctx, id)
	payments, _ := s.repo.GetPayments(ctx, id)
	inv.PaymentSchedules = schedules
	inv.Payments = payments
	return inv, nil
}

func (s *InvoiceService) GetInvoiceByNumber(ctx context.Context, orgID uuid.UUID, number string) (*model.Invoice, error) {
	inv, err := s.repo.GetInvoiceByNumber(ctx, orgID, number)
	if err != nil {
		return nil, err
	}
	schedules, _ := s.repo.GetPaymentSchedules(ctx, inv.ID)
	payments, _ := s.repo.GetPayments(ctx, inv.ID)
	inv.PaymentSchedules = schedules
	inv.Payments = payments
	return inv, nil
}

func (s *InvoiceService) ListInvoices(ctx context.Context, orgID uuid.UUID, status string, page, limit int) ([]model.Invoice, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListInvoices(ctx, orgID, status, offset, limit)
}

func (s *InvoiceService) GetInvoicesByJamaah(ctx context.Context, orgID, jamaahID uuid.UUID) ([]model.Invoice, error) {
	return s.repo.GetInvoicesByJamaah(ctx, orgID, jamaahID)
}

func (s *InvoiceService) UpdateInvoice(ctx context.Context, id, orgID uuid.UUID, req model.UpdateInvoiceRequest) (*model.Invoice, error) {
	inv, err := s.repo.GetInvoiceByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}
	if inv.Status == string(model.InvoiceStatusBatal) {
		return nil, repository.ErrAlreadyCancelled
	}

	if req.DiscountAmount != nil {
		inv.DiscountAmount = *req.DiscountAmount
	}
	if req.SurchargeAmount != nil {
		inv.SurchargeAmount = *req.SurchargeAmount
	}
	if req.Notes != nil {
		inv.Notes = *req.Notes
	}
	if req.DueDate != nil {
		if *req.DueDate == "" {
			inv.DueDate = nil
		} else {
			t, err := parseDate(*req.DueDate)
			if err != nil {
				return nil, fmt.Errorf("due_date: %w", err)
			}
			inv.DueDate = t
		}
	}

	inv.TotalAmount = inv.PriceSnapshot - inv.DiscountAmount + inv.SurchargeAmount
	inv.AmountRemaining = inv.TotalAmount - inv.AmountPaid
	if inv.AmountRemaining < 0 {
		inv.AmountRemaining = 0
	}

	if err := s.repo.UpdateInvoice(ctx, inv); err != nil {
		return nil, err
	}
	return s.repo.GetInvoiceByID(ctx, id, orgID)
}

func (s *InvoiceService) CancelInvoice(ctx context.Context, id, orgID uuid.UUID, reason string) error {
	return s.repo.CancelInvoice(ctx, id, orgID, reason)
}

func (s *InvoiceService) CreatePaymentSchedules(ctx context.Context, orgID, invoiceID uuid.UUID, req model.CreatePaymentScheduleRequest) ([]model.PaymentSchedule, error) {
	inv, err := s.repo.GetInvoiceByID(ctx, invoiceID, orgID)
	if err != nil {
		return nil, err
	}
	if inv.Status == string(model.InvoiceStatusBatal) {
		return nil, repository.ErrAlreadyCancelled
	}

	totalScheduled := int64(0)
	schedules := make([]model.PaymentSchedule, 0, len(req.Installments))
	for _, inst := range req.Installments {
		totalScheduled += inst.Amount
	}

	if totalScheduled > inv.TotalAmount {
		return nil, fmt.Errorf("total scheduled amount (%d) exceeds invoice total (%d)", totalScheduled, inv.TotalAmount)
	}

	for i, inst := range req.Installments {
		ps := &model.PaymentSchedule{
			ID:             uuid.New(),
			InvoiceID:      invoiceID,
			InstallmentNum: i + 1,
			Amount:         inst.Amount,
			Description:    strPtr(inst.Description),
			IsPaid:         false,
		}
		if inst.DueDate != "" {
			t, err := parseDate(inst.DueDate)
			if err == nil {
				ps.DueDate = t
			}
		}
		if err := s.repo.CreatePaymentSchedule(ctx, ps); err != nil {
			return nil, err
		}
		schedules = append(schedules, *ps)
	}

	return schedules, nil
}

func (s *InvoiceService) GetPaymentSchedules(ctx context.Context, orgID, invoiceID uuid.UUID) ([]model.PaymentSchedule, error) {
	_, err := s.repo.GetInvoiceByID(ctx, invoiceID, orgID)
	if err != nil {
		return nil, err
	}
	return s.repo.GetPaymentSchedules(ctx, invoiceID)
}

func (s *InvoiceService) RecordPayment(ctx context.Context, orgID, userID, invoiceID uuid.UUID, req model.RecordPaymentRequest) (*model.Payment, *model.Invoice, error) {
	inv, err := s.repo.GetInvoiceByID(ctx, invoiceID, orgID)
	if err != nil {
		return nil, nil, err
	}
	if inv.Status == string(model.InvoiceStatusBatal) {
		return nil, nil, repository.ErrAlreadyCancelled
	}
	if inv.Status == string(model.InvoiceStatusLunas) {
		return nil, nil, repository.ErrAlreadyLunas
	}

	paidAt := time.Now()
	if req.PaidAt != "" {
		t, err := parseDate(req.PaidAt)
		if err == nil && t != nil {
			paidAt = *t
		}
	}

	payment := &model.Payment{
		ID:              uuid.New(),
		OrgID:           orgID,
		InvoiceID:       invoiceID,
		Amount:          req.Amount,
		PaymentMethod:   req.PaymentMethod,
		BankName:        strPtr(req.BankName),
		AccountNumber:   strPtr(req.AccountNumber),
		ReferenceNumber: strPtr(req.ReferenceNumber),
		ProofURL:        strPtr(req.ProofURL),
		Notes:           req.Notes,
		ReceivedBy:      userID,
		PaidAt:          paidAt,
	}

	if err := s.repo.CreatePayment(ctx, payment); err != nil {
		return nil, nil, err
	}

	inv.AmountPaid += req.Amount
	inv.AmountRemaining = inv.TotalAmount - inv.AmountPaid
	if inv.AmountRemaining <= 0 {
		inv.AmountRemaining = 0
		inv.Status = string(model.InvoiceStatusLunas)
	} else if inv.AmountPaid > 0 {
		inv.Status = string(model.InvoiceStatusSebagian)
	}
	if err := s.repo.UpdateInvoiceStatus(ctx, invoiceID, orgID, inv.Status); err != nil {
		return payment, nil, fmt.Errorf("update invoice status: %w", err)
	}
	if err := s.repo.UpdateInvoice(ctx, inv); err != nil {
		return payment, nil, fmt.Errorf("update invoice amounts: %w", err)
	}

	updated, err := s.repo.GetInvoiceByID(ctx, invoiceID, orgID)
	if err != nil {
		return payment, nil, nil
	}
	return payment, updated, nil
}

func (s *InvoiceService) GetPayments(ctx context.Context, orgID, invoiceID uuid.UUID) ([]model.Payment, error) {
	_, err := s.repo.GetInvoiceByID(ctx, invoiceID, orgID)
	if err != nil {
		return nil, err
	}
	return s.repo.GetPayments(ctx, invoiceID)
}

func (s *InvoiceService) GetSummary(ctx context.Context, orgID uuid.UUID) (*model.InvoiceSummary, error) {
	return s.repo.GetSummary(ctx, orgID)
}

func parseDate(s string) (*time.Time, error) {
	if s == "" {
		return nil, nil
	}
	formats := []string{"2006-01-02", "2006-01-02T15:04:05Z", "2006-01-02T15:04:05"}
	for _, f := range formats {
		if t, err := time.Parse(f, s); err == nil {
			return &t, nil
		}
	}
	return nil, fmt.Errorf("invalid date format: %s", s)
}

func strPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}
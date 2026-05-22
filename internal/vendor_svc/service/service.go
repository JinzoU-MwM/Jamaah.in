package service

import (
	"context"
	"time"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/vendor_svc/model"
	"github.com/jamaah-in/v2/internal/vendor_svc/repository"
)

type VendorService struct {
	repo *repository.VendorRepo
}

var ErrVendorNotFound = repository.ErrVendorNotFound

func NewVendorService(repo *repository.VendorRepo) *VendorService {
	return &VendorService{repo: repo}
}

// --- Vendor Master ---

func (s *VendorService) CreateVendor(ctx context.Context, orgID uuid.UUID, req model.CreateVendorRequest) (*model.Vendor, error) {
	v := &model.Vendor{
		ID:                uuid.New(),
		OrgID:             orgID,
		Name:              req.Name,
		Type:              req.Type,
		NPWP:              strPtr(req.NPWP),
		Address:           strPtr(req.Address),
		PICName:           strPtr(req.PICName),
		PICPhone:          strPtr(req.PICPhone),
		PICEmail:          strPtr(req.PICEmail),
		BankName:          strPtr(req.BankName),
		BankAccountNumber: strPtr(req.BankAccountNumber),
		BankAccountName:   strPtr(req.BankAccountName),
		Notes:             strPtr(req.Notes),
	}
	if err := s.repo.CreateVendor(ctx, v); err != nil {
		return nil, err
	}
	return v, nil
}

func (s *VendorService) GetVendor(ctx context.Context, id, orgID uuid.UUID) (*model.Vendor, error) {
	return s.repo.GetVendorByID(ctx, id, orgID)
}

func (s *VendorService) UpdateVendor(ctx context.Context, id, orgID uuid.UUID, req model.UpdateVendorRequest) (*model.Vendor, error) {
	v, err := s.repo.GetVendorByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}
	if req.Name != nil {
		v.Name = *req.Name
	}
	if req.Type != nil {
		v.Type = *req.Type
	}
	if req.NPWP != nil {
		v.NPWP = req.NPWP
	}
	if req.Address != nil {
		v.Address = req.Address
	}
	if req.PICName != nil {
		v.PICName = req.PICName
	}
	if req.PICPhone != nil {
		v.PICPhone = req.PICPhone
	}
	if req.PICEmail != nil {
		v.PICEmail = req.PICEmail
	}
	if req.BankName != nil {
		v.BankName = req.BankName
	}
	if req.BankAccountNumber != nil {
		v.BankAccountNumber = req.BankAccountNumber
	}
	if req.BankAccountName != nil {
		v.BankAccountName = req.BankAccountName
	}
	if req.Notes != nil {
		v.Notes = req.Notes
	}
	if err := s.repo.UpdateVendor(ctx, v); err != nil {
		return nil, err
	}
	return s.repo.GetVendorByID(ctx, id, orgID)
}

func (s *VendorService) DeleteVendor(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.DeleteVendor(ctx, id, orgID)
}

func (s *VendorService) ListVendors(ctx context.Context, orgID uuid.UUID, vendorType, search string, page, limit int) ([]model.Vendor, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListVendors(ctx, orgID, vendorType, search, offset, limit)
}

// --- Vendor Bills ---

func (s *VendorService) CreateBill(ctx context.Context, orgID uuid.UUID, req model.CreateBillRequest) (*model.VendorBill, error) {
	if req.Currency == "" {
		req.Currency = "IDR"
	}
	if req.ExchangeRate == 0 {
		req.ExchangeRate = 1.0
	}

	var dueDate *time.Time
	if req.DueDate != "" {
		d, err := repository.ParseDate(req.DueDate)
		if err != nil {
			return nil, err
		}
		dueDate = d
	}

	b := &model.VendorBill{
		ID:           uuid.New(),
		OrgID:        orgID,
		VendorID:     req.VendorID,
		PackageID:    req.PackageID,
		Description:  req.Description,
		Amount:       req.Amount,
		Currency:     req.Currency,
		ExchangeRate: req.ExchangeRate,
		DueDate:      dueDate,
		Status:       "belum_bayar",
	}

	if err := s.repo.CreateBill(ctx, b); err != nil {
		return nil, err
	}
	return s.repo.GetBillByID(ctx, b.ID, orgID)
}

func (s *VendorService) GetBill(ctx context.Context, id, orgID uuid.UUID) (*model.VendorBill, error) {
	return s.repo.GetBillByID(ctx, id, orgID)
}

func (s *VendorService) UpdateBill(ctx context.Context, id, orgID uuid.UUID, req model.UpdateBillRequest) (*model.VendorBill, error) {
	b, err := s.repo.GetBillByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}
	if req.Description != nil {
		b.Description = *req.Description
	}
	if req.Amount != nil {
		b.Amount = *req.Amount
	}
	if req.Currency != nil {
		b.Currency = *req.Currency
	}
	if req.ExchangeRate != nil {
		b.ExchangeRate = *req.ExchangeRate
	}
	if req.DueDate != nil {
		if *req.DueDate == "" {
			b.DueDate = nil
		} else {
			d, err := repository.ParseDate(*req.DueDate)
			if err != nil {
				return nil, err
			}
			b.DueDate = d
		}
	}
	if req.Status != nil {
		b.Status = *req.Status
	}
	if err := s.repo.UpdateBill(ctx, b); err != nil {
		return nil, err
	}
	return s.repo.GetBillByID(ctx, id, orgID)
}

func (s *VendorService) DeleteBill(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.DeleteBill(ctx, id, orgID)
}

func (s *VendorService) ListBills(ctx context.Context, orgID uuid.UUID, vendorID, packageID *uuid.UUID, status string, page, limit int) ([]model.VendorBill, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListBills(ctx, orgID, vendorID, packageID, status, offset, limit)
}

func (s *VendorService) GetOverdueBills(ctx context.Context, orgID uuid.UUID) ([]model.VendorBill, error) {
	return s.repo.GetOverdueBills(ctx, orgID)
}

func (s *VendorService) GetBillsDueSoon(ctx context.Context, orgID uuid.UUID, withinDays int) ([]model.VendorBill, error) {
	if withinDays < 1 {
		withinDays = 7
	}
	return s.repo.GetBillsDueSoon(ctx, orgID, withinDays)
}

func (s *VendorService) GetDebtSummary(ctx context.Context, orgID uuid.UUID, vendorID *uuid.UUID) (*model.VendorDebtSummary, error) {
	return s.repo.GetDebtSummary(ctx, orgID, vendorID)
}

// --- Vendor Payments ---

func (s *VendorService) CreatePayment(ctx context.Context, orgID uuid.UUID, req model.CreatePaymentRequest) (*model.VendorPayment, error) {
	bill, err := s.repo.GetBillByID(ctx, req.VendorBillID, orgID)
	if err != nil {
		return nil, err
	}

	if req.Currency == "" {
		req.Currency = "IDR"
	}
	if req.ExchangeRate == 0 {
		req.ExchangeRate = 1.0
	}

	paymentDate, err := repository.ParseDate(req.PaymentDate)
	if err != nil || paymentDate == nil {
		return nil, err
	}

	p := &model.VendorPayment{
		ID:               uuid.New(),
		OrgID:            orgID,
		VendorBillID:     req.VendorBillID,
		VendorID:         bill.VendorID,
		PaymentDate:      *paymentDate,
		Amount:           req.Amount,
		Currency:         req.Currency,
		ExchangeRate:      req.ExchangeRate,
		SourceAccount:    strPtr(req.SourceAccount),
		TransferProofURL: strPtr(req.TransferProofURL),
		Notes:            strPtr(req.Notes),
	}

	if err := s.repo.CreatePayment(ctx, p); err != nil {
		return nil, err
	}

	if err := s.repo.UpdateBillPaidAmount(ctx, bill.ID); err != nil {
		return nil, err
	}

	updatedBill, err := s.repo.GetBillByID(ctx, bill.ID, orgID)
	if err != nil {
		return p, nil
	}

	if updatedBill.PaidAmount >= updatedBill.AmountIDR {
		_ = s.repo.UpdateBillStatus(ctx, bill.ID, "lunas")
	} else if updatedBill.PaidAmount > 0 {
		_ = s.repo.UpdateBillStatus(ctx, bill.ID, "sebagian")
	}

	return p, nil
}

func (s *VendorService) GetPayment(ctx context.Context, id, orgID uuid.UUID) (*model.VendorPayment, error) {
	return s.repo.GetPaymentByID(ctx, id, orgID)
}

func (s *VendorService) DeletePayment(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.DeletePayment(ctx, id, orgID)
}

func (s *VendorService) ListPaymentsByBill(ctx context.Context, billID, orgID uuid.UUID) ([]model.VendorPayment, error) {
	return s.repo.ListPaymentsByBill(ctx, billID, orgID)
}

func (s *VendorService) ListPaymentsByVendor(ctx context.Context, vendorID, orgID uuid.UUID, page, limit int) ([]model.VendorPayment, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListPaymentsByVendor(ctx, vendorID, orgID, offset, limit)
}

func strPtr(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}
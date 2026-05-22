package handler

import (
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/vendor_svc/model"
	"github.com/jamaah-in/v2/internal/vendor_svc/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type VendorHandler struct {
	svc *service.VendorService
}

func NewVendorHandler(svc *service.VendorService) *VendorHandler {
	return &VendorHandler{svc: svc}
}

// --- Vendor Master ---

func (h *VendorHandler) CreateVendor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateVendorRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Name == "" {
		return response.BadRequest(c, "name is required")
	}
	if req.Type == "" {
		return response.BadRequest(c, "type is required")
	}
	if !isValidVendorType(req.Type) {
		return response.BadRequest(c, "type must be one of: maskapai, hotel, transport, perlengkapan, katering, lainnya")
	}

	vendor, err := h.svc.CreateVendor(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, vendor)
}

func (h *VendorHandler) GetVendor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid vendor id")
	}

	vendor, err := h.svc.GetVendor(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "vendor not found")
	}
	return response.OK(c, vendor)
}

func (h *VendorHandler) UpdateVendor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid vendor id")
	}

	var req model.UpdateVendorRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Type != nil && !isValidVendorType(*req.Type) {
		return response.BadRequest(c, "type must be one of: maskapai, hotel, transport, perlengkapan, katering, lainnya")
	}

	vendor, err := h.svc.UpdateVendor(c.Context(), id, claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, vendor)
}

func (h *VendorHandler) DeleteVendor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid vendor id")
	}
	if err := h.svc.DeleteVendor(c.Context(), id, claims.OrgID); err != nil {
		if err == service.ErrVendorNotFound {
			return response.NotFound(c, "vendor not found")
		}
		if strings.Contains(err.Error(), "foreign key") || strings.Contains(err.Error(), "violates") {
			return response.Conflict(c, "cannot delete vendor: has associated bills or payments")
		}
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, fiber.Map{"message": "vendor deleted"})
}

func (h *VendorHandler) ListVendors(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	vendorType := c.Query("type")
	search := c.Query("search")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	vendors, total, err := h.svc.ListVendors(c.Context(), claims.OrgID, vendorType, search, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, vendors, int64(total), page, limit)
}

// --- Vendor Bills ---

func (h *VendorHandler) CreateBill(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateBillRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.VendorID == uuid.Nil {
		return response.BadRequest(c, "vendor_id is required")
	}
	if req.PackageID == uuid.Nil {
		return response.BadRequest(c, "package_id is required")
	}
	if req.Description == "" {
		return response.BadRequest(c, "description is required")
	}
	if req.Amount < 1 {
		return response.BadRequest(c, "amount must be at least 1")
	}

	bill, err := h.svc.CreateBill(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, bill)
}

func (h *VendorHandler) GetBill(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid bill id")
	}

	bill, err := h.svc.GetBill(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "vendor bill not found")
	}
	return response.OK(c, bill)
}

func (h *VendorHandler) UpdateBill(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid bill id")
	}

	var req model.UpdateBillRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Status != nil && !isValidBillStatus(*req.Status) {
		return response.BadRequest(c, "status must be one of: belum_bayar, sebagian, lunas")
	}

	bill, err := h.svc.UpdateBill(c.Context(), id, claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, bill)
}

func (h *VendorHandler) DeleteBill(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid bill id")
	}
	if err := h.svc.DeleteBill(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "vendor bill not found")
	}
	return response.OK(c, fiber.Map{"message": "vendor bill deleted"})
}

func (h *VendorHandler) ListBills(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	var vendorID *uuid.UUID
	if vid := c.Query("vendor_id"); vid != "" {
		parsed, err := uuid.Parse(vid)
		if err == nil {
			vendorID = &parsed
		}
	}
	var packageID *uuid.UUID
	if pid := c.Query("package_id"); pid != "" {
		parsed, err := uuid.Parse(pid)
		if err == nil {
			packageID = &parsed
		}
	}
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	bills, total, err := h.svc.ListBills(c.Context(), claims.OrgID, vendorID, packageID, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, bills, int64(total), page, limit)
}

func (h *VendorHandler) GetOverdueBills(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	bills, err := h.svc.GetOverdueBills(c.Context(), claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, bills)
}

func (h *VendorHandler) GetBillsDueSoon(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	days, _ := strconv.Atoi(c.Query("days", "7"))
	bills, err := h.svc.GetBillsDueSoon(c.Context(), claims.OrgID, days)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, bills)
}

func (h *VendorHandler) GetDebtSummary(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	var vendorID *uuid.UUID
	if vid := c.Query("vendor_id"); vid != "" {
		parsed, err := uuid.Parse(vid)
		if err == nil {
			vendorID = &parsed
		}
	}

	summary, err := h.svc.GetDebtSummary(c.Context(), claims.OrgID, vendorID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, summary)
}

// --- Vendor Payments ---

func (h *VendorHandler) CreatePayment(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreatePaymentRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.VendorBillID == uuid.Nil {
		return response.BadRequest(c, "vendor_bill_id is required")
	}
	if req.PaymentDate == "" {
		return response.BadRequest(c, "payment_date is required")
	}
	if req.Amount < 1 {
		return response.BadRequest(c, "amount must be at least 1")
	}

	payment, err := h.svc.CreatePayment(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, payment)
}

func (h *VendorHandler) GetPayment(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid payment id")
	}

	payment, err := h.svc.GetPayment(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "vendor payment not found")
	}
	return response.OK(c, payment)
}

func (h *VendorHandler) DeletePayment(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid payment id")
	}
	if err := h.svc.DeletePayment(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "vendor payment not found")
	}
	return response.OK(c, fiber.Map{"message": "vendor payment deleted"})
}

func (h *VendorHandler) ListPaymentsByBill(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	billID, err := uuid.Parse(c.Params("billId"))
	if err != nil {
		return response.BadRequest(c, "invalid bill id")
	}

	payments, err := h.svc.ListPaymentsByBill(c.Context(), billID, claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, payments)
}

func (h *VendorHandler) ListPaymentsByVendor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	vendorID, err := uuid.Parse(c.Params("vendorId"))
	if err != nil {
		return response.BadRequest(c, "invalid vendor id")
	}
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	payments, total, err := h.svc.ListPaymentsByVendor(c.Context(), vendorID, claims.OrgID, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, payments, int64(total), page, limit)
}

func isValidVendorType(s string) bool {
	for _, v := range model.ValidVendorTypes() {
		if s == v {
			return true
		}
	}
	return false
}

func isValidBillStatus(s string) bool {
	for _, v := range model.ValidBillStatuses() {
		if s == v {
			return true
		}
	}
	return false
}
package handler

import (
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/invoice/model"
	"github.com/jamaah-in/v2/internal/invoice/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type InvoiceHandler struct {
	svc *service.InvoiceService
}

func NewInvoiceHandler(svc *service.InvoiceService) *InvoiceHandler {
	return &InvoiceHandler{svc: svc}
}

func (h *InvoiceHandler) CreateInvoice(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateInvoiceRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.JamaahID == uuid.Nil {
		return response.BadRequest(c, "jamaah_id is required")
	}
	if req.PackageID == uuid.Nil {
		return response.BadRequest(c, "package_id is required")
	}
	if req.RegistrationID == uuid.Nil {
		return response.BadRequest(c, "registration_id is required")
	}
	if req.PriceSnapshot < 1 {
		return response.BadRequest(c, "price_snapshot must be at least 1")
	}
	if req.PaymentScheme == "" {
		return response.BadRequest(c, "payment_scheme is required")
	}
	if !isValidPaymentScheme(req.PaymentScheme) {
		return response.BadRequest(c, "payment_scheme must be one of: dp_lunas, cicilan, full")
	}
	if req.RoomType != "" && !isValidRoomType(req.RoomType) {
		return response.BadRequest(c, "room_type must be one of: quad, triple, double, single")
	}

	inv, err := h.svc.CreateInvoice(c.Context(), claims.OrgID, claims.UserID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, inv)
}

func (h *InvoiceHandler) GetInvoice(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	inv, err := h.svc.GetInvoice(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "invoice not found")
	}
	return response.OK(c, inv)
}

func (h *InvoiceHandler) GetInvoiceByNumber(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	number := c.Params("number")

	inv, err := h.svc.GetInvoiceByNumber(c.Context(), claims.OrgID, number)
	if err != nil {
		return response.NotFound(c, "invoice not found")
	}
	return response.OK(c, inv)
}

func (h *InvoiceHandler) ListInvoices(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	invoices, total, err := h.svc.ListInvoices(c.Context(), claims.OrgID, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, invoices, int64(total), page, limit)
}

func (h *InvoiceHandler) GetInvoicesByJamaah(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("jamaahId"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	invoices, err := h.svc.GetInvoicesByJamaah(c.Context(), claims.OrgID, jamaahID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, invoices)
}

func (h *InvoiceHandler) UpdateInvoice(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	var req model.UpdateInvoiceRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	inv, err := h.svc.UpdateInvoice(c.Context(), id, claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, inv)
}

func (h *InvoiceHandler) CancelInvoice(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	var req model.CancelInvoiceRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Reason == "" {
		return response.BadRequest(c, "reason is required")
	}

	if err := h.svc.CancelInvoice(c.Context(), id, claims.OrgID, req.Reason); err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, fiber.Map{"message": "invoice cancelled"})
}

func (h *InvoiceHandler) CreatePaymentSchedules(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	invoiceID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	var req model.CreatePaymentScheduleRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if len(req.Installments) == 0 {
		return response.BadRequest(c, "at least one installment is required")
	}

	schedules, err := h.svc.CreatePaymentSchedules(c.Context(), claims.OrgID, invoiceID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, schedules)
}

func (h *InvoiceHandler) GetPaymentSchedules(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	invoiceID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	schedules, err := h.svc.GetPaymentSchedules(c.Context(), claims.OrgID, invoiceID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, schedules)
}

func (h *InvoiceHandler) RecordPayment(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	invoiceID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	var req model.RecordPaymentRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Amount < 1 {
		return response.BadRequest(c, "amount must be at least 1")
	}
	if req.PaymentMethod == "" {
		return response.BadRequest(c, "payment_method is required")
	}
	if !isValidPaymentMethod(req.PaymentMethod) {
		return response.BadRequest(c, "payment_method must be one of: transfer_bank, tunai, qris, kartu_kredit, e_wallet")
	}

	payment, inv, err := h.svc.RecordPayment(c.Context(), claims.OrgID, claims.UserID, invoiceID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, fiber.Map{"payment": payment, "invoice": inv})
}

func (h *InvoiceHandler) GetPayments(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	invoiceID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid invoice id")
	}

	payments, err := h.svc.GetPayments(c.Context(), claims.OrgID, invoiceID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, payments)
}

func (h *InvoiceHandler) GetSummary(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	summary, err := h.svc.GetSummary(c.Context(), claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, summary)
}

func isValidPaymentScheme(s string) bool {
	for _, v := range model.ValidPaymentSchemes() {
		if s == v {
			return true
		}
	}
	return false
}

func isValidPaymentMethod(s string) bool {
	for _, v := range model.ValidPaymentMethods() {
		if s == v {
			return true
		}
	}
	return false
}

func isValidRoomType(s string) bool {
	for _, v := range []string{"quad", "triple", "double", "single"} {
		if s == v {
			return true
		}
	}
	return false
}
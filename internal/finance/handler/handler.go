package handler

import (
	"strconv"
	"strings"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/finance/model"
	"github.com/jamaah-in/v2/internal/finance/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type FinanceHandler struct {
	svc *service.FinanceService
}

func NewFinanceHandler(svc *service.FinanceService) *FinanceHandler {
	return &FinanceHandler{svc: svc}
}

func (h *FinanceHandler) CreateExpense(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateExpenseRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.PackageID == uuid.Nil {
		return response.BadRequest(c, "package_id is required")
	}
	if req.Category == "" {
		return response.BadRequest(c, "category is required")
	}
	if !isValidCategory(req.Category) {
		return response.BadRequest(c, "category must be one of: "+strings.Join(model.ValidExpenseCategories(), ", "))
	}
	if req.Description == "" {
		return response.BadRequest(c, "description is required")
	}
	if req.Amount < 1 {
		return response.BadRequest(c, "amount must be at least 1")
	}
	if req.ExpenseDate == "" {
		return response.BadRequest(c, "expense_date is required")
	}
	if req.Status != "" && !isValidExpenseStatus(req.Status) {
		return response.BadRequest(c, "status must be one of: belum_bayar, sebagian, lunas")
	}

	expense, err := h.svc.CreateExpense(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, expense)
}

func (h *FinanceHandler) GetExpense(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid expense id")
	}

	expense, err := h.svc.GetExpense(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "expense not found")
	}
	return response.OK(c, expense)
}

func (h *FinanceHandler) UpdateExpense(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid expense id")
	}

	var req model.UpdateExpenseRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Category != nil && !isValidCategory(*req.Category) {
		return response.BadRequest(c, "category must be one of: "+strings.Join(model.ValidExpenseCategories(), ", "))
	}
	if req.Status != nil && !isValidExpenseStatus(*req.Status) {
		return response.BadRequest(c, "status must be one of: belum_bayar, sebagian, lunas")
	}

	expense, err := h.svc.UpdateExpense(c.Context(), id, claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, expense)
}

func (h *FinanceHandler) DeleteExpense(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid expense id")
	}
	if err := h.svc.DeleteExpense(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "expense not found")
	}
	return response.OK(c, fiber.Map{"message": "expense deleted"})
}

func (h *FinanceHandler) ListExpenses(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	category := c.Query("category")
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	expenses, total, err := h.svc.ListExpenses(c.Context(), claims.OrgID, category, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, expenses, int64(total), page, limit)
}

func (h *FinanceHandler) ListExpensesByPackage(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	expenses, err := h.svc.ListExpensesByPackage(c.Context(), claims.OrgID, packageID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, expenses)
}

func (h *FinanceHandler) GetSummary(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	var packageID *uuid.UUID
	if pid := c.Query("package_id"); pid != "" {
		parsed, err := uuid.Parse(pid)
		if err == nil {
			packageID = &parsed
		}
	}

	summary, err := h.svc.GetSummary(c.Context(), claims.OrgID, packageID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, summary)
}

func (h *FinanceHandler) GetOverdueExpenses(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	expenses, err := h.svc.GetOverdueExpenses(c.Context(), claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, expenses)
}

func (h *FinanceHandler) GetPnL(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	authToken := c.Get("Authorization")
	pnl, err := h.svc.GetPnL(c.Context(), claims.OrgID, packageID, authToken)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, pnl)
}

func isValidCategory(s string) bool {
	for _, v := range model.ValidExpenseCategories() {
		if s == v {
			return true
		}
	}
	return false
}

func isValidExpenseStatus(s string) bool {
	for _, v := range model.ValidExpenseStatuses() {
		if s == v {
			return true
		}
	}
	return false
}
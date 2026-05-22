package handler

import (
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/package/model"
	"github.com/jamaah-in/v2/internal/package/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type PackageHandler struct {
	svc *service.PackageService
}

func NewPackageHandler(svc *service.PackageService) *PackageHandler {
	return &PackageHandler{svc: svc}
}

func (h *PackageHandler) CreatePackage(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreatePackageRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Name == "" {
		return response.BadRequest(c, "name is required")
	}
	if req.PackageType == "" {
		return response.BadRequest(c, "package_type is required")
	}
	if req.TotalSeats < 1 {
		return response.BadRequest(c, "total_seats must be at least 1")
	}

	pkg, err := h.svc.CreatePackage(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, pkg)
}

func (h *PackageHandler) GetPackage(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	pkg, err := h.svc.GetPackage(c.Context(), id)
	if err != nil {
		return response.NotFound(c, "package not found")
	}
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if pkg.OrgID != claims.OrgID && !pkg.IsPublished {
		return response.NotFound(c, "package not found")
	}
	return response.OK(c, pkg)
}

func (h *PackageHandler) ListPackages(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	packages, total, err := h.svc.ListPackages(c.Context(), claims.OrgID, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, packages, int64(total), page, limit)
}

func (h *PackageHandler) UpdatePackage(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	var req model.UpdatePackageRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	pkg, err := h.svc.UpdatePackage(c.Context(), id, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, pkg)
}

func (h *PackageHandler) DeletePackage(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}
	if err := h.svc.DeletePackage(c.Context(), id); err != nil {
		return response.NotFound(c, "package not found")
	}
	return response.OK(c, fiber.Map{"message": "package deleted"})
}

func (h *PackageHandler) UpdatePackageStatus(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	var req model.UpdatePackageStatusRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	pkg, err := h.svc.UpdatePackageStatus(c.Context(), id, req.Status)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, pkg)
}

func (h *PackageHandler) GetPackageQuota(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}
	quota, err := h.svc.GetPackageQuota(c.Context(), id)
	if err != nil {
		return response.NotFound(c, "package not found")
	}
	return response.OK(c, quota)
}

func (h *PackageHandler) GetProfitProjection(c *fiber.Ctx) error {
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}
	proj, err := h.svc.GetProfitProjection(c.Context(), id)
	if err != nil {
		return response.NotFound(c, "package not found")
	}
	return response.OK(c, proj)
}

func (h *PackageHandler) CreatePricingTier(c *fiber.Ctx) error {
	packageID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	var req model.CreatePricingTierRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.RoomType == "" {
		return response.BadRequest(c, "room_type is required")
	}
	if req.Price < 1 {
		return response.BadRequest(c, "price must be at least 1")
	}

	tier, err := h.svc.CreatePricingTier(c.Context(), packageID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, tier)
}

func (h *PackageHandler) UpdatePricingTier(c *fiber.Ctx) error {
	tierID, err := uuid.Parse(c.Params("tid"))
	if err != nil {
		return response.BadRequest(c, "invalid tier id")
	}

	var req model.CreatePricingTierRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	tier, err := h.svc.UpdatePricingTier(c.Context(), tierID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, tier)
}

func (h *PackageHandler) DeletePricingTier(c *fiber.Ctx) error {
	tierID, err := uuid.Parse(c.Params("tid"))
	if err != nil {
		return response.BadRequest(c, "invalid tier id")
	}
	if err := h.svc.DeletePricingTier(c.Context(), tierID); err != nil {
		return response.NotFound(c, "tier not found")
	}
	return response.OK(c, fiber.Map{"message": "tier deleted"})
}

func (h *PackageHandler) CreateCostComponent(c *fiber.Ctx) error {
	packageID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	var req model.CreateCostComponentRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Name == "" {
		return response.BadRequest(c, "name is required")
	}
	if req.Category == "" {
		return response.BadRequest(c, "category is required")
	}

	cc, err := h.svc.CreateCostComponent(c.Context(), packageID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, cc)
}

func (h *PackageHandler) UpdateCostComponent(c *fiber.Ctx) error {
	ccID, err := uuid.Parse(c.Params("cid"))
	if err != nil {
		return response.BadRequest(c, "invalid cost component id")
	}

	var req model.CreateCostComponentRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	cc, err := h.svc.UpdateCostComponent(c.Context(), ccID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, cc)
}

func (h *PackageHandler) DeleteCostComponent(c *fiber.Ctx) error {
	ccID, err := uuid.Parse(c.Params("cid"))
	if err != nil {
		return response.BadRequest(c, "invalid cost component id")
	}
	if err := h.svc.DeleteCostComponent(c.Context(), ccID); err != nil {
		return response.NotFound(c, "cost component not found")
	}
	return response.OK(c, fiber.Map{"message": "cost component deleted"})
}

func (h *PackageHandler) GetPublicPackage(c *fiber.Ctx) error {
	slug := c.Params("slug")
	pkg, err := h.svc.GetPackageBySlug(c.Context(), slug)
	if err != nil {
		return response.NotFound(c, "package not found")
	}
	if !pkg.IsPublished {
		return response.NotFound(c, "package not found")
	}
	public := fiber.Map{
		"id":                pkg.ID,
		"name":              pkg.Name,
		"slug":              pkg.Slug,
		"description":       pkg.Description,
		"package_type":      pkg.PackageType,
		"departure_date":    pkg.DepartureDate,
		"return_date":       pkg.ReturnDate,
		"duration_days":     pkg.DurationDays,
		"total_seats":       pkg.TotalSeats,
		"reserved_seats":    pkg.ReservedSeats,
		"available_seats":   pkg.TotalSeats - pkg.ReservedSeats,
		"airline":           pkg.Airline,
		"hotel_makkah_name": pkg.HotelMakkahName,
		"pricing_tiers":    pkg.PricingTiers,
	}
	return response.OK(c, public)
}
package handler

import (
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/aiocr/model"
	"github.com/jamaah-in/v2/internal/aiocr/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type AIOCRHandler struct {
	svc *service.AIOCRService
}

func NewAIOCRHandler(svc *service.AIOCRService) *AIOCRHandler {
	return &AIOCRHandler{svc: svc}
}

func (h *AIOCRHandler) CreateScanJob(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateScanJobRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if len(req.Files) == 0 {
		return response.BadRequest(c, "at least one file is required")
	}

	job, err := h.svc.CreateScanJob(c.Context(), claims.OrgID, claims.UserID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, job)
}

func (h *AIOCRHandler) GetScanJob(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid scan job id")
	}

	job, err := h.svc.GetScanJob(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "scan job not found")
	}
	return response.OK(c, job)
}

func (h *AIOCRHandler) ListScanJobs(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	jobs, total, err := h.svc.ListScanJobs(c.Context(), claims.OrgID, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, jobs, int64(total), page, limit)
}

func (h *AIOCRHandler) GetScanResult(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid scan result id")
	}

	result, err := h.svc.GetScanResult(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "scan result not found")
	}
	return response.OK(c, result)
}

func (h *AIOCRHandler) GetScanResultsByJob(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jobID, err := uuid.Parse(c.Params("jobId"))
	if err != nil {
		return response.BadRequest(c, "invalid job id")
	}

	results, err := h.svc.GetScanResultsByJob(c.Context(), claims.OrgID, jobID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, results)
}

func (h *AIOCRHandler) CreateExportTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateExportTemplateRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Name == "" {
		return response.BadRequest(c, "name is required")
	}
	if req.ColumnMapping == nil {
		return response.BadRequest(c, "column_mapping is required")
	}

	t, err := h.svc.CreateExportTemplate(c.Context(), claims.OrgID, claims.UserID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, t)
}

func (h *AIOCRHandler) ListExportTemplates(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	templates, err := h.svc.ListExportTemplates(c.Context(), claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, templates)
}

func (h *AIOCRHandler) DeleteExportTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid template id")
	}
	if err := h.svc.DeleteExportTemplate(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "export template not found")
	}
	return response.OK(c, fiber.Map{"message": "export template deleted"})
}
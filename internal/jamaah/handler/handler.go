package handler

import (
	"strconv"

	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/jamaah/model"
	"github.com/jamaah-in/v2/internal/jamaah/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type JamaahHandler struct {
	svc *service.JamaahService
}

func NewJamaahHandler(svc *service.JamaahService) *JamaahHandler {
	return &JamaahHandler{svc: svc}
}

func (h *JamaahHandler) CreateProfile(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)

	var req model.CreateJamaahRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Nama == "" {
		return response.BadRequest(c, "nama is required")
	}

	profile, err := h.svc.CreateProfile(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, profile)
}

func (h *JamaahHandler) GetProfile(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	profile, err := h.svc.GetProfile(c.Context(), id, claims.OrgID)
	if err != nil {
		return response.NotFound(c, "jamaah profile not found")
	}
	return response.OK(c, profile)
}

func (h *JamaahHandler) UpdateProfile(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	var req model.UpdateJamaahRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	profile, err := h.svc.UpdateProfile(c.Context(), id, claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, profile)
}

func (h *JamaahHandler) DeleteProfile(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}
	if err := h.svc.DeleteProfile(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "jamaah profile not found")
	}
	return response.OK(c, fiber.Map{"message": "jamaah profile deleted"})
}

func (h *JamaahHandler) ListProfiles(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	search := c.Query("search")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	profiles, total, err := h.svc.ListProfiles(c.Context(), claims.OrgID, search, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, profiles, int64(total), page, limit)
}

func (h *JamaahHandler) FindByNIK(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	nik := c.Params("nik")
	if nik == "" {
		return response.BadRequest(c, "nik is required")
	}

	profile, err := h.svc.FindByNIK(c.Context(), claims.OrgID, nik)
	if err != nil {
		return response.NotFound(c, "jamaah profile not found")
	}
	return response.OK(c, profile)
}

func (h *JamaahHandler) FindByPaspor(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	paspor := c.Params("paspor")
	if paspor == "" {
		return response.BadRequest(c, "paspor number is required")
	}

	profile, err := h.svc.FindByPaspor(c.Context(), claims.OrgID, paspor)
	if err != nil {
		return response.NotFound(c, "jamaah profile not found")
	}
	return response.OK(c, profile)
}

func (h *JamaahHandler) RegisterToPackage(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	var req model.RegisterToPackageRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.PackageID == uuid.Nil {
		return response.BadRequest(c, "package_id is required")
	}
	if req.RoomType == "" {
		return response.BadRequest(c, "room_type is required")
	}

	reg, err := h.svc.RegisterToPackage(c.Context(), claims.OrgID, claims.UserID, jamaahID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, reg)
}

func (h *JamaahHandler) GetRegistration(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	reg, err := h.svc.GetRegistration(c.Context(), claims.OrgID, jamaahID, packageID)
	if err != nil {
		return response.NotFound(c, "registration not found")
	}
	return response.OK(c, reg)
}

func (h *JamaahHandler) UpdatePipelineStatus(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	var req model.UpdatePipelineStatusRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	reg, err := h.svc.UpdatePipelineStatus(c.Context(), claims.OrgID, jamaahID, packageID, req.PipelineStatus)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, reg)
}

func (h *JamaahHandler) RemoveFromPackage(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}

	if err := h.svc.RemoveFromPackage(c.Context(), claims.OrgID, jamaahID, packageID); err != nil {
		return response.NotFound(c, "registration not found")
	}
	return response.OK(c, fiber.Map{"message": "removed from package"})
}

func (h *JamaahHandler) ListByPackage(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	packageID, err := uuid.Parse(c.Params("pkgId"))
	if err != nil {
		return response.BadRequest(c, "invalid package id")
	}
	status := c.Query("status")
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	profiles, total, err := h.svc.ListByPackage(c.Context(), claims.OrgID, packageID, status, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Paginated(c, profiles, int64(total), page, limit)
}

func (h *JamaahHandler) AddNote(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	var req model.AddNoteRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Content == "" {
		return response.BadRequest(c, "content is required")
	}

	note, err := h.svc.AddNote(c.Context(), jamaahID, claims.OrgID, claims.UserID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, note)
}

func (h *JamaahHandler) ListNotes(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	notes, err := h.svc.ListNotes(c.Context(), claims.OrgID, jamaahID, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, notes)
}

func (h *JamaahHandler) AddFollowUp(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	var req model.AddFollowUpRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Description == "" {
		return response.BadRequest(c, "description is required")
	}
	if req.DueDate == "" {
		return response.BadRequest(c, "due_date is required")
	}

	fu, err := h.svc.AddFollowUp(c.Context(), claims.OrgID, claims.UserID, jamaahID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, fu)
}

func (h *JamaahHandler) ListFollowUps(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	completed := c.Query("completed") == "true"
	page, _ := strconv.Atoi(c.Query("page", "1"))
	limit, _ := strconv.Atoi(c.Query("page_size", "20"))

	followups, err := h.svc.ListFollowUps(c.Context(), claims.OrgID, completed, page, limit)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, followups)
}

func (h *JamaahHandler) CompleteFollowUp(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("followUpId"))
	if err != nil {
		return response.BadRequest(c, "invalid follow-up id")
	}
	if err := h.svc.CompleteFollowUp(c.Context(), id, claims.OrgID); err != nil {
		return response.NotFound(c, "follow-up not found")
	}
	return response.OK(c, fiber.Map{"message": "follow-up completed"})
}

func (h *JamaahHandler) UploadDocument(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	var req model.UploadDocumentRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.DocType == "" {
		return response.BadRequest(c, "doc_type is required")
	}

	var fileURL, fileName *string
	var fileSize *int64

	file, err := c.FormFile("file")
	if err == nil {
		fileName = &file.Filename
		fileSizeVal := file.Size
		fileSize = &fileSizeVal
		fileURL = strPtr("")
	}

	doc, err := h.svc.UploadDocument(c.Context(), claims.OrgID, jamaahID, req, fileURL, fileName, fileSize)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, doc)
}

func (h *JamaahHandler) ListDocuments(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	jamaahID, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid jamaah id")
	}

	docs, err := h.svc.ListDocuments(c.Context(), claims.OrgID, jamaahID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, docs)
}

func (h *JamaahHandler) UpdateDocumentStatus(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	docID, err := uuid.Parse(c.Params("docId"))
	if err != nil {
		return response.BadRequest(c, "invalid document id")
	}

	var req model.UpdateDocumentStatusRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}

	if err := h.svc.UpdateDocumentStatus(c.Context(), claims.OrgID, docID, req.Status, &claims.UserID, req.Notes); err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, fiber.Map{"message": "document status updated"})
}

func (h *JamaahHandler) DashboardAlerts(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	alerts, err := h.svc.GetDashboardAlerts(c.Context(), claims.OrgID)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, alerts)
}

func strPtr(s string) *string { return &s }
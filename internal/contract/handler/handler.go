package handler

import (
	"github.com/gofiber/fiber/v2"
	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/contract/model"
	"github.com/jamaah-in/v2/internal/contract/repository"
	"github.com/jamaah-in/v2/internal/contract/service"
	sharedAuth "github.com/jamaah-in/v2/internal/shared/auth"
	"github.com/jamaah-in/v2/internal/shared/response"
)

type ContractHandler struct {
	svc *service.ContractService
}

func NewContractHandler(svc *service.ContractService) *ContractHandler {
	return &ContractHandler{svc: svc}
}

func (h *ContractHandler) ListTemplates(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	includeInactive := c.Query("include_inactive") == "true"
	templates, err := h.svc.ListTemplates(c.Context(), claims.OrgID, includeInactive)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, templates)
}

func (h *ContractHandler) GetTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid template id")
	}
	tpl, err := h.svc.GetTemplate(c.Context(), id)
	if err != nil || tpl.OrgID != claims.OrgID {
		return response.NotFound(c, "contract template not found")
	}
	return response.OK(c, tpl)
}

func (h *ContractHandler) CreateTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if !canEditContracts(claims.Role) {
		return response.Forbidden(c, "insufficient permissions to create contract template")
	}
	var req model.CreateTemplateRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Name == "" {
		return response.BadRequest(c, "name is required")
	}
	if req.Content == "" {
		return response.BadRequest(c, "content is required")
	}
	tpl, err := h.svc.CreateTemplate(c.Context(), claims.OrgID, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.Created(c, tpl)
}

func (h *ContractHandler) UpdateTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if !canEditContracts(claims.Role) {
		return response.Forbidden(c, "insufficient permissions to update contract template")
	}
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid template id")
	}
	tpl, err := h.svc.GetTemplate(c.Context(), id)
	if err != nil || tpl.OrgID != claims.OrgID {
		return response.NotFound(c, "contract template not found")
	}
	var req model.UpdateTemplateRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	tpl, err = h.svc.UpdateTemplate(c.Context(), id, req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, tpl)
}

func (h *ContractHandler) DeleteTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if !canEditContracts(claims.Role) {
		return response.Forbidden(c, "insufficient permissions to delete contract template")
	}
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid template id")
	}
	tpl, err := h.svc.GetTemplate(c.Context(), id)
	if err != nil || tpl.OrgID != claims.OrgID {
		return response.NotFound(c, "contract template not found")
	}
	if err := h.svc.DeleteTemplate(c.Context(), id); err != nil {
		return response.NotFound(c, "contract template not found")
	}
	return response.OK(c, fiber.Map{"message": "contract template deleted"})
}

func (h *ContractHandler) PreviewTemplate(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if claims.OrgID == uuid.Nil {
		return response.Forbidden(c, "invalid organization")
	}
	var req model.PreviewTemplateRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.Content == "" {
		return response.BadRequest(c, "content is required")
	}
	preview, err := h.svc.PreviewTemplate(c.Context(), req)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, preview)
}

func (h *ContractHandler) CreateInstance(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	if !canEditContracts(claims.Role) {
		return response.Forbidden(c, "insufficient permissions to generate contract")
	}
	var req model.CreateContractInstanceRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	if req.TemplateID == uuid.Nil {
		return response.BadRequest(c, "template_id is required")
	}
	if req.RecipientName == "" {
		return response.BadRequest(c, "recipient_name is required")
	}
	contract, err := h.svc.CreateInstance(c.Context(), claims.OrgID, req)
	if err == repository.ErrTemplateNotFound {
		return response.NotFound(c, "contract template not found")
	}
	if err != nil {
		return response.BadRequest(c, err.Error())
	}
	return response.Created(c, contract)
}

func (h *ContractHandler) ListInstances(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	status := c.Query("status")
	contracts, err := h.svc.ListInstances(c.Context(), claims.OrgID, status)
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, contracts)
}

func (h *ContractHandler) GetInstance(c *fiber.Ctx) error {
	claims := c.Locals("claims").(*sharedAuth.Claims)
	id, err := uuid.Parse(c.Params("id"))
	if err != nil {
		return response.BadRequest(c, "invalid contract id")
	}
	contract, err := h.svc.GetInstance(c.Context(), id)
	if err == repository.ErrInstanceNotFound || (err == nil && contract.OrgID != claims.OrgID) {
		return response.NotFound(c, "contract instance not found")
	}
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, contract)
}

func (h *ContractHandler) GetPublicContract(c *fiber.Ctx) error {
	contract, err := h.svc.GetPublicInstance(c.Context(), c.Params("token"))
	if err == repository.ErrInstanceNotFound {
		return response.NotFound(c, "contract link not found")
	}
	if err != nil {
		return response.InternalError(c, err.Error())
	}
	return response.OK(c, contract)
}

func (h *ContractHandler) SignPublicContract(c *fiber.Ctx) error {
	var req model.SignContractRequest
	if err := c.BodyParser(&req); err != nil {
		return response.BadRequest(c, "invalid request body")
	}
	contract, err := h.svc.SignPublicContract(c.Context(), c.Params("token"), req, c.IP())
	if err == repository.ErrInstanceNotFound {
		return response.NotFound(c, "contract link not found")
	}
	if err != nil {
		return response.BadRequest(c, err.Error())
	}
	return response.OK(c, contract)
}

func canEditContracts(role string) bool {
	return role == "owner" || role == "admin"
}

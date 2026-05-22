package service

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jamaah-in/v2/internal/contract/model"
	"github.com/jamaah-in/v2/internal/contract/repository"
)

const contractConsentStatement = "Saya menyatakan telah membaca dan menyetujui seluruh isi kontrak"

type ContractService struct {
	repo *repository.ContractRepo
}

func NewContractService(repo *repository.ContractRepo) *ContractService {
	return &ContractService{repo: repo}
}

func (s *ContractService) CreateTemplate(ctx context.Context, orgID uuid.UUID, req model.CreateTemplateRequest) (*model.ContractTemplate, error) {
	isActive := true
	if req.IsActive != nil {
		isActive = *req.IsActive
	}
	tpl := &model.ContractTemplate{
		ID:          uuid.New(),
		OrgID:       orgID,
		Name:        strings.TrimSpace(req.Name),
		PackageType: trimOptionalString(req.PackageType),
		Content:     strings.TrimSpace(req.Content),
		IsActive:    isActive,
	}
	if err := s.repo.CreateTemplate(ctx, tpl); err != nil {
		return nil, err
	}
	return tpl, nil
}

func (s *ContractService) GetTemplate(ctx context.Context, id uuid.UUID) (*model.ContractTemplate, error) {
	return s.repo.GetTemplateByID(ctx, id)
}

func (s *ContractService) ListTemplates(ctx context.Context, orgID uuid.UUID, includeInactive bool) ([]model.ContractTemplate, error) {
	return s.repo.ListTemplates(ctx, orgID, includeInactive)
}

func (s *ContractService) UpdateTemplate(ctx context.Context, id uuid.UUID, req model.UpdateTemplateRequest) (*model.ContractTemplate, error) {
	tpl, err := s.repo.GetTemplateByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if req.Name != nil {
		tpl.Name = strings.TrimSpace(*req.Name)
	}
	if req.PackageType != nil {
		tpl.PackageType = trimOptionalString(req.PackageType)
	}
	if req.Content != nil {
		tpl.Content = strings.TrimSpace(*req.Content)
	}
	if req.IsActive != nil {
		tpl.IsActive = *req.IsActive
	}
	if err := s.repo.UpdateTemplate(ctx, tpl); err != nil {
		return nil, err
	}
	return s.repo.GetTemplateByID(ctx, id)
}

func (s *ContractService) DeleteTemplate(ctx context.Context, id uuid.UUID) error {
	return s.repo.DeleteTemplate(ctx, id)
}

func (s *ContractService) PreviewTemplate(_ context.Context, req model.PreviewTemplateRequest) (*model.PreviewTemplateResponse, error) {
	rendered := repository.RenderTemplate(strings.TrimSpace(req.Content), req.Data)
	return &model.PreviewTemplateResponse{Rendered: rendered}, nil
}

func (s *ContractService) CreateInstance(ctx context.Context, orgID uuid.UUID, req model.CreateContractInstanceRequest) (*model.ContractInstance, error) {
	tpl, err := s.repo.GetTemplateByID(ctx, req.TemplateID)
	if err != nil {
		return nil, err
	}
	if tpl.OrgID != orgID {
		return nil, repository.ErrTemplateNotFound
	}

	recipientName := strings.TrimSpace(req.RecipientName)
	if recipientName == "" {
		return nil, fmt.Errorf("recipient name is required")
	}

	variables := cloneVariables(req.Variables)
	if variables == nil {
		variables = map[string]string{}
	}
	if _, ok := variables["nama_jamaah"]; !ok {
		variables["nama_jamaah"] = recipientName
	}
	if req.PackageType != nil && strings.TrimSpace(*req.PackageType) != "" {
		variables["tipe_paket"] = strings.TrimSpace(*req.PackageType)
	}

	token, err := repository.GeneratePublicToken()
	if err != nil {
		return nil, err
	}
	expiresInDays := 7
	if req.ExpiresInDays != nil && *req.ExpiresInDays > 0 {
		expiresInDays = *req.ExpiresInDays
	}
	now := time.Now().UTC()
	contract := &model.ContractInstance{
		ID:              uuid.New(),
		OrgID:           orgID,
		TemplateID:      tpl.ID,
		JamaahID:        req.JamaahID,
		PackageID:       req.PackageID,
		TemplateName:    tpl.Name,
		PackageType:     firstNonNil(trimOptionalString(req.PackageType), trimOptionalString(tpl.PackageType)),
		RecipientName:   recipientName,
		RecipientPhone:  trimOptionalString(req.RecipientPhone),
		RecipientEmail:  trimOptionalString(req.RecipientEmail),
		PublicToken:     token,
		Variables:       variables,
		RenderedContent: repository.RenderTemplate(tpl.Content, variables),
		Status:          string(model.ContractStatusSent),
		ExpiresAt:       now.Add(time.Duration(expiresInDays) * 24 * time.Hour),
	}
	if err := s.repo.CreateInstance(ctx, contract); err != nil {
		return nil, err
	}
	return contract, nil
}

func (s *ContractService) ListInstances(ctx context.Context, orgID uuid.UUID, status string) ([]model.ContractInstance, error) {
	contracts, err := s.repo.ListInstances(ctx, orgID, strings.TrimSpace(status))
	if err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	for i := range contracts {
		if shouldExpireContract(&contracts[i], now) {
			contracts[i].Status = string(model.ContractStatusExpired)
			_ = s.repo.UpdateInstanceStatus(ctx, contracts[i].ID, contracts[i].Status)
		}
	}
	return contracts, nil
}

func (s *ContractService) GetInstance(ctx context.Context, id uuid.UUID) (*model.ContractInstance, error) {
	return s.repo.GetInstanceByID(ctx, id)
}

func (s *ContractService) GetPublicInstance(ctx context.Context, token string) (*model.PublicContractResponse, error) {
	contract, err := s.repo.GetInstanceByToken(ctx, token)
	if err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	if shouldExpireContract(contract, now) {
		contract.Status = string(model.ContractStatusExpired)
		_ = s.repo.UpdateInstanceStatus(ctx, contract.ID, contract.Status)
	}
	return buildPublicContractResponse(contract), nil
}

func (s *ContractService) SignPublicContract(ctx context.Context, token string, req model.SignContractRequest, ipAddress string) (*model.PublicContractResponse, error) {
	contract, err := s.repo.GetInstanceByToken(ctx, token)
	if err != nil {
		return nil, err
	}
	now := time.Now().UTC()
	if shouldExpireContract(contract, now) {
		contract.Status = string(model.ContractStatusExpired)
		_ = s.repo.UpdateInstanceStatus(ctx, contract.ID, contract.Status)
		return buildPublicContractResponse(contract), fmt.Errorf("contract link has expired")
	}
	if contract.Status == string(model.ContractStatusSigned) {
		return buildPublicContractResponse(contract), fmt.Errorf("contract has already been signed")
	}

	signedName := strings.TrimSpace(req.SignedName)
	signatureMode := strings.TrimSpace(req.SignatureMode)
	signatureValue := strings.TrimSpace(req.SignatureValue)
	if signedName == "" {
		return nil, fmt.Errorf("signed name is required")
	}
	if signatureValue == "" {
		return nil, fmt.Errorf("signature value is required")
	}
	if signatureMode != string(model.SignatureModeDraw) && signatureMode != string(model.SignatureModeType) {
		return nil, fmt.Errorf("invalid signature mode")
	}
	if !req.ConsentAccepted {
		return nil, fmt.Errorf("consent must be accepted")
	}
	if !req.ScrolledToBottom {
		return nil, fmt.Errorf("contract must be scrolled to the bottom before signing")
	}

	hashInput := strings.Join([]string{
		contract.RenderedContent,
		signedName,
		signatureMode,
		signatureValue,
		ipAddress,
		now.Format(time.RFC3339Nano),
	}, "|")
	hash := sha256.Sum256([]byte(hashInput))
	hashValue := hex.EncodeToString(hash[:])

	contract.Status = string(model.ContractStatusSigned)
	contract.SignedAt = &now
	contract.SignedName = &signedName
	contract.SignatureMode = &signatureMode
	contract.SignatureValue = &signatureValue
	if ip := strings.TrimSpace(ipAddress); ip != "" {
		contract.SignedIPAddress = &ip
	}
	contract.DocumentHash = &hashValue
	if err := s.repo.SignInstance(ctx, contract); err != nil {
		return nil, err
	}
	return buildPublicContractResponse(contract), nil
}

func buildPublicContractResponse(contract *model.ContractInstance) *model.PublicContractResponse {
	return &model.PublicContractResponse{
		ID:               contract.ID,
		TemplateName:     contract.TemplateName,
		RecipientName:    contract.RecipientName,
		RenderedContent:  contract.RenderedContent,
		Status:           contract.Status,
		ExpiresAt:        contract.ExpiresAt,
		SignedAt:         contract.SignedAt,
		SignedName:       contract.SignedName,
		SignatureMode:    contract.SignatureMode,
		DocumentHash:     contract.DocumentHash,
		CanSign:          contract.Status == string(model.ContractStatusSent) && contract.ExpiresAt.After(time.Now().UTC()),
		ConsentStatement: contractConsentStatement,
	}
}

func shouldExpireContract(contract *model.ContractInstance, now time.Time) bool {
	return contract.Status == string(model.ContractStatusSent) && !contract.ExpiresAt.After(now)
}

func cloneVariables(input map[string]string) map[string]string {
	if input == nil {
		return nil
	}
	out := make(map[string]string, len(input))
	for key, value := range input {
		out[strings.TrimSpace(key)] = strings.TrimSpace(value)
	}
	return out
}

func trimOptionalString(value *string) *string {
	if value == nil {
		return nil
	}
	trimmed := strings.TrimSpace(*value)
	if trimmed == "" {
		return nil
	}
	return &trimmed
}

func firstNonNil(values ...*string) *string {
	for _, value := range values {
		if value != nil {
			return value
		}
	}
	return nil
}

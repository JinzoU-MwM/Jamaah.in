package repository

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamaah-in/v2/internal/contract/model"
)

type ContractRepo struct {
	pool *pgxpool.Pool
}

func NewContractRepo(pool *pgxpool.Pool) *ContractRepo {
	return &ContractRepo{pool: pool}
}

func (r *ContractRepo) CreateTemplate(ctx context.Context, tpl *model.ContractTemplate) error {
	query := `INSERT INTO contract_templates (id, org_id, name, package_type, content, is_active)
		VALUES ($1, $2, $3, $4, $5, $6)
		RETURNING created_at, updated_at`
	return r.pool.QueryRow(ctx, query,
		tpl.ID, tpl.OrgID, tpl.Name, tpl.PackageType, tpl.Content, tpl.IsActive,
	).Scan(&tpl.CreatedAt, &tpl.UpdatedAt)
}

func (r *ContractRepo) GetTemplateByID(ctx context.Context, id uuid.UUID) (*model.ContractTemplate, error) {
	tpl := &model.ContractTemplate{}
	query := `SELECT id, org_id, name, package_type, content, is_active, created_at, updated_at
		FROM contract_templates WHERE id = $1`
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&tpl.ID, &tpl.OrgID, &tpl.Name, &tpl.PackageType, &tpl.Content, &tpl.IsActive, &tpl.CreatedAt, &tpl.UpdatedAt,
	)
	if err == pgx.ErrNoRows {
		return nil, ErrTemplateNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("get template: %w", err)
	}
	return tpl, nil
}

func (r *ContractRepo) ListTemplates(ctx context.Context, orgID uuid.UUID, includeInactive bool) ([]model.ContractTemplate, error) {
	query := `SELECT id, org_id, name, package_type, content, is_active, created_at, updated_at
		FROM contract_templates WHERE org_id = $1`
	args := []any{orgID}
	if !includeInactive {
		query += ` AND is_active = true`
	}
	query += ` ORDER BY updated_at DESC`

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("list templates: %w", err)
	}
	defer rows.Close()

	templates := []model.ContractTemplate{}
	for rows.Next() {
		var tpl model.ContractTemplate
		if err := rows.Scan(
			&tpl.ID, &tpl.OrgID, &tpl.Name, &tpl.PackageType, &tpl.Content, &tpl.IsActive, &tpl.CreatedAt, &tpl.UpdatedAt,
		); err != nil {
			return nil, fmt.Errorf("scan template: %w", err)
		}
		templates = append(templates, tpl)
	}
	return templates, nil
}

func (r *ContractRepo) UpdateTemplate(ctx context.Context, tpl *model.ContractTemplate) error {
	query := `UPDATE contract_templates
		SET name = $2, package_type = $3, content = $4, is_active = $5, updated_at = NOW()
		WHERE id = $1`
	result, err := r.pool.Exec(ctx, query, tpl.ID, tpl.Name, tpl.PackageType, tpl.Content, tpl.IsActive)
	if err != nil {
		return fmt.Errorf("update template: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrTemplateNotFound
	}
	return nil
}

func (r *ContractRepo) DeleteTemplate(ctx context.Context, id uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM contract_templates WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete template: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrTemplateNotFound
	}
	return nil
}

func (r *ContractRepo) CreateInstance(ctx context.Context, contract *model.ContractInstance) error {
	variablesJSON, err := json.Marshal(contract.Variables)
	if err != nil {
		return fmt.Errorf("marshal variables: %w", err)
	}
	query := `INSERT INTO contract_instances (
		id, org_id, template_id, jamaah_id, package_id, template_name, package_type,
		recipient_name, recipient_phone, recipient_email, public_token, variables,
		rendered_content, status, expires_at
	) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
	RETURNING created_at, updated_at`
	return r.pool.QueryRow(ctx, query,
		contract.ID, contract.OrgID, contract.TemplateID, contract.JamaahID, contract.PackageID,
		contract.TemplateName, contract.PackageType, contract.RecipientName, contract.RecipientPhone,
		contract.RecipientEmail, contract.PublicToken, variablesJSON, contract.RenderedContent,
		contract.Status, contract.ExpiresAt,
	).Scan(&contract.CreatedAt, &contract.UpdatedAt)
}

func (r *ContractRepo) ListInstances(ctx context.Context, orgID uuid.UUID, status string) ([]model.ContractInstance, error) {
	query := `SELECT id, org_id, template_id, jamaah_id, package_id, template_name, package_type,
		recipient_name, recipient_phone, recipient_email, public_token, variables, rendered_content,
		status, expires_at, signed_at, signed_name, signature_mode, signature_value, signed_ip_address,
		document_hash, created_at, updated_at
		FROM contract_instances WHERE org_id = $1`
	args := []any{orgID}
	if strings.TrimSpace(status) != "" {
		query += ` AND status = $2`
		args = append(args, status)
	}
	query += ` ORDER BY created_at DESC`

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, fmt.Errorf("list contract instances: %w", err)
	}
	defer rows.Close()

	var contracts []model.ContractInstance
	for rows.Next() {
		contract, err := scanInstance(rows)
		if err != nil {
			return nil, err
		}
		contracts = append(contracts, *contract)
	}
	return contracts, nil
}

func (r *ContractRepo) GetInstanceByID(ctx context.Context, id uuid.UUID) (*model.ContractInstance, error) {
	query := `SELECT id, org_id, template_id, jamaah_id, package_id, template_name, package_type,
		recipient_name, recipient_phone, recipient_email, public_token, variables, rendered_content,
		status, expires_at, signed_at, signed_name, signature_mode, signature_value, signed_ip_address,
		document_hash, created_at, updated_at
		FROM contract_instances WHERE id = $1`
	instance, err := scanInstance(r.pool.QueryRow(ctx, query, id))
	if err == pgx.ErrNoRows {
		return nil, ErrInstanceNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("get contract instance: %w", err)
	}
	return instance, nil
}

func (r *ContractRepo) GetInstanceByToken(ctx context.Context, token string) (*model.ContractInstance, error) {
	query := `SELECT id, org_id, template_id, jamaah_id, package_id, template_name, package_type,
		recipient_name, recipient_phone, recipient_email, public_token, variables, rendered_content,
		status, expires_at, signed_at, signed_name, signature_mode, signature_value, signed_ip_address,
		document_hash, created_at, updated_at
		FROM contract_instances WHERE public_token = $1`
	instance, err := scanInstance(r.pool.QueryRow(ctx, query, token))
	if err == pgx.ErrNoRows {
		return nil, ErrInstanceNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("get contract instance by token: %w", err)
	}
	return instance, nil
}

func (r *ContractRepo) SignInstance(ctx context.Context, contract *model.ContractInstance) error {
	query := `UPDATE contract_instances
		SET status = $2, signed_at = $3, signed_name = $4, signature_mode = $5,
			signature_value = $6, signed_ip_address = $7, document_hash = $8, updated_at = NOW()
		WHERE id = $1`
	result, err := r.pool.Exec(ctx, query,
		contract.ID, contract.Status, contract.SignedAt, contract.SignedName, contract.SignatureMode,
		contract.SignatureValue, contract.SignedIPAddress, contract.DocumentHash,
	)
	if err != nil {
		return fmt.Errorf("sign contract instance: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrInstanceNotFound
	}
	return nil
}

func (r *ContractRepo) UpdateInstanceStatus(ctx context.Context, id uuid.UUID, status string) error {
	result, err := r.pool.Exec(ctx, `UPDATE contract_instances SET status = $2, updated_at = NOW() WHERE id = $1`, id, status)
	if err != nil {
		return fmt.Errorf("update contract instance status: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrInstanceNotFound
	}
	return nil
}

func scanInstance(row rowScanner) (*model.ContractInstance, error) {
	instance := &model.ContractInstance{}
	var variablesJSON []byte
	err := row.Scan(
		&instance.ID, &instance.OrgID, &instance.TemplateID, &instance.JamaahID, &instance.PackageID,
		&instance.TemplateName, &instance.PackageType, &instance.RecipientName, &instance.RecipientPhone,
		&instance.RecipientEmail, &instance.PublicToken, &variablesJSON, &instance.RenderedContent,
		&instance.Status, &instance.ExpiresAt, &instance.SignedAt, &instance.SignedName, &instance.SignatureMode,
		&instance.SignatureValue, &instance.SignedIPAddress, &instance.DocumentHash, &instance.CreatedAt, &instance.UpdatedAt,
	)
	if err != nil {
		return nil, err
	}
	instance.Variables = map[string]string{}
	if len(variablesJSON) > 0 {
		if err := json.Unmarshal(variablesJSON, &instance.Variables); err != nil {
			return nil, fmt.Errorf("unmarshal contract variables: %w", err)
		}
	}
	return instance, nil
}

type rowScanner interface {
	Scan(dest ...any) error
}

func RenderTemplate(content string, data map[string]string) string {
	rendered := content
	for key, value := range data {
		rendered = strings.ReplaceAll(rendered, "{{"+key+"}}", value)
	}
	return rendered
}

func GeneratePublicToken() (string, error) {
	buf := make([]byte, 24)
	if _, err := rand.Read(buf); err != nil {
		return "", fmt.Errorf("generate public token: %w", err)
	}
	return hex.EncodeToString(buf), nil
}

var (
	ErrTemplateNotFound = fmt.Errorf("contract template not found")
	ErrInstanceNotFound = fmt.Errorf("contract instance not found")
)

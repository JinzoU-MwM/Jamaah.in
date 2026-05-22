package repository

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamaah-in/v2/internal/jamaah/model"
)

type rowScanner interface {
	Scan(dest ...interface{}) error
}

type JamaahRepo struct {
	pool *pgxpool.Pool
}

func NewJamaahRepo(pool *pgxpool.Pool) *JamaahRepo {
	return &JamaahRepo{pool: pool}
}

const profileCols = `id, org_id, title, nama, nama_ayah, jenis_identitas, no_identitas, nama_paspor, no_paspor,
	tanggal_paspor, kota_paspor, tempat_lahir, tanggal_lahir, gender, alamat, provinsi, kabupaten,
	kecamatan, kelurahan, no_telepon, no_hp, kewarganegaraan, status_pernikahan, pendidikan, pekerjaan,
	golongan_darah, provider_visa, no_visa, tanggal_visa, tanggal_visa_akhir, asuransi, no_polis,
	tanggal_input_polis, tanggal_awal_polis, tanggal_akhir_polis, no_bpjs, email,
	contact_emergency_name, contact_emergency_phone, lead_source, referring_agent_id,
	ihram_size, mukena_size, baju_size, created_at, updated_at`

const insertCols = `id, org_id, title, nama, nama_ayah, jenis_identitas, no_identitas, nama_paspor, no_paspor,
	tanggal_paspor, kota_paspor, tempat_lahir, tanggal_lahir, gender, alamat, provinsi, kabupaten,
	kecamatan, kelurahan, no_telepon, no_hp, kewarganegaraan, status_pernikahan, pendidikan, pekerjaan,
	golongan_darah, provider_visa, no_visa, tanggal_visa, tanggal_visa_akhir, asuransi, no_polis,
	tanggal_input_polis, tanggal_awal_polis, tanggal_akhir_polis, no_bpjs, email,
	contact_emergency_name, contact_emergency_phone, lead_source, referring_agent_id,
	ihram_size, mukena_size, baju_size`

func (r *JamaahRepo) scanProfile(row rowScanner) (*model.JamaahProfile, error) {
	p := &model.JamaahProfile{}
	err := row.Scan(&p.ID, &p.OrgID, &p.Title, &p.Nama, &p.NamaAyah, &p.JenisIdentitas, &p.NoIdentitas,
		&p.NamaPaspor, &p.NoPaspor, &p.TanggalPaspor, &p.KotaPaspor, &p.TempatLahir, &p.TanggalLahir,
		&p.Gender, &p.Alamat, &p.Provinsi, &p.Kabupaten, &p.Kecamatan, &p.Kelurahan, &p.NoTelepon, &p.NoHP,
		&p.Kewarganegaraan, &p.StatusPernikahan, &p.Pendidikan, &p.Pekerjaan, &p.GolonganDarah,
		&p.ProviderVisa, &p.NoVisa, &p.TanggalVisa, &p.TanggalVisaAkhir, &p.Asuransi, &p.NoPolis,
		&p.TanggalInputPolis, &p.TanggalAwalPolis, &p.TanggalAkhirPolis, &p.NoBpjs, &p.Email,
		&p.ContactEmergencyName, &p.ContactEmergencyPhone, &p.LeadSource, &p.ReferringAgentID,
		&p.IhramSize, &p.MukenaSize, &p.BajuSize, &p.CreatedAt, &p.UpdatedAt)
	return p, err
}

func (r *JamaahRepo) CreateProfile(ctx context.Context, p *model.JamaahProfile) error {
	query := fmt.Sprintf(`INSERT INTO jamaah_profiles (%s) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24,$25,$26,$27,$28,$29,$30,$31,$32,$33,$34,$35,$36,$37,$38,$39,$40,$41,$42,$43,$44)
		RETURNING created_at, updated_at`, insertCols)
	err := r.pool.QueryRow(ctx, query,
		p.ID, p.OrgID, p.Title, p.Nama, p.NamaAyah, p.JenisIdentitas, p.NoIdentitas, p.NamaPaspor,
		p.NoPaspor, p.TanggalPaspor, p.KotaPaspor, p.TempatLahir, p.TanggalLahir, p.Gender, p.Alamat,
		p.Provinsi, p.Kabupaten, p.Kecamatan, p.Kelurahan, p.NoTelepon, p.NoHP, p.Kewarganegaraan,
		p.StatusPernikahan, p.Pendidikan, p.Pekerjaan, p.GolonganDarah, p.ProviderVisa, p.NoVisa,
		p.TanggalVisa, p.TanggalVisaAkhir, p.Asuransi, p.NoPolis, p.TanggalInputPolis, p.TanggalAwalPolis,
		p.TanggalAkhirPolis, p.NoBpjs, p.Email, p.ContactEmergencyName, p.ContactEmergencyPhone,
		p.LeadSource, p.ReferringAgentID, p.IhramSize, p.MukenaSize, p.BajuSize,
	).Scan(&p.CreatedAt, &p.UpdatedAt)
	if err != nil {
		if strings.Contains(err.Error(), "unique constraint") || strings.Contains(err.Error(), "duplicate key") {
			if strings.Contains(err.Error(), "no_identitas") {
				return ErrNIKExists
			}
			if strings.Contains(err.Error(), "no_paspor") {
				return ErrPasporExists
			}
		}
		return fmt.Errorf("create profile: %w", err)
	}
	return nil
}

func (r *JamaahRepo) GetProfileByID(ctx context.Context, id, orgID uuid.UUID) (*model.JamaahProfile, error) {
	p, err := r.scanProfile(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM jamaah_profiles WHERE id = $1 AND org_id = $2`, profileCols), id, orgID))
	if err == pgx.ErrNoRows {
		return nil, ErrProfileNotFound
	}
	return p, err
}

func (r *JamaahRepo) UpdateProfile(ctx context.Context, p *model.JamaahProfile) error {
	query := `UPDATE jamaah_profiles SET title=$2, nama=$3, nama_ayah=$4, jenis_identitas=$5, no_identitas=$6,
		nama_paspor=$7, no_paspor=$8, tanggal_paspor=$9, kota_paspor=$10, tempat_lahir=$11, tanggal_lahir=$12,
		gender=$13, alamat=$14, provinsi=$15, kabupaten=$16, kecamatan=$17, kelurahan=$18, no_telepon=$19, no_hp=$20,
		kewarganegaraan=$21, status_pernikahan=$22, pendidikan=$23, pekerjaan=$24, golongan_darah=$25,
		provider_visa=$26, no_visa=$27, tanggal_visa=$28, tanggal_visa_akhir=$29, asuransi=$30, no_polis=$31,
		tanggal_input_polis=$32, tanggal_awal_polis=$33, tanggal_akhir_polis=$34, no_bpjs=$35, email=$36,
		contact_emergency_name=$37, contact_emergency_phone=$38, lead_source=$39, ihram_size=$40, mukena_size=$41,
		baju_size=$42, updated_at=NOW() WHERE id = $1 AND org_id = $43`
	result, err := r.pool.Exec(ctx, query,
		p.ID, p.Title, p.Nama, p.NamaAyah, p.JenisIdentitas, p.NoIdentitas, p.NamaPaspor, p.NoPaspor,
		p.TanggalPaspor, p.KotaPaspor, p.TempatLahir, p.TanggalLahir, p.Gender, p.Alamat, p.Provinsi,
		p.Kabupaten, p.Kecamatan, p.Kelurahan, p.NoTelepon, p.NoHP, p.Kewarganegaraan, p.StatusPernikahan,
		p.Pendidikan, p.Pekerjaan, p.GolonganDarah, p.ProviderVisa, p.NoVisa, p.TanggalVisa, p.TanggalVisaAkhir,
		p.Asuransi, p.NoPolis, p.TanggalInputPolis, p.TanggalAwalPolis, p.TanggalAkhirPolis, p.NoBpjs,
		p.Email, p.ContactEmergencyName, p.ContactEmergencyPhone, p.LeadSource, p.IhramSize, p.MukenaSize, p.BajuSize, p.OrgID)
	if err != nil {
		return fmt.Errorf("update profile: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrProfileNotFound
	}
	return nil
}

func (r *JamaahRepo) DeleteProfile(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM jamaah_profiles WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrProfileNotFound
	}
	return nil
}

func (r *JamaahRepo) ListProfiles(ctx context.Context, orgID uuid.UUID, search string, offset, limit int) ([]model.JamaahProfile, int, error) {
	countQuery := `SELECT COUNT(*) FROM jamaah_profiles WHERE org_id = $1`
	listQuery := fmt.Sprintf(`SELECT %s FROM jamaah_profiles WHERE org_id = $1`, profileCols)
	args := []any{orgID}

	if search != "" {
		countQuery += ` AND (nama ILIKE $2 OR no_identitas ILIKE $2 OR no_paspor ILIKE $2 OR no_hp ILIKE $2 OR email ILIKE $2)`
		listQuery += ` AND (nama ILIKE $2 OR no_identitas ILIKE $2 OR no_paspor ILIKE $2 OR no_hp ILIKE $2 OR email ILIKE $2)`
		args = append(args, "%"+search+"%")
	}

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	listQuery += ` ORDER BY created_at DESC LIMIT $` + fmt.Sprintf("%d", len(args)+1) + ` OFFSET $` + fmt.Sprintf("%d", len(args)+2)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, listQuery, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	profiles := []model.JamaahProfile{}
	for rows.Next() {
		p, err := r.scanProfile(rows)
		if err != nil {
			return nil, 0, err
		}
		profiles = append(profiles, *p)
	}
	return profiles, total, nil
}

func (r *JamaahRepo) FindByNIK(ctx context.Context, orgID uuid.UUID, nik string) (*model.JamaahProfile, error) {
	p, err := r.scanProfile(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM jamaah_profiles WHERE org_id = $1 AND no_identitas = $2`, profileCols), orgID, nik))
	if err == pgx.ErrNoRows {
		return nil, ErrProfileNotFound
	}
	return p, err
}

func (r *JamaahRepo) FindByPaspor(ctx context.Context, orgID uuid.UUID, paspor string) (*model.JamaahProfile, error) {
	p, err := r.scanProfile(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM jamaah_profiles WHERE org_id = $1 AND no_paspor = $2`, profileCols), orgID, paspor))
	if err == pgx.ErrNoRows {
		return nil, ErrProfileNotFound
	}
	return p, err
}

func (r *JamaahRepo) CreateRegistration(ctx context.Context, reg *model.JamaahPackageRegistration) error {
	query := `INSERT INTO jamaah_package_registrations (id, org_id, jamaah_id, package_id, room_type, price_snapshot, discount_amount, custom_price, pipeline_status, mahram_id, internal_notes)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11) RETURNING created_at, updated_at`
	return r.pool.QueryRow(ctx, query,
		reg.ID, reg.OrgID, reg.JamaahID, reg.PackageID, reg.RoomType, reg.PriceSnapshot,
		reg.DiscountAmount, reg.CustomPrice, reg.PipelineStatus, reg.MahramID, reg.InternalNotes,
	).Scan(&reg.CreatedAt, &reg.UpdatedAt)
}

func (r *JamaahRepo) GetRegistration(ctx context.Context, orgID, jamaahID, packageID uuid.UUID) (*model.JamaahPackageRegistration, error) {
	reg := &model.JamaahPackageRegistration{}
	query := `SELECT id, org_id, jamaah_id, package_id, room_type, price_snapshot, discount_amount, custom_price,
		pipeline_status, registered_at, dp_date, lunas_date, berangkat_date, mahram_id, internal_notes, created_at, updated_at
		FROM jamaah_package_registrations WHERE org_id = $1 AND jamaah_id = $2 AND package_id = $3`
	err := r.pool.QueryRow(ctx, query, orgID, jamaahID, packageID).Scan(
		&reg.ID, &reg.OrgID, &reg.JamaahID, &reg.PackageID, &reg.RoomType, &reg.PriceSnapshot,
		&reg.DiscountAmount, &reg.CustomPrice, &reg.PipelineStatus, &reg.RegisteredAt,
		&reg.DPDate, &reg.LunasDate, &reg.BerangkatDate, &reg.MahramID, &reg.InternalNotes, &reg.CreatedAt, &reg.UpdatedAt)
	if err == pgx.ErrNoRows {
		return nil, ErrRegistrationNotFound
	}
	return reg, err
}

func (r *JamaahRepo) UpdatePipelineStatus(ctx context.Context, orgID, jamaahID, packageID uuid.UUID, status string, dpDate, lunasDate, berangkatDate *time.Time) error {
	query := `UPDATE jamaah_package_registrations SET pipeline_status = $4, dp_date = $5, lunas_date = $6, berangkat_date = $7, updated_at = NOW() WHERE org_id = $1 AND jamaah_id = $2 AND package_id = $3`
	result, err := r.pool.Exec(ctx, query, orgID, jamaahID, packageID, status, dpDate, lunasDate, berangkatDate)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrRegistrationNotFound
	}
	return nil
}

func (r *JamaahRepo) RemoveFromPackage(ctx context.Context, orgID, jamaahID, packageID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM jamaah_package_registrations WHERE org_id = $1 AND jamaah_id = $2 AND package_id = $3`, orgID, jamaahID, packageID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrRegistrationNotFound
	}
	return nil
}

func (r *JamaahRepo) ListByPackage(ctx context.Context, orgID, packageID uuid.UUID, status string, offset, limit int) ([]model.JamaahProfile, int, error) {
	countQuery := `SELECT COUNT(*) FROM jamaah_package_registrations WHERE org_id = $1 AND package_id = $2`
	args := []any{orgID, packageID}
	if status != "" {
		countQuery += ` AND pipeline_status = $3`
		args = append(args, status)
	}
	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	listQuery := `SELECT jp.jamaah_id FROM jamaah_package_registrations jp WHERE jp.org_id = $1 AND jp.package_id = $2`
	listArgs := []any{orgID, packageID}
	argIdx := 3
	if status != "" {
		listQuery += fmt.Sprintf(` AND jp.pipeline_status = $%d`, argIdx)
		listArgs = append(listArgs, status)
		argIdx++
	}
	listQuery += fmt.Sprintf(` ORDER BY jp.registered_at DESC LIMIT $%d OFFSET $%d`, argIdx, argIdx+1)
	listArgs = append(listArgs, limit, offset)

	rows, err := r.pool.Query(ctx, listQuery, listArgs...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	profiles := []model.JamaahProfile{}
	for rows.Next() {
		var jamaahID uuid.UUID
		if err := rows.Scan(&jamaahID); err != nil {
			return nil, 0, err
		}
		p, err := r.GetProfileByID(ctx, jamaahID, orgID)
		if err != nil {
			continue
		}
		profiles = append(profiles, *p)
	}
	return profiles, total, nil
}

func (r *JamaahRepo) CreateNote(ctx context.Context, note *model.JamaahNote) error {
	query := `INSERT INTO jamaah_notes (id, jamaah_id, org_id, user_id, content) VALUES ($1, $2, $3, $4, $5) RETURNING created_at`
	return r.pool.QueryRow(ctx, query, note.ID, note.JamaahID, note.OrgID, note.UserID, note.Content).Scan(&note.CreatedAt)
}

func (r *JamaahRepo) ListNotes(ctx context.Context, orgID, jamaahID uuid.UUID, limit, offset int) ([]model.JamaahNote, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, jamaah_id, org_id, user_id, content, created_at FROM jamaah_notes WHERE org_id = $1 AND jamaah_id = $2 ORDER BY created_at DESC LIMIT $3 OFFSET $4`, orgID, jamaahID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	notes := []model.JamaahNote{}
	for rows.Next() {
		var n model.JamaahNote
		if err := rows.Scan(&n.ID, &n.JamaahID, &n.OrgID, &n.UserID, &n.Content, &n.CreatedAt); err != nil {
			return nil, err
		}
		notes = append(notes, n)
	}
	return notes, nil
}

func (r *JamaahRepo) CreateFollowUp(ctx context.Context, fu *model.FollowUp) error {
	query := `INSERT INTO follow_ups (id, jamaah_id, package_id, org_id, user_id, description, due_date, is_completed) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING created_at`
	return r.pool.QueryRow(ctx, query, fu.ID, fu.JamaahID, fu.PackageID, fu.OrgID, fu.UserID, fu.Description, fu.DueDate, fu.IsCompleted).Scan(&fu.CreatedAt)
}

func (r *JamaahRepo) ListFollowUps(ctx context.Context, orgID uuid.UUID, completed bool, limit, offset int) ([]model.FollowUp, error) {
	query := `SELECT id, jamaah_id, package_id, org_id, user_id, description, due_date, is_completed, completed_at, created_at FROM follow_ups WHERE org_id = $1`
	args := []any{orgID}
	if !completed {
		query += ` AND is_completed = false`
	}
	query += ` ORDER BY due_date ASC LIMIT $2 OFFSET $3`
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	followups := []model.FollowUp{}
	for rows.Next() {
		var fu model.FollowUp
		if err := rows.Scan(&fu.ID, &fu.JamaahID, &fu.PackageID, &fu.OrgID, &fu.UserID, &fu.Description, &fu.DueDate, &fu.IsCompleted, &fu.CompletedAt, &fu.CreatedAt); err != nil {
			return nil, err
		}
		followups = append(followups, fu)
	}
	return followups, nil
}

func (r *JamaahRepo) CompleteFollowUp(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `UPDATE follow_ups SET is_completed = true, completed_at = NOW() WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrFollowUpNotFound
	}
	return nil
}

func (r *JamaahRepo) CreateDocument(ctx context.Context, doc *model.JamaahDocument) error {
	query := `INSERT INTO jamaah_documents (id, jamaah_id, package_id, org_id, doc_type, status, file_url, file_name, file_size, notes) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING created_at, updated_at`
	return r.pool.QueryRow(ctx, query, doc.ID, doc.JamaahID, doc.PackageID, doc.OrgID, doc.DocType, doc.Status, doc.FileURL, doc.FileName, doc.FileSize, doc.Notes).Scan(&doc.CreatedAt, &doc.UpdatedAt)
}

func (r *JamaahRepo) ListDocuments(ctx context.Context, orgID, jamaahID uuid.UUID) ([]model.JamaahDocument, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, jamaah_id, package_id, org_id, doc_type, status, file_url, file_name, file_size, notes, verified_by, verified_at, created_at, updated_at FROM jamaah_documents WHERE org_id = $1 AND jamaah_id = $2 ORDER BY created_at DESC`, orgID, jamaahID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	docs := []model.JamaahDocument{}
	for rows.Next() {
		var d model.JamaahDocument
		if err := rows.Scan(&d.ID, &d.JamaahID, &d.PackageID, &d.OrgID, &d.DocType, &d.Status, &d.FileURL, &d.FileName, &d.FileSize, &d.Notes, &d.VerifiedBy, &d.VerifiedAt, &d.CreatedAt, &d.UpdatedAt); err != nil {
			return nil, err
		}
		docs = append(docs, d)
	}
	return docs, nil
}

func (r *JamaahRepo) UpdateDocumentStatus(ctx context.Context, orgID uuid.UUID, id uuid.UUID, status string, verifiedBy *uuid.UUID, notes string) error {
	var completedAt *time.Time
	if status == "selesai" {
		now := time.Now()
		completedAt = &now
	}
	query := `UPDATE jamaah_documents SET status = $3, verified_by = $4, verified_at = $5, notes = $6, updated_at = NOW() WHERE org_id = $1 AND id = $2`
	result, err := r.pool.Exec(ctx, query, orgID, id, status, verifiedBy, completedAt, notes)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrDocumentNotFound
	}
	return nil
}

func (r *JamaahRepo) GetPassportExpiring(ctx context.Context, orgID uuid.UUID, withinDays int) ([]model.JamaahProfile, error) {
	query := fmt.Sprintf(`SELECT %s FROM jamaah_profiles WHERE org_id = $1 AND no_paspor IS NOT NULL AND no_paspor != '' AND tanggal_paspor IS NOT NULL AND tanggal_paspor + INTERVAL '5 years' - INTERVAL '%d days' <= NOW() AND tanggal_paspor + INTERVAL '5 years' > NOW() ORDER BY tanggal_paspor ASC`, profileCols, withinDays)
	rows, err := r.pool.Query(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	profiles := []model.JamaahProfile{}
	for rows.Next() {
		p, err := r.scanProfile(rows)
		if err != nil {
			return nil, err
		}
		profiles = append(profiles, *p)
	}
	return profiles, nil
}

var (
	ErrProfileNotFound      = fmt.Errorf("jamaah profile not found")
	ErrNIKExists           = fmt.Errorf("NIK already exists in this organization")
	ErrPasporExists        = fmt.Errorf("passport number already exists in this organization")
	ErrRegistrationNotFound = fmt.Errorf("registration not found")
	ErrFollowUpNotFound    = fmt.Errorf("follow-up not found")
	ErrDocumentNotFound    = fmt.Errorf("document not found")
)
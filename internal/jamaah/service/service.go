package service

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/jamaah/model"
	"github.com/jamaah-in/v2/internal/jamaah/repository"
)

type JamaahService struct {
	repo *repository.JamaahRepo
}

func NewJamaahService(repo *repository.JamaahRepo) *JamaahService {
	return &JamaahService{repo: repo}
}

func (s *JamaahService) CreateProfile(ctx context.Context, orgID uuid.UUID, req model.CreateJamaahRequest) (*model.JamaahProfile, error) {
	if req.Nama == "" {
		return nil, fmt.Errorf("nama is required")
	}

	p := &model.JamaahProfile{
		ID:   uuid.New(),
		OrgID: orgID,
		Title: req.Title,
		Nama:  req.Nama,
	}

	if req.NamaAyah != "" {
		p.NamaAyah = req.NamaAyah
	}
	if req.JenisIdentitas != "" {
		p.JenisIdentitas = req.JenisIdentitas
	}
	if req.NoIdentitas != "" {
		p.NoIdentitas = &req.NoIdentitas
	}
	if req.NamaPaspor != "" {
		p.NamaPaspor = req.NamaPaspor
	}
	if req.NoPaspor != "" {
		p.NoPaspor = &req.NoPaspor
	}
	if req.TanggalPaspor != "" {
		t, err := parseDate(req.TanggalPaspor)
		if err != nil {
			return nil, fmt.Errorf("tanggal_paspor: %w", err)
		}
		p.TanggalPaspor = t
	}
	if req.KotaPaspor != "" {
		p.KotaPaspor = req.KotaPaspor
	}
	if req.TempatLahir != "" {
		p.TempatLahir = req.TempatLahir
	}
	if req.TanggalLahir != "" {
		t, err := parseDate(req.TanggalLahir)
		if err != nil {
			return nil, fmt.Errorf("tanggal_lahir: %w", err)
		}
		p.TanggalLahir = t
	}
	if req.Gender != "" {
		p.Gender = req.Gender
	}
	if req.Alamat != "" {
		p.Alamat = req.Alamat
	}
	if req.Provinsi != "" {
		p.Provinsi = req.Provinsi
	}
	if req.Kabupaten != "" {
		p.Kabupaten = req.Kabupaten
	}
	if req.Kecamatan != "" {
		p.Kecamatan = req.Kecamatan
	}
	if req.Kelurahan != "" {
		p.Kelurahan = req.Kelurahan
	}
	if req.NoTelepon != "" {
		p.NoTelepon = req.NoTelepon
	}
	if req.NoHP != "" {
		p.NoHP = req.NoHP
	}
	if req.Kewarganegaraan != "" {
		p.Kewarganegaraan = req.Kewarganegaraan
	}
	if req.StatusPernikahan != "" {
		p.StatusPernikahan = req.StatusPernikahan
	}
	if req.Pendidikan != "" {
		p.Pendidikan = req.Pendidikan
	}
	if req.Pekerjaan != "" {
		p.Pekerjaan = req.Pekerjaan
	}
	if req.ProviderVisa != "" {
		p.ProviderVisa = req.ProviderVisa
	}
	if req.NoVisa != "" {
		p.NoVisa = req.NoVisa
	}
	if req.Asuransi != "" {
		p.Asuransi = req.Asuransi
	}
	if req.NoPolis != "" {
		p.NoPolis = req.NoPolis
	}
	if req.Email != "" {
		p.Email = req.Email
	}
	if req.ContactEmergencyName != "" {
		p.ContactEmergencyName = req.ContactEmergencyName
	}
	if req.ContactEmergencyPhone != "" {
		p.ContactEmergencyPhone = req.ContactEmergencyPhone
	}
	if req.LeadSource != "" {
		p.LeadSource = req.LeadSource
	}
	if req.IhramSize != "" {
		p.IhramSize = req.IhramSize
	}
	if req.MukenaSize != "" {
		p.MukenaSize = req.MukenaSize
	}
	if req.BajuSize != "" {
		p.BajuSize = req.BajuSize
	}

	if err := s.repo.CreateProfile(ctx, p); err != nil {
		return nil, err
	}
	return p, nil
}

func (s *JamaahService) GetProfile(ctx context.Context, id, orgID uuid.UUID) (*model.JamaahProfile, error) {
	return s.repo.GetProfileByID(ctx, id, orgID)
}

func (s *JamaahService) UpdateProfile(ctx context.Context, id, orgID uuid.UUID, req model.UpdateJamaahRequest) (*model.JamaahProfile, error) {
	p, err := s.repo.GetProfileByID(ctx, id, orgID)
	if err != nil {
		return nil, err
	}

	if req.Title != nil {
		p.Title = *req.Title
	}
	if req.Nama != nil {
		p.Nama = *req.Nama
	}
	if req.NamaAyah != nil {
		p.NamaAyah = *req.NamaAyah
	}
	if req.JenisIdentitas != nil {
		p.JenisIdentitas = *req.JenisIdentitas
	}
	if req.NoIdentitas != nil {
		p.NoIdentitas = req.NoIdentitas
	}
	if req.NamaPaspor != nil {
		p.NamaPaspor = *req.NamaPaspor
	}
	if req.NoPaspor != nil {
		p.NoPaspor = req.NoPaspor
	}
	if req.TanggalPaspor != nil {
		if *req.TanggalPaspor == "" {
			p.TanggalPaspor = nil
		} else {
			t, err := parseDate(*req.TanggalPaspor)
			if err != nil {
				return nil, fmt.Errorf("tanggal_paspor: %w", err)
			}
			p.TanggalPaspor = t
		}
	}
	if req.KotaPaspor != nil {
		p.KotaPaspor = *req.KotaPaspor
	}
	if req.TempatLahir != nil {
		p.TempatLahir = *req.TempatLahir
	}
	if req.TanggalLahir != nil {
		if *req.TanggalLahir == "" {
			p.TanggalLahir = nil
		} else {
			t, err := parseDate(*req.TanggalLahir)
			if err != nil {
				return nil, fmt.Errorf("tanggal_lahir: %w", err)
			}
			p.TanggalLahir = t
		}
	}
	if req.Gender != nil {
		p.Gender = *req.Gender
	}
	if req.Alamat != nil {
		p.Alamat = *req.Alamat
	}
	if req.Provinsi != nil {
		p.Provinsi = *req.Provinsi
	}
	if req.Kabupaten != nil {
		p.Kabupaten = *req.Kabupaten
	}
	if req.Kecamatan != nil {
		p.Kecamatan = *req.Kecamatan
	}
	if req.Kelurahan != nil {
		p.Kelurahan = *req.Kelurahan
	}
	if req.NoTelepon != nil {
		p.NoTelepon = *req.NoTelepon
	}
	if req.NoHP != nil {
		p.NoHP = *req.NoHP
	}
	if req.Kewarganegaraan != nil {
		p.Kewarganegaraan = *req.Kewarganegaraan
	}
	if req.StatusPernikahan != nil {
		p.StatusPernikahan = *req.StatusPernikahan
	}
	if req.Pendidikan != nil {
		p.Pendidikan = *req.Pendidikan
	}
	if req.Pekerjaan != nil {
		p.Pekerjaan = *req.Pekerjaan
	}
	if req.ProviderVisa != nil {
		p.ProviderVisa = *req.ProviderVisa
	}
	if req.NoVisa != nil {
		p.NoVisa = *req.NoVisa
	}
	if req.Asuransi != nil {
		p.Asuransi = *req.Asuransi
	}
	if req.NoPolis != nil {
		p.NoPolis = *req.NoPolis
	}
	if req.Email != nil {
		p.Email = *req.Email
	}
	if req.ContactEmergencyName != nil {
		p.ContactEmergencyName = *req.ContactEmergencyName
	}
	if req.ContactEmergencyPhone != nil {
		p.ContactEmergencyPhone = *req.ContactEmergencyPhone
	}
	if req.LeadSource != nil {
		p.LeadSource = *req.LeadSource
	}
	if req.IhramSize != nil {
		p.IhramSize = *req.IhramSize
	}
	if req.MukenaSize != nil {
		p.MukenaSize = *req.MukenaSize
	}
	if req.BajuSize != nil {
		p.BajuSize = *req.BajuSize
	}

	if err := s.repo.UpdateProfile(ctx, p); err != nil {
		return nil, err
	}
	return p, nil
}

func (s *JamaahService) DeleteProfile(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.DeleteProfile(ctx, id, orgID)
}

func (s *JamaahService) ListProfiles(ctx context.Context, orgID uuid.UUID, search string, page, limit int) ([]model.JamaahProfile, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListProfiles(ctx, orgID, search, offset, limit)
}

func (s *JamaahService) FindByNIK(ctx context.Context, orgID uuid.UUID, nik string) (*model.JamaahProfile, error) {
	return s.repo.FindByNIK(ctx, orgID, nik)
}

func (s *JamaahService) FindByPaspor(ctx context.Context, orgID uuid.UUID, paspor string) (*model.JamaahProfile, error) {
	return s.repo.FindByPaspor(ctx, orgID, paspor)
}

func (s *JamaahService) RegisterToPackage(ctx context.Context, orgID, userID uuid.UUID, jamaahID uuid.UUID, req model.RegisterToPackageRequest) (*model.JamaahPackageRegistration, error) {
	existing, _ := s.repo.GetRegistration(ctx, orgID, jamaahID, req.PackageID)
	if existing != nil {
		return nil, fmt.Errorf("jamaah is already registered to this package")
	}

	reg := &model.JamaahPackageRegistration{
		ID:             uuid.New(),
		OrgID:          orgID,
		JamaahID:       jamaahID,
		PackageID:      req.PackageID,
		RoomType:        req.RoomType,
		PriceSnapshot:   req.PriceSnapshot,
		DiscountAmount:  req.DiscountAmount,
		CustomPrice:     req.CustomPrice,
		PipelineStatus:  string(model.StatusProspek),
		RegisteredAt:    time.Now(),
		MahramID:        nil,
		InternalNotes:   "",
	}

	if err := s.repo.CreateRegistration(ctx, reg); err != nil {
		return nil, err
	}
	return reg, nil
}

func (s *JamaahService) GetRegistration(ctx context.Context, orgID, jamaahID, packageID uuid.UUID) (*model.JamaahPackageRegistration, error) {
	return s.repo.GetRegistration(ctx, orgID, jamaahID, packageID)
}

func (s *JamaahService) UpdatePipelineStatus(ctx context.Context, orgID, jamaahID, packageID uuid.UUID, status string) (*model.JamaahPackageRegistration, error) {
	reg, err := s.repo.GetRegistration(ctx, orgID, jamaahID, packageID)
	if err != nil {
		return nil, err
	}

	var dpDate, lunasDate, berangkatDate *time.Time
	now := time.Now()
	switch status {
	case string(model.StatusProspek):
		// Going back to prospek clears all dates
		dpDate = nil
		lunasDate = nil
		berangkatDate = nil
	case string(model.StatusDP):
		// DP sets dp_date, clears later dates
		dpDate = &now
		lunasDate = nil
		berangkatDate = nil
	case string(model.StatusLunas):
		// Lunas preserves dp_date, sets lunas_date, clears berangkat
		dpDate = reg.DPDate
		lunasDate = &now
		berangkatDate = nil
	case string(model.StatusBerangkat):
		// Berangkat preserves dp_date and lunas_date, sets berangkat_date
		dpDate = reg.DPDate
		lunasDate = reg.LunasDate
		berangkatDate = &now
	}

	if err := s.repo.UpdatePipelineStatus(ctx, orgID, jamaahID, packageID, status, dpDate, lunasDate, berangkatDate); err != nil {
		return nil, err
	}
	return s.repo.GetRegistration(ctx, orgID, jamaahID, packageID)
}

func (s *JamaahService) RemoveFromPackage(ctx context.Context, orgID, jamaahID, packageID uuid.UUID) error {
	return s.repo.RemoveFromPackage(ctx, orgID, jamaahID, packageID)
}

func (s *JamaahService) ListByPackage(ctx context.Context, orgID, packageID uuid.UUID, status string, page, limit int) ([]model.JamaahProfile, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListByPackage(ctx, orgID, packageID, status, offset, limit)
}

func (s *JamaahService) AddNote(ctx context.Context, jamaahID, orgID, userID uuid.UUID, req model.AddNoteRequest) (*model.JamaahNote, error) {
	note := &model.JamaahNote{
		ID:        uuid.New(),
		JamaahID:  jamaahID,
		OrgID:     orgID,
		UserID:    userID,
		Content:   req.Content,
	}
	if err := s.repo.CreateNote(ctx, note); err != nil {
		return nil, err
	}
	return note, nil
}

func (s *JamaahService) ListNotes(ctx context.Context, orgID, jamaahID uuid.UUID, page, limit int) ([]model.JamaahNote, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListNotes(ctx, orgID, jamaahID, limit, offset)
}

func (s *JamaahService) AddFollowUp(ctx context.Context, orgID, userID uuid.UUID, jamaahID uuid.UUID, req model.AddFollowUpRequest) (*model.FollowUp, error) {
	var packageID *uuid.UUID
	if req.PackageID != nil && *req.PackageID != "" {
		pid, err := uuid.Parse(*req.PackageID)
		if err != nil {
			return nil, fmt.Errorf("invalid package_id")
		}
		packageID = &pid
	}

	dueDate, err := parseDate(req.DueDate)
	if err != nil {
		return nil, fmt.Errorf("due_date: %w", err)
	}

	fu := &model.FollowUp{
		ID:          uuid.New(),
		JamaahID:    jamaahID,
		PackageID:   packageID,
		OrgID:       orgID,
		UserID:      userID,
		Description: req.Description,
		DueDate:     *dueDate,
		IsCompleted: false,
	}
	if err := s.repo.CreateFollowUp(ctx, fu); err != nil {
		return nil, err
	}
	return fu, nil
}

func (s *JamaahService) ListFollowUps(ctx context.Context, orgID uuid.UUID, completed bool, page, limit int) ([]model.FollowUp, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListFollowUps(ctx, orgID, completed, limit, offset)
}

func (s *JamaahService) CompleteFollowUp(ctx context.Context, id, orgID uuid.UUID) error {
	return s.repo.CompleteFollowUp(ctx, id, orgID)
}

func (s *JamaahService) UploadDocument(ctx context.Context, orgID uuid.UUID, jamaahID uuid.UUID, req model.UploadDocumentRequest, fileURL, fileName *string, fileSize *int64) (*model.JamaahDocument, error) {
	status := "belum_diterima"
	if req.Status != "" {
		status = req.Status
	}

	doc := &model.JamaahDocument{
		ID:        uuid.New(),
		JamaahID:  jamaahID,
		PackageID: nil,
		OrgID:     orgID,
		DocType:   req.DocType,
		Status:    status,
		FileURL:   fileURL,
		FileName:  fileName,
		FileSize:  fileSize,
		Notes:     req.Notes,
	}
	if err := s.repo.CreateDocument(ctx, doc); err != nil {
		return nil, err
	}
	return doc, nil
}

func (s *JamaahService) ListDocuments(ctx context.Context, orgID, jamaahID uuid.UUID) ([]model.JamaahDocument, error) {
	return s.repo.ListDocuments(ctx, orgID, jamaahID)
}

func (s *JamaahService) UpdateDocumentStatus(ctx context.Context, orgID uuid.UUID, id uuid.UUID, status string, verifiedBy *uuid.UUID, notes string) error {
	return s.repo.UpdateDocumentStatus(ctx, orgID, id, status, verifiedBy, notes)
}

func (s *JamaahService) GetDashboardAlerts(ctx context.Context, orgID uuid.UUID) (*model.DashboardAlerts, error) {
	expiring90, err := s.repo.GetPassportExpiring(ctx, orgID, 90)
	if err != nil {
		return nil, fmt.Errorf("get passport expiring 90: %w", err)
	}
	expiring30, err := s.repo.GetPassportExpiring(ctx, orgID, 30)
	if err != nil {
		return nil, fmt.Errorf("get passport expiring 30: %w", err)
	}

	overdueFollowUps, err := s.repo.ListFollowUps(ctx, orgID, false, 50, 0)
	if err != nil {
		return nil, fmt.Errorf("get overdue follow-ups: %w", err)
	}

	return &model.DashboardAlerts{
		PassportExpiring90: expiring90,
		PassportExpiring30: expiring30,
		OverdueFollowUps:   overdueFollowUps,
	}, nil
}

func parseDate(s string) (*time.Time, error) {
	if s == "" {
		return nil, nil
	}
	formats := []string{"2006-01-02", "2006-01-02T15:04:05Z", "2006-01-02T15:04:05"}
	for _, f := range formats {
		if t, err := time.Parse(f, s); err == nil {
			return &t, nil
		}
	}
	return nil, fmt.Errorf("invalid date format: %s", s)
}
package service

import (
	"context"
	"fmt"

	"github.com/google/uuid"
	"github.com/jamaah-in/v2/internal/package/model"
	"github.com/jamaah-in/v2/internal/package/repository"
)

type PackageService struct {
	repo *repository.PackageRepo
}

func NewPackageService(repo *repository.PackageRepo) *PackageService {
	return &PackageService{repo: repo}
}

func (s *PackageService) CreatePackage(ctx context.Context, orgID uuid.UUID, req model.CreatePackageRequest) (*model.Package, error) {
	slug := repository.GenerateSlug(req.Name)
	taken, err := s.repo.IsSlugTaken(ctx, slug, nil)
	if err != nil {
		return nil, err
	}
	if taken {
		for i := 1; i < 100; i++ {
			candidate := fmt.Sprintf("%s-%d", slug, i)
			taken, err = s.repo.IsSlugTaken(ctx, candidate, nil)
			if err != nil {
				return nil, err
			}
			if !taken {
				slug = candidate
				break
			}
		}
	}

	depDate, err := repository.ParseDate(req.DepartureDate)
	if err != nil {
		return nil, fmt.Errorf("departure_date: %w", err)
	}
	retDate, err := repository.ParseDate(req.ReturnDate)
	if err != nil {
		return nil, fmt.Errorf("return_date: %w", err)
	}

	pkg := &model.Package{
		ID:                   uuid.New(),
		OrgID:                orgID,
		Name:                 req.Name,
		Slug:                 slug,
		Description:          req.Description,
		PackageType:          req.PackageType,
		DepartureDate:        depDate,
		ReturnDate:           retDate,
		TotalSeats:           req.TotalSeats,
		Airline:              req.Airline,
		FlightNumberGo:       req.FlightNumberGo,
		FlightNumberReturn:   req.FlightNumberReturn,
		HotelMakkahName:      req.HotelMakkahName,
		HotelMakkahStars:     req.HotelMakkahStars,
		HotelMakkahNights:    req.HotelMakkahNights,
		HotelMakkahDistance:  req.HotelMakkahDistance,
		HotelMadinahName:     req.HotelMadinahName,
		HotelMadinahStars:    req.HotelMadinahStars,
		HotelMadinahNights:   req.HotelMadinahNights,
		HotelMadinahDistance: req.HotelMadinahDistance,
		Itinerary:            req.Itinerary,
		IsPublished:           false,
		Status:               "draft",
	}

	if err := s.repo.CreatePackage(ctx, pkg); err != nil {
		return nil, err
	}

	for i, tierReq := range req.PricingTiers {
		tier := &model.PricingTier{
			ID:         uuid.New(),
			PackageID:  pkg.ID,
			RoomType:   tierReq.RoomType,
			Price:      tierReq.Price,
			Label:      tierReq.Label,
			IsEarlyBird: tierReq.IsEarlyBird,
			SortOrder:  i,
		}
		if tierReq.EarlyBirdExpiresAt != nil {
			t, err := repository.ParseDate(tierReq.EarlyBirdExpiresAt)
			if err == nil && t != nil {
				tier.EarlyBirdExpiresAt = t
			}
		}
		if err := s.repo.CreatePricingTier(ctx, tier); err != nil {
			return nil, fmt.Errorf("create pricing tier: %w", err)
		}
	}

	for i, ccReq := range req.CostComponents {
		cc := &model.CostComponent{
			ID:              uuid.New(),
			PackageID:       pkg.ID,
			Name:            ccReq.Name,
			Category:        ccReq.Category,
			AmountPerPerson: ccReq.AmountPerPerson,
			Quantity:        ccReq.Quantity,
			TotalAmount:     ccReq.AmountPerPerson * int64(ccReq.Quantity),
			SortOrder:       i,
		}
		if err := s.repo.CreateCostComponent(ctx, cc); err != nil {
			return nil, fmt.Errorf("create cost component: %w", err)
		}
	}

	return s.repo.GetPackageByID(ctx, pkg.ID)
}

func (s *PackageService) GetPackage(ctx context.Context, id uuid.UUID) (*model.Package, error) {
	return s.repo.GetPackageByID(ctx, id)
}

func (s *PackageService) GetPackageBySlug(ctx context.Context, slug string) (*model.Package, error) {
	return s.repo.GetPackageBySlug(ctx, slug)
}

func (s *PackageService) ListPackages(ctx context.Context, orgID uuid.UUID, status string, page, limit int) ([]model.Package, int, error) {
	if page < 1 {
		page = 1
	}
	if limit < 1 || limit > 100 {
		limit = 20
	}
	offset := (page - 1) * limit
	return s.repo.ListPackages(ctx, orgID, status, offset, limit)
}

func (s *PackageService) UpdatePackage(ctx context.Context, id uuid.UUID, req model.UpdatePackageRequest) (*model.Package, error) {
	pkg, err := s.repo.GetPackageByID(ctx, id)
	if err != nil {
		return nil, err
	}

	if req.Name != nil {
		pkg.Name = *req.Name
	}
	if req.PackageType != nil {
		pkg.PackageType = *req.PackageType
	}
	if req.DepartureDate != nil {
		d, err := repository.ParseDate(req.DepartureDate)
		if err != nil {
			return nil, err
		}
		pkg.DepartureDate = d
	}
	if req.ReturnDate != nil {
		d, err := repository.ParseDate(req.ReturnDate)
		if err != nil {
			return nil, err
		}
		pkg.ReturnDate = d
	}
	if req.TotalSeats != nil {
		pkg.TotalSeats = *req.TotalSeats
	}
	if req.Description != nil {
		pkg.Description = req.Description
	}
	if req.Airline != nil {
		pkg.Airline = req.Airline
	}
	if req.FlightNumberGo != nil {
		pkg.FlightNumberGo = req.FlightNumberGo
	}
	if req.FlightNumberReturn != nil {
		pkg.FlightNumberReturn = req.FlightNumberReturn
	}
	if req.HotelMakkahName != nil {
		pkg.HotelMakkahName = req.HotelMakkahName
	}
	if req.HotelMakkahStars != nil {
		pkg.HotelMakkahStars = req.HotelMakkahStars
	}
	if req.HotelMakkahNights != nil {
		pkg.HotelMakkahNights = req.HotelMakkahNights
	}
	if req.HotelMakkahDistance != nil {
		pkg.HotelMakkahDistance = req.HotelMakkahDistance
	}
	if req.HotelMadinahName != nil {
		pkg.HotelMadinahName = req.HotelMadinahName
	}
	if req.HotelMadinahStars != nil {
		pkg.HotelMadinahStars = req.HotelMadinahStars
	}
	if req.HotelMadinahNights != nil {
		pkg.HotelMadinahNights = req.HotelMadinahNights
	}
	if req.HotelMadinahDistance != nil {
		pkg.HotelMadinahDistance = req.HotelMadinahDistance
	}
	if req.Itinerary != nil {
		pkg.Itinerary = req.Itinerary
	}
	if req.IsPublished != nil {
		pkg.IsPublished = *req.IsPublished
	}

	if err := s.repo.UpdatePackage(ctx, pkg); err != nil {
		return nil, err
	}
	return s.repo.GetPackageByID(ctx, id)
}

func (s *PackageService) DeletePackage(ctx context.Context, id uuid.UUID) error {
	return s.repo.DeletePackage(ctx, id)
}

func (s *PackageService) UpdatePackageStatus(ctx context.Context, id uuid.UUID, status string) (*model.Package, error) {
	if err := s.repo.UpdatePackageStatus(ctx, id, status); err != nil {
		return nil, err
	}
	return s.repo.GetPackageByID(ctx, id)
}

func (s *PackageService) GetPackageQuota(ctx context.Context, id uuid.UUID) (*model.PackageQuota, error) {
	pkg, err := s.repo.GetPackageByID(ctx, id)
	if err != nil {
		return nil, err
	}
	return &model.PackageQuota{
		TotalSeats:    pkg.TotalSeats,
		ReservedSeats: pkg.ReservedSeats,
		Available:     pkg.TotalSeats - pkg.ReservedSeats,
	}, nil
}

func (s *PackageService) GetProfitProjection(ctx context.Context, id uuid.UUID) (*model.PackageProfitProjection, error) {
	return s.repo.GetProfitProjection(ctx, id)
}

func (s *PackageService) CreatePricingTier(ctx context.Context, packageID uuid.UUID, req model.CreatePricingTierRequest) (*model.PricingTier, error) {
	if _, err := s.repo.GetPackageByID(ctx, packageID); err != nil {
		return nil, err
	}
	tier := &model.PricingTier{
		ID:          uuid.New(),
		PackageID:   packageID,
		RoomType:    req.RoomType,
		Price:       req.Price,
		Label:       req.Label,
		IsEarlyBird: req.IsEarlyBird,
		SortOrder:   req.SortOrder,
	}
	if req.EarlyBirdExpiresAt != nil {
		t, err := repository.ParseDate(req.EarlyBirdExpiresAt)
		if err == nil && t != nil {
			tier.EarlyBirdExpiresAt = t
		}
	}
	if err := s.repo.CreatePricingTier(ctx, tier); err != nil {
		return nil, err
	}
	return tier, nil
}

func (s *PackageService) UpdatePricingTier(ctx context.Context, tierID uuid.UUID, req model.CreatePricingTierRequest) (*model.PricingTier, error) {
	tiers, err := s.repo.GetPricingTiers(ctx, uuid.Nil)
	_ = tiers
	if err != nil {
		return nil, err
	}
	tier := &model.PricingTier{
		ID:          tierID,
		RoomType:    req.RoomType,
		Price:       req.Price,
		Label:       req.Label,
		IsEarlyBird: req.IsEarlyBird,
		SortOrder:   req.SortOrder,
	}
	if req.EarlyBirdExpiresAt != nil {
		t, err := repository.ParseDate(req.EarlyBirdExpiresAt)
		if err == nil && t != nil {
			tier.EarlyBirdExpiresAt = t
		}
	}
	if err := s.repo.UpdatePricingTier(ctx, tier); err != nil {
		return nil, err
	}
	return tier, nil
}

func (s *PackageService) DeletePricingTier(ctx context.Context, tierID uuid.UUID) error {
	return s.repo.DeletePricingTier(ctx, tierID)
}

func (s *PackageService) CreateCostComponent(ctx context.Context, packageID uuid.UUID, req model.CreateCostComponentRequest) (*model.CostComponent, error) {
	if _, err := s.repo.GetPackageByID(ctx, packageID); err != nil {
		return nil, err
	}
cc := &model.CostComponent{
		ID:              uuid.New(),
		PackageID:       packageID,
		Name:            req.Name,
		Category:        req.Category,
		AmountPerPerson: req.AmountPerPerson,
		Quantity:        req.Quantity,
		SortOrder:       req.SortOrder,
	}
	if err := s.repo.CreateCostComponent(ctx, cc); err != nil {
		return nil, err
	}
	return cc, nil
}

func (s *PackageService) UpdateCostComponent(ctx context.Context, ccID uuid.UUID, req model.CreateCostComponentRequest) (*model.CostComponent, error) {
	cc := &model.CostComponent{
		ID:              ccID,
		Name:            req.Name,
		Category:        req.Category,
		AmountPerPerson: req.AmountPerPerson,
		Quantity:        req.Quantity,
		SortOrder:       req.SortOrder,
	}
	if err := s.repo.UpdateCostComponent(ctx, cc); err != nil {
		return nil, err
	}
	return cc, nil
}

func (s *PackageService) DeleteCostComponent(ctx context.Context, ccID uuid.UUID) error {
	return s.repo.DeleteCostComponent(ctx, ccID)
}
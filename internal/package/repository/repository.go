package repository

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jamaah-in/v2/internal/package/model"
)

type PackageRepo struct {
	pool *pgxpool.Pool
}

func NewPackageRepo(pool *pgxpool.Pool) *PackageRepo {
	return &PackageRepo{pool: pool}
}

func (r *PackageRepo) CreatePackage(ctx context.Context, pkg *model.Package) error {
	query := `
		INSERT INTO packages (id, org_id, name, slug, description, package_type, departure_date, return_date,
			total_seats, airline, flight_number_go, flight_number_return,
			hotel_makkah_name, hotel_makkah_stars, hotel_makkah_nights, hotel_makkah_distance,
			hotel_madinah_name, hotel_madinah_stars, hotel_madinah_nights, hotel_madinah_distance,
			itinerary, is_published, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23)
		RETURNING created_at, updated_at`
	err := r.pool.QueryRow(ctx, query,
		pkg.ID, pkg.OrgID, pkg.Name, pkg.Slug, pkg.Description, pkg.PackageType,
		pkg.DepartureDate, pkg.ReturnDate, pkg.TotalSeats,
		pkg.Airline, pkg.FlightNumberGo, pkg.FlightNumberReturn,
		pkg.HotelMakkahName, pkg.HotelMakkahStars, pkg.HotelMakkahNights, pkg.HotelMakkahDistance,
		pkg.HotelMadinahName, pkg.HotelMadinahStars, pkg.HotelMadinahNights, pkg.HotelMadinahDistance,
		pkg.Itinerary, pkg.IsPublished, pkg.Status,
	).Scan(&pkg.CreatedAt, &pkg.UpdatedAt)
	if err != nil {
		if strings.Contains(err.Error(), "duplicate key") || strings.Contains(err.Error(), "unique constraint") {
			return ErrSlugExists
		}
		return fmt.Errorf("create package: %w", err)
	}
	return nil
}

func (r *PackageRepo) GetPackageByID(ctx context.Context, id uuid.UUID) (*model.Package, error) {
	pkg := &model.Package{}
	query := `SELECT id, org_id, name, slug, description, package_type, departure_date, return_date,
		duration_days, total_seats, reserved_seats, airline, flight_number_go, flight_number_return,
		hotel_makkah_name, hotel_makkah_stars, hotel_makkah_nights, hotel_makkah_distance,
		hotel_madinah_name, hotel_madinah_stars, hotel_madinah_nights, hotel_madinah_distance,
		itinerary, is_published, status, created_at, updated_at
		FROM packages WHERE id = $1`
	err := r.pool.QueryRow(ctx, query, id).Scan(
		&pkg.ID, &pkg.OrgID, &pkg.Name, &pkg.Slug, &pkg.Description, &pkg.PackageType,
		&pkg.DepartureDate, &pkg.ReturnDate, &pkg.DurationDays, &pkg.TotalSeats, &pkg.ReservedSeats,
		&pkg.Airline, &pkg.FlightNumberGo, &pkg.FlightNumberReturn,
		&pkg.HotelMakkahName, &pkg.HotelMakkahStars, &pkg.HotelMakkahNights, &pkg.HotelMakkahDistance,
		&pkg.HotelMadinahName, &pkg.HotelMadinahStars, &pkg.HotelMadinahNights, &pkg.HotelMadinahDistance,
		&pkg.Itinerary, &pkg.IsPublished, &pkg.Status, &pkg.CreatedAt, &pkg.UpdatedAt,
	)
	if err == pgx.ErrNoRows {
		return nil, ErrPackageNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("get package: %w", err)
	}
	pkg.PricingTiers, _ = r.GetPricingTiers(ctx, pkg.ID)
	pkg.CostComponents, _ = r.GetCostComponents(ctx, pkg.ID)
	return pkg, nil
}

func (r *PackageRepo) GetPackageBySlug(ctx context.Context, slug string) (*model.Package, error) {
	var id uuid.UUID
	err := r.pool.QueryRow(ctx, `SELECT id FROM packages WHERE slug = $1`, slug).Scan(&id)
	if err == pgx.ErrNoRows {
		return nil, ErrPackageNotFound
	}
	if err != nil {
		return nil, err
	}
	return r.GetPackageByID(ctx, id)
}

func (r *PackageRepo) ListPackages(ctx context.Context, orgID uuid.UUID, status string, offset, limit int) ([]model.Package, int, error) {
	countQuery := `SELECT COUNT(*) FROM packages WHERE org_id = $1`
	listQuery := `SELECT id, org_id, name, slug, description, package_type, departure_date, return_date,
		duration_days, total_seats, reserved_seats, airline, flight_number_go, flight_number_return,
		hotel_makkah_name, hotel_makkah_stars, hotel_makkah_nights, hotel_makkah_distance,
		hotel_madinah_name, hotel_madinah_stars, hotel_madinah_nights, hotel_madinah_distance,
		itinerary, is_published, status, created_at, updated_at
		FROM packages WHERE org_id = $1`

	args := []any{orgID}
	argIdx := 2

	if status != "" {
		countQuery += fmt.Sprintf(" AND status = $%d", argIdx)
		listQuery += fmt.Sprintf(" AND status = $%d", argIdx)
		args = append(args, status)
		argIdx++
	}

	var total int
	countArgs := args[:len(args)]
	if err := r.pool.QueryRow(ctx, countQuery, countArgs...).Scan(&total); err != nil {
		return nil, 0, err
	}

	listQuery += fmt.Sprintf(" ORDER BY created_at DESC LIMIT $%d OFFSET $%d", argIdx, argIdx+1)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, listQuery, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	packages := []model.Package{}
	for rows.Next() {
		var pkg model.Package
		if err := rows.Scan(
			&pkg.ID, &pkg.OrgID, &pkg.Name, &pkg.Slug, &pkg.Description, &pkg.PackageType,
			&pkg.DepartureDate, &pkg.ReturnDate, &pkg.DurationDays, &pkg.TotalSeats, &pkg.ReservedSeats,
			&pkg.Airline, &pkg.FlightNumberGo, &pkg.FlightNumberReturn,
			&pkg.HotelMakkahName, &pkg.HotelMakkahStars, &pkg.HotelMakkahNights, &pkg.HotelMakkahDistance,
			&pkg.HotelMadinahName, &pkg.HotelMadinahStars, &pkg.HotelMadinahNights, &pkg.HotelMadinahDistance,
			&pkg.Itinerary, &pkg.IsPublished, &pkg.Status, &pkg.CreatedAt, &pkg.UpdatedAt,
		); err != nil {
			return nil, 0, err
		}
		pkg.PricingTiers, _ = r.GetPricingTiers(ctx, pkg.ID)
		packages = append(packages, pkg)
	}
	return packages, total, nil
}

func (r *PackageRepo) UpdatePackage(ctx context.Context, pkg *model.Package) error {
	query := `UPDATE packages SET name = $2, description = $3, package_type = $4, departure_date = $5, return_date = $6,
		total_seats = $7, airline = $8, flight_number_go = $9, flight_number_return = $10,
		hotel_makkah_name = $11, hotel_makkah_stars = $12, hotel_makkah_nights = $13, hotel_makkah_distance = $14,
		hotel_madinah_name = $15, hotel_madinah_stars = $16, hotel_madinah_nights = $17, hotel_madinah_distance = $18,
		itinerary = $19, is_published = $20, status = $21, updated_at = NOW()
		WHERE id = $1`
	result, err := r.pool.Exec(ctx, query,
		pkg.ID, pkg.Name, pkg.Description, pkg.PackageType, pkg.DepartureDate, pkg.ReturnDate,
		pkg.TotalSeats, pkg.Airline, pkg.FlightNumberGo, pkg.FlightNumberReturn,
		pkg.HotelMakkahName, pkg.HotelMakkahStars, pkg.HotelMakkahNights, pkg.HotelMakkahDistance,
		pkg.HotelMadinahName, pkg.HotelMadinahStars, pkg.HotelMadinahNights, pkg.HotelMadinahDistance,
		pkg.Itinerary, pkg.IsPublished, pkg.Status,
	)
	if err != nil {
		return fmt.Errorf("update package: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrPackageNotFound
	}
	return nil
}

func (r *PackageRepo) DeletePackage(ctx context.Context, id uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM packages WHERE id = $1`, id)
	if err != nil {
		return fmt.Errorf("delete package: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrPackageNotFound
	}
	return nil
}

func (r *PackageRepo) UpdatePackageStatus(ctx context.Context, id uuid.UUID, status string) error {
	result, err := r.pool.Exec(ctx, `UPDATE packages SET status = $2, updated_at = NOW() WHERE id = $1`, id, status)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrPackageNotFound
	}
	return nil
}

func (r *PackageRepo) UpdateReservedSeats(ctx context.Context, id uuid.UUID, delta int) error {
	query := `UPDATE packages SET reserved_seats = reserved_seats + $2, updated_at = NOW() WHERE id = $1`
	result, err := r.pool.Exec(ctx, query, id, delta)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrPackageNotFound
	}
	return nil
}

func (r *PackageRepo) IsSlugTaken(ctx context.Context, slug string, excludeID *uuid.UUID) (bool, error) {
	var exists bool
	if excludeID != nil {
		err := r.pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM packages WHERE slug = $1 AND id != $2)`, slug, excludeID).Scan(&exists)
		return exists, err
	}
	err := r.pool.QueryRow(ctx, `SELECT EXISTS(SELECT 1 FROM packages WHERE slug = $1)`, slug).Scan(&exists)
	return exists, err
}

func (r *PackageRepo) CreatePricingTier(ctx context.Context, tier *model.PricingTier) error {
	query := `INSERT INTO pricing_tiers (id, package_id, room_type, price, label, is_early_bird, early_bird_expires_at, sort_order)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING created_at, updated_at`
	return r.pool.QueryRow(ctx, query,
		tier.ID, tier.PackageID, tier.RoomType, tier.Price, tier.Label,
		tier.IsEarlyBird, tier.EarlyBirdExpiresAt, tier.SortOrder,
	).Scan(&tier.CreatedAt, &tier.UpdatedAt)
}

func (r *PackageRepo) GetPricingTiers(ctx context.Context, packageID uuid.UUID) ([]model.PricingTier, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, package_id, room_type, price, label, is_early_bird, early_bird_expires_at, sort_order, created_at, updated_at
		FROM pricing_tiers WHERE package_id = $1 ORDER BY sort_order`, packageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	tiers := []model.PricingTier{}
	for rows.Next() {
		var t model.PricingTier
		if err := rows.Scan(&t.ID, &t.PackageID, &t.RoomType, &t.Price, &t.Label, &t.IsEarlyBird, &t.EarlyBirdExpiresAt, &t.SortOrder, &t.CreatedAt, &t.UpdatedAt); err != nil {
			return nil, err
		}
		tiers = append(tiers, t)
	}
	return tiers, nil
}

func (r *PackageRepo) UpdatePricingTier(ctx context.Context, tier *model.PricingTier) error {
	query := `UPDATE pricing_tiers SET room_type = $2, price = $3, label = $4, is_early_bird = $5, early_bird_expires_at = $6, sort_order = $7, updated_at = NOW() WHERE id = $1`
	result, err := r.pool.Exec(ctx, query, tier.ID, tier.RoomType, tier.Price, tier.Label, tier.IsEarlyBird, tier.EarlyBirdExpiresAt, tier.SortOrder)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrTierNotFound
	}
	return nil
}

func (r *PackageRepo) GetPricingTierByID(ctx context.Context, id uuid.UUID) (*model.PricingTier, error) {
	tier := &model.PricingTier{}
	err := r.pool.QueryRow(ctx, `SELECT id, package_id, room_type, price, label, is_early_bird, early_bird_expires_at, sort_order, created_at, updated_at
		FROM pricing_tiers WHERE id = $1`, id).Scan(
		&tier.ID, &tier.PackageID, &tier.RoomType, &tier.Price, &tier.Label, &tier.IsEarlyBird, &tier.EarlyBirdExpiresAt, &tier.SortOrder, &tier.CreatedAt, &tier.UpdatedAt,
	)
	if err == pgx.ErrNoRows {
		return nil, ErrTierNotFound
	}
	if err != nil {
		return nil, err
	}
	return tier, nil
}

func (r *PackageRepo) DeletePricingTier(ctx context.Context, id uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM pricing_tiers WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrTierNotFound
	}
	return nil
}

func (r *PackageRepo) CreateCostComponent(ctx context.Context, cc *model.CostComponent) error {
	query := `INSERT INTO cost_components (id, package_id, name, category, amount_per_person, quantity, sort_order)
		VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING created_at, updated_at, total_amount`
	return r.pool.QueryRow(ctx, query,
		cc.ID, cc.PackageID, cc.Name, cc.Category, cc.AmountPerPerson, cc.Quantity, cc.SortOrder,
	).Scan(&cc.CreatedAt, &cc.UpdatedAt, &cc.TotalAmount)
}

func (r *PackageRepo) GetCostComponents(ctx context.Context, packageID uuid.UUID) ([]model.CostComponent, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, package_id, name, category, amount_per_person, quantity, total_amount, sort_order, created_at, updated_at
		FROM cost_components WHERE package_id = $1 ORDER BY sort_order`, packageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	ccs := []model.CostComponent{}
	for rows.Next() {
		var cc model.CostComponent
		if err := rows.Scan(&cc.ID, &cc.PackageID, &cc.Name, &cc.Category, &cc.AmountPerPerson, &cc.Quantity, &cc.TotalAmount, &cc.SortOrder, &cc.CreatedAt, &cc.UpdatedAt); err != nil {
			return nil, err
		}
		ccs = append(ccs, cc)
	}
	return ccs, nil
}

func (r *PackageRepo) UpdateCostComponent(ctx context.Context, cc *model.CostComponent) error {
	query := `UPDATE cost_components SET name = $2, category = $3, amount_per_person = $4, quantity = $5, sort_order = $6, updated_at = NOW() WHERE id = $1`
	result, err := r.pool.Exec(ctx, query, cc.ID, cc.Name, cc.Category, cc.AmountPerPerson, cc.Quantity, cc.SortOrder)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrCostNotFound
	}
	return nil
}

func (r *PackageRepo) GetCostComponentByID(ctx context.Context, id uuid.UUID) (*model.CostComponent, error) {
	cc := &model.CostComponent{}
	err := r.pool.QueryRow(ctx, `SELECT id, package_id, name, category, amount_per_person, quantity, total_amount, sort_order, created_at, updated_at
		FROM cost_components WHERE id = $1`, id).Scan(
		&cc.ID, &cc.PackageID, &cc.Name, &cc.Category, &cc.AmountPerPerson, &cc.Quantity, &cc.TotalAmount, &cc.SortOrder, &cc.CreatedAt, &cc.UpdatedAt,
	)
	if err == pgx.ErrNoRows {
		return nil, ErrCostNotFound
	}
	if err != nil {
		return nil, err
	}
	return cc, nil
}

func (r *PackageRepo) DeleteCostComponent(ctx context.Context, id uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM cost_components WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrCostNotFound
	}
	return nil
}

func (r *PackageRepo) GetProfitProjection(ctx context.Context, id uuid.UUID) (*model.PackageProfitProjection, error) {
	pkg, err := r.GetPackageByID(ctx, id)
	if err != nil {
		return nil, err
	}

	var totalHPP int64 = 0
	for _, cc := range pkg.CostComponents {
		totalHPP += cc.TotalAmount
	}

	var lowestPrice int64 = 0
	if len(pkg.PricingTiers) > 0 {
		lowestPrice = pkg.PricingTiers[0].Price
		for _, t := range pkg.PricingTiers {
			if t.Price < lowestPrice {
				lowestPrice = t.Price
			}
		}
	}

	return &model.PackageProfitProjection{
		PackageID:                pkg.ID,
		PackageName:              pkg.Name,
		TotalSeats:               pkg.TotalSeats,
		ReservedSeats:            pkg.ReservedSeats,
		HppPerPerson:             totalHPP,
		TotalHPP:                 totalHPP * int64(pkg.TotalSeats),
		LowestPrice:              lowestPrice,
		ProjectedMarginPerPerson: lowestPrice - totalHPP,
	}, nil
}

func GenerateSlug(name string) string {
	slug := strings.ToLower(name)
	slug = strings.ReplaceAll(slug, " ", "-")
	slug = strings.Map(func(r rune) rune {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			return r
		}
		return -1
	}, slug)
	for strings.Contains(slug, "--") {
		slug = strings.ReplaceAll(slug, "--", "-")
	}
	slug = strings.Trim(slug, "-")
	if len(slug) > 100 {
		slug = slug[:100]
	}
	if len(slug) == 0 {
		slug = fmt.Sprintf("pkg-%s", uuid.New().String()[:8])
	}
	return slug
}

var (
	ErrPackageNotFound = fmt.Errorf("package not found")
	ErrSlugExists      = fmt.Errorf("package slug already exists")
	ErrTierNotFound    = fmt.Errorf("pricing tier not found")
	ErrCostNotFound    = fmt.Errorf("cost component not found")
)

func ParseDate(s *string) (*time.Time, error) {
	if s == nil || *s == "" {
		return nil, nil
	}
	t, err := time.Parse("2006-01-02", *s)
	if err != nil {
		return nil, fmt.Errorf("invalid date format: %w", err)
	}
	return &t, nil
}

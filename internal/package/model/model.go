package model

import (
	"time"

	"github.com/google/uuid"
)

type PackageType string

const (
	PackageTypeUmrohReguler PackageType = "umroh_reguler"
	PackageTypeUmrohPlus    PackageType = "umroh_plus"
	PackageTypeHajiKhusus   PackageType = "haji_khusus"
	PackageTypeHajiONHPlus  PackageType = "haji_onh_plus"
)

func ValidPackageTypes() []string {
	return []string{"umroh_reguler", "umroh_plus", "haji_khusus", "haji_onh_plus"}
}

type PackageStatus string

const (
	StatusDraft   PackageStatus = "draft"
	StatusOpen    PackageStatus = "open"
	StatusFull    PackageStatus = "full"
	StatusClosed  PackageStatus = "closed"
	StatusDone    PackageStatus = "done"
)

func ValidPackageStatuses() []string {
	return []string{"draft", "open", "full", "closed", "done"}
}

type RoomType string

const (
	RoomQuad   RoomType = "quad"
	RoomTriple RoomType = "triple"
	RoomDouble RoomType = "double"
	RoomSingle RoomType = "single"
)

func ValidRoomTypes() []string {
	return []string{"quad", "triple", "double", "single"}
}

type CostCategory string

const (
	CostFlight        CostCategory = "flight"
	CostHotelMakkah   CostCategory = "hotel_makkah"
	CostHotelMadinah  CostCategory = "hotel_madinah"
	CostVisa          CostCategory = "visa"
	CostTransport     CostCategory = "transport"
	CostGuide        CostCategory = "guide"
	CostEquipment    CostCategory = "equipment"
	CostCatering     CostCategory = "catering"
	CostOther        CostCategory = "other"
)

func ValidCostCategories() []string {
	return []string{"flight", "hotel_makkah", "hotel_madinah", "visa", "transport", "guide", "equipment", "catering", "other"}
}

type Package struct {
	ID                   uuid.UUID  `json:"id" db:"id"`
	OrgID                uuid.UUID  `json:"org_id" db:"org_id"`
	Name                 string     `json:"name" db:"name"`
	Slug                 string     `json:"slug" db:"slug"`
	Description          *string    `json:"description,omitempty" db:"description"`
	PackageType          string     `json:"package_type" db:"package_type"`
	DepartureDate        *time.Time `json:"departure_date,omitempty" db:"departure_date"`
	ReturnDate           *time.Time `json:"return_date,omitempty" db:"return_date"`
	DurationDays         *int       `json:"duration_days,omitempty" db:"duration_days"`
	TotalSeats           int        `json:"total_seats" db:"total_seats"`
	ReservedSeats        int        `json:"reserved_seats" db:"reserved_seats"`
	Airline              *string    `json:"airline,omitempty" db:"airline"`
	FlightNumberGo       *string    `json:"flight_number_go,omitempty" db:"flight_number_go"`
	FlightNumberReturn   *string    `json:"flight_number_return,omitempty" db:"flight_number_return"`
	HotelMakkahName      *string    `json:"hotel_makkah_name,omitempty" db:"hotel_makkah_name"`
	HotelMakkahStars     *int       `json:"hotel_makkah_stars,omitempty" db:"hotel_makkah_stars"`
	HotelMakkahNights    *int       `json:"hotel_makkah_nights,omitempty" db:"hotel_makkah_nights"`
	HotelMakkahDistance  *string    `json:"hotel_makkah_distance,omitempty" db:"hotel_makkah_distance"`
	HotelMadinahName     *string    `json:"hotel_madinah_name,omitempty" db:"hotel_madinah_name"`
	HotelMadinahStars    *int       `json:"hotel_madinah_stars,omitempty" db:"hotel_madinah_stars"`
	HotelMadinahNights   *int       `json:"hotel_madinah_nights,omitempty" db:"hotel_madinah_nights"`
	HotelMadinahDistance *string    `json:"hotel_madinah_distance,omitempty" db:"hotel_madinah_distance"`
	Itinerary            *string    `json:"itinerary,omitempty" db:"itinerary"`
	IsPublished          bool       `json:"is_published" db:"is_published"`
	Status               string     `json:"status" db:"status"`
	PricingTiers         []PricingTier  `json:"pricing_tiers,omitempty" db:"-"`
	CostComponents       []CostComponent `json:"cost_components,omitempty" db:"-"`
	CreatedAt            time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt            time.Time  `json:"updated_at" db:"updated_at"`
}

type PricingTier struct {
	ID                  uuid.UUID  `json:"id" db:"id"`
	PackageID           uuid.UUID  `json:"package_id" db:"package_id"`
	RoomType            string     `json:"room_type" db:"room_type"`
	Price                int64      `json:"price" db:"price"`
	Label                *string    `json:"label,omitempty" db:"label"`
	IsEarlyBird         bool       `json:"is_early_bird" db:"is_early_bird"`
	EarlyBirdExpiresAt  *time.Time `json:"early_bird_expires_at,omitempty" db:"early_bird_expires_at"`
	SortOrder            int        `json:"sort_order" db:"sort_order"`
	CreatedAt           time.Time  `json:"created_at" db:"created_at"`
	UpdatedAt           time.Time  `json:"updated_at" db:"updated_at"`
}

type CostComponent struct {
	ID               uuid.UUID `json:"id" db:"id"`
	PackageID        uuid.UUID `json:"package_id" db:"package_id"`
	Name             string    `json:"name" db:"name"`
	Category         string    `json:"category" db:"category"`
	AmountPerPerson  int64     `json:"amount_per_person" db:"amount_per_person"`
	Quantity         int       `json:"quantity" db:"quantity"`
	TotalAmount      int64     `json:"total_amount" db:"total_amount"`
	SortOrder        int       `json:"sort_order" db:"sort_order"`
	CreatedAt        time.Time `json:"created_at" db:"created_at"`
	UpdatedAt        time.Time `json:"updated_at" db:"updated_at"`
}

type PackageQuota struct {
	TotalSeats    int `json:"total_seats"`
	ReservedSeats int `json:"reserved_seats"`
	Available     int `json:"available"`
}

type CreatePackageRequest struct {
	Name               string     `json:"name" validate:"required,min=2,max=255"`
	PackageType        string     `json:"package_type" validate:"required,oneof=umroh_reguler umroh_plus haji_khusus haji_onh_plus"`
	DepartureDate      *string    `json:"departure_date,omitempty" validate:"required"`
	ReturnDate         *string    `json:"return_date,omitempty" validate:"required"`
	TotalSeats         int        `json:"total_seats" validate:"required,min=1"`
	Description        *string    `json:"description,omitempty"`
	Airline            *string    `json:"airline,omitempty"`
	FlightNumberGo     *string    `json:"flight_number_go,omitempty"`
	FlightNumberReturn *string    `json:"flight_number_return,omitempty"`
	HotelMakkahName    *string    `json:"hotel_makkah_name,omitempty"`
	HotelMakkahStars   *int       `json:"hotel_makkah_stars,omitempty"`
	HotelMakkahNights  *int       `json:"hotel_makkah_nights,omitempty"`
	HotelMakkahDistance *string   `json:"hotel_makkah_distance,omitempty"`
	HotelMadinahName   *string    `json:"hotel_madinah_name,omitempty"`
	HotelMadinahStars  *int       `json:"hotel_madinah_stars,omitempty"`
	HotelMadinahNights *int       `json:"hotel_madinah_nights,omitempty"`
	HotelMadinahDistance *string  `json:"hotel_madinah_distance,omitempty"`
	Itinerary          *string    `json:"itinerary,omitempty"`
	PricingTiers       []CreatePricingTierRequest `json:"pricing_tiers,omitempty"`
	CostComponents     []CreateCostComponentRequest `json:"cost_components,omitempty"`
}

type CreatePricingTierRequest struct {
	RoomType           string `json:"room_type" validate:"required,oneof=quad triple double single"`
	Price              int64  `json:"price" validate:"required,min=1"`
	Label              *string `json:"label,omitempty"`
	IsEarlyBird        bool   `json:"is_early_bird"`
	EarlyBirdExpiresAt *string `json:"early_bird_expires_at,omitempty"`
	SortOrder          int    `json:"sort_order"`
}

type CreateCostComponentRequest struct {
	Name            string `json:"name" validate:"required"`
	Category        string `json:"category" validate:"required,oneof=flight hotel_makkah hotel_madinah visa transport guide equipment catering other"`
	AmountPerPerson int64  `json:"amount_per_person" validate:"min=0"`
	Quantity        int    `json:"quantity" validate:"min=1"`
	SortOrder       int    `json:"sort_order"`
}

type UpdatePackageRequest struct {
	Name               *string `json:"name,omitempty"`
	PackageType        *string `json:"package_type,omitempty"`
	DepartureDate      *string `json:"departure_date,omitempty"`
	ReturnDate         *string `json:"return_date,omitempty"`
	TotalSeats         *int    `json:"total_seats,omitempty"`
	Description        *string `json:"description,omitempty"`
	Airline            *string `json:"airline,omitempty"`
	FlightNumberGo     *string `json:"flight_number_go,omitempty"`
	FlightNumberReturn *string `json:"flight_number_return,omitempty"`
	HotelMakkahName    *string `json:"hotel_makkah_name,omitempty"`
	HotelMakkahStars   *int    `json:"hotel_makkah_stars,omitempty"`
	HotelMakkahNights  *int    `json:"hotel_makkah_nights,omitempty"`
	HotelMakkahDistance *string `json:"hotel_makkah_distance,omitempty"`
	HotelMadinahName   *string `json:"hotel_madinah_name,omitempty"`
	HotelMadinahStars  *int    `json:"hotel_madinah_stars,omitempty"`
	HotelMadinahNights *int    `json:"hotel_madinah_nights,omitempty"`
	HotelMadinahDistance *string `json:"hotel_madinah_distance,omitempty"`
	Itinerary          *string `json:"itinerary,omitempty"`
	IsPublished        *bool   `json:"is_published,omitempty"`
}

type UpdatePackageStatusRequest struct {
	Status string `json:"status" validate:"required,oneof=draft open full closed done"`
}

type ListPackagesRequest struct {
	Status string `json:"status,omitempty"`
	Page   int    `json:"page,omitempty"`
	Limit  int    `json:"limit,omitempty"`
}

type PackageProfitProjection struct {
	PackageID              uuid.UUID `json:"package_id"`
	PackageName            string    `json:"package_name"`
	TotalSeats             int       `json:"total_seats"`
	ReservedSeats          int       `json:"reserved_seats"`
	HppPerPerson           int64     `json:"hpp_per_person"`
	TotalHPP               int64     `json:"total_hpp"`
	LowestPrice            int64     `json:"lowest_price"`
	ProjectedMarginPerPerson int64   `json:"projected_margin_per_person"`
}
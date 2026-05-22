package service

import (
	"testing"

	"github.com/google/uuid"

	"github.com/jamaah-in/v2/internal/finance/model"
)

func TestProjectedCategoryTotalsMultipliesBySeats(t *testing.T) {
	pkg := &packageSnapshot{
		ID:         uuid.New(),
		TotalSeats: 40,
		CostComponents: []packageCostComponent{
			{Category: "flight", AmountPerPerson: 5000000, Quantity: 1},
			{Category: "equipment", AmountPerPerson: 1000000, Quantity: 1},
		},
	}

	got, total := projectedCategoryTotals(pkg)

	if got["flight"] != 200000000 {
		t.Fatalf("flight total = %d, want %d", got["flight"], int64(200000000))
	}
	if got["equipment"] != 40000000 {
		t.Fatalf("equipment total = %d, want %d", got["equipment"], int64(40000000))
	}
	if total != 240000000 {
		t.Fatalf("total = %d, want %d", total, int64(240000000))
	}
}

func TestExpenseCategoryTotalsUsesDescriptionForAccommodation(t *testing.T) {
	expenses := []model.TripExpense{
		{Category: "accommodation", Description: "Hotel Makkah 4 malam", AmountIDR: 150000000},
		{Category: "accommodation", Description: "Hotel Madinah 3 malam", AmountIDR: 80000000},
		{Category: "guide", Description: "Muthawwif", AmountIDR: 20000000},
	}

	got := expenseCategoryTotals(expenses)

	if got["hotel_makkah"] != 150000000 {
		t.Fatalf("hotel_makkah = %d, want %d", got["hotel_makkah"], int64(150000000))
	}
	if got["hotel_madinah"] != 80000000 {
		t.Fatalf("hotel_madinah = %d, want %d", got["hotel_madinah"], int64(80000000))
	}
	if got["guide"] != 20000000 {
		t.Fatalf("guide = %d, want %d", got["guide"], int64(20000000))
	}
}

func TestNormalizeVendorBillCategoryMapsPerlengkapanToEquipment(t *testing.T) {
	vendorType := "perlengkapan"
	bill := vendorBillListItem{
		Description: "Distribusi koper dan ihram",
		AmountIDR:   40000000,
		VendorType:  &vendorType,
	}

	got := normalizeVendorBillCategory(bill)
	if got != "equipment" {
		t.Fatalf("category = %s, want equipment", got)
	}
}

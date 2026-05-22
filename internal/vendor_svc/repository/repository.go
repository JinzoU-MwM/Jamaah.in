package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/jamaah-in/v2/internal/vendor_svc/model"
)

type VendorRepo struct {
	pool *pgxpool.Pool
}

func NewVendorRepo(pool *pgxpool.Pool) *VendorRepo {
	return &VendorRepo{pool: pool}
}

var (
	ErrVendorNotFound  = fmt.Errorf("vendor not found")
	ErrBillNotFound    = fmt.Errorf("vendor bill not found")
	ErrPaymentNotFound = fmt.Errorf("vendor payment not found")
)

// --- Vendor Master ---

const vendorCols = `id, org_id, name, type, npwp, address, pic_name, pic_phone, pic_email, bank_name, bank_account_number, bank_account_name, notes, created_at, updated_at`

const vendorInsertCols = `id, org_id, name, type, npwp, address, pic_name, pic_phone, pic_email, bank_name, bank_account_number, bank_account_name, notes`

func (r *VendorRepo) scanVendor(scanner interface{ Scan(dest ...interface{}) error }) (*model.Vendor, error) {
	v := &model.Vendor{}
	err := scanner.Scan(&v.ID, &v.OrgID, &v.Name, &v.Type, &v.NPWP, &v.Address,
		&v.PICName, &v.PICPhone, &v.PICEmail, &v.BankName, &v.BankAccountNumber,
		&v.BankAccountName, &v.Notes, &v.CreatedAt, &v.UpdatedAt)
	return v, err
}

func (r *VendorRepo) CreateVendor(ctx context.Context, v *model.Vendor) error {
	query := fmt.Sprintf(`INSERT INTO vendors (%s) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
		RETURNING created_at, updated_at`, vendorInsertCols)
	return r.pool.QueryRow(ctx, query,
		v.ID, v.OrgID, v.Name, v.Type, v.NPWP, v.Address,
		v.PICName, v.PICPhone, v.PICEmail, v.BankName, v.BankAccountNumber,
		v.BankAccountName, v.Notes,
	).Scan(&v.CreatedAt, &v.UpdatedAt)
}

func (r *VendorRepo) GetVendorByID(ctx context.Context, id, orgID uuid.UUID) (*model.Vendor, error) {
	v, err := r.scanVendor(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM vendors WHERE id = $1 AND org_id = $2`, vendorCols), id, orgID))
	if err != nil {
		return nil, ErrVendorNotFound
	}
	return v, nil
}

func (r *VendorRepo) UpdateVendor(ctx context.Context, v *model.Vendor) error {
	query := `UPDATE vendors SET name=$2, type=$3, npwp=$4, address=$5, pic_name=$6, pic_phone=$7, pic_email=$8,
		bank_name=$9, bank_account_number=$10, bank_account_name=$11, notes=$12, updated_at=NOW()
		WHERE id = $1 AND org_id = $13`
	result, err := r.pool.Exec(ctx, query,
		v.ID, v.Name, v.Type, v.NPWP, v.Address, v.PICName, v.PICPhone, v.PICEmail,
		v.BankName, v.BankAccountNumber, v.BankAccountName, v.Notes, v.OrgID)
	if err != nil {
		return fmt.Errorf("update vendor: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrVendorNotFound
	}
	return nil
}

func (r *VendorRepo) DeleteVendor(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM vendors WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrVendorNotFound
	}
	return nil
}

func (r *VendorRepo) ListVendors(ctx context.Context, orgID uuid.UUID, vendorType, search string, offset, limit int) ([]model.Vendor, int, error) {
	countQuery := `SELECT COUNT(*) FROM vendors WHERE org_id = $1`
	query := fmt.Sprintf(`SELECT %s FROM vendors WHERE org_id = $1`, vendorCols)
	args := []any{orgID}
	argIdx := 2

	if vendorType != "" {
		countQuery += fmt.Sprintf(` AND type = $%d`, argIdx)
		query += fmt.Sprintf(` AND type = $%d`, argIdx)
		args = append(args, vendorType)
		argIdx++
	}
	if search != "" {
		countQuery += fmt.Sprintf(` AND name ILIKE $%d`, argIdx)
		query += fmt.Sprintf(` AND name ILIKE $%d`, argIdx)
		args = append(args, "%"+search+"%")
		argIdx++
	}

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	query += fmt.Sprintf(` ORDER BY name ASC LIMIT $%d OFFSET $%d`, argIdx, argIdx+1)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	vendors := []model.Vendor{}
	for rows.Next() {
		v, err := r.scanVendor(rows)
		if err != nil {
			return nil, 0, err
		}
		vendors = append(vendors, *v)
	}
	return vendors, total, nil
}

// --- Vendor Bills ---

const billCols = `vb.id, vb.org_id, vb.vendor_id, vb.package_id, vb.description, vb.amount, vb.currency, vb.exchange_rate, vb.amount_idr, vb.paid_amount, vb.due_date, vb.status, vb.created_at, vb.updated_at, v.name AS vendor_name`

func (r *VendorRepo) scanBill(scanner interface{ Scan(dest ...interface{}) error }) (*model.VendorBill, error) {
	b := &model.VendorBill{}
	err := scanner.Scan(&b.ID, &b.OrgID, &b.VendorID, &b.PackageID, &b.Description,
		&b.Amount, &b.Currency, &b.ExchangeRate, &b.AmountIDR, &b.PaidAmount,
		&b.DueDate, &b.Status, &b.CreatedAt, &b.UpdatedAt, &b.VendorName)
	return b, err
}

const billInsertCols = `id, org_id, vendor_id, package_id, description, amount, currency, exchange_rate, due_date, status`

func (r *VendorRepo) CreateBill(ctx context.Context, b *model.VendorBill) error {
	query := fmt.Sprintf(`INSERT INTO vendor_bills (%s) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
		RETURNING amount_idr, paid_amount, created_at, updated_at`, billInsertCols)
	return r.pool.QueryRow(ctx, query,
		b.ID, b.OrgID, b.VendorID, b.PackageID, b.Description,
		b.Amount, b.Currency, b.ExchangeRate, b.DueDate, b.Status,
	).Scan(&b.AmountIDR, &b.PaidAmount, &b.CreatedAt, &b.UpdatedAt)
}

func (r *VendorRepo) GetBillByID(ctx context.Context, id, orgID uuid.UUID) (*model.VendorBill, error) {
	query := fmt.Sprintf(`SELECT %s FROM vendor_bills vb JOIN vendors v ON vb.vendor_id = v.id WHERE vb.id = $1 AND vb.org_id = $2`, billCols)
	b, err := r.scanBill(r.pool.QueryRow(ctx, query, id, orgID))
	if err != nil {
		return nil, ErrBillNotFound
	}
	return b, nil
}

func (r *VendorRepo) UpdateBill(ctx context.Context, b *model.VendorBill) error {
	query := `UPDATE vendor_bills SET description=$2, amount=$3, currency=$4, exchange_rate=$5,
		due_date=$6, status=$7, updated_at=NOW() WHERE id = $1 AND org_id = $8`
	result, err := r.pool.Exec(ctx, query,
		b.ID, b.Description, b.Amount, b.Currency, b.ExchangeRate, b.DueDate, b.Status, b.OrgID)
	if err != nil {
		return fmt.Errorf("update vendor bill: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrBillNotFound
	}
	return nil
}

func (r *VendorRepo) DeleteBill(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM vendor_bills WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrBillNotFound
	}
	return nil
}

func (r *VendorRepo) ListBills(ctx context.Context, orgID uuid.UUID, vendorID *uuid.UUID, packageID *uuid.UUID, status string, offset, limit int) ([]model.VendorBill, int, error) {
	countQuery := `SELECT COUNT(*) FROM vendor_bills vb JOIN vendors v ON vb.vendor_id = v.id WHERE vb.org_id = $1`
	query := fmt.Sprintf(`SELECT %s FROM vendor_bills vb JOIN vendors v ON vb.vendor_id = v.id WHERE vb.org_id = $1`, billCols)
	args := []any{orgID}
	argIdx := 2

	if vendorID != nil {
		countQuery += fmt.Sprintf(` AND vb.vendor_id = $%d`, argIdx)
		query += fmt.Sprintf(` AND vb.vendor_id = $%d`, argIdx)
		args = append(args, *vendorID)
		argIdx++
	}
	if packageID != nil {
		countQuery += fmt.Sprintf(` AND vb.package_id = $%d`, argIdx)
		query += fmt.Sprintf(` AND vb.package_id = $%d`, argIdx)
		args = append(args, *packageID)
		argIdx++
	}
	if status != "" {
		countQuery += fmt.Sprintf(` AND vb.status = $%d`, argIdx)
		query += fmt.Sprintf(` AND vb.status = $%d`, argIdx)
		args = append(args, status)
		argIdx++
	}

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	query += fmt.Sprintf(` ORDER BY vb.due_date ASC NULLS LAST, vb.created_at DESC LIMIT $%d OFFSET $%d`, argIdx, argIdx+1)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	bills := []model.VendorBill{}
	for rows.Next() {
		b, err := r.scanBill(rows)
		if err != nil {
			return nil, 0, err
		}
		bills = append(bills, *b)
	}
	return bills, total, nil
}

func (r *VendorRepo) GetOverdueBills(ctx context.Context, orgID uuid.UUID) ([]model.VendorBill, error) {
	query := fmt.Sprintf(`SELECT %s FROM vendor_bills vb JOIN vendors v ON vb.vendor_id = v.id
		WHERE vb.org_id = $1 AND vb.status IN ('belum_bayar','sebagian') AND vb.due_date IS NOT NULL AND vb.due_date < NOW()
		ORDER BY vb.due_date ASC`, billCols)
	rows, err := r.pool.Query(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	bills := []model.VendorBill{}
	for rows.Next() {
		b, err := r.scanBill(rows)
		if err != nil {
			return nil, err
		}
		bills = append(bills, *b)
	}
	return bills, nil
}

func (r *VendorRepo) GetBillsDueSoon(ctx context.Context, orgID uuid.UUID, withinDays int) ([]model.VendorBill, error) {
	query := fmt.Sprintf(`SELECT %s FROM vendor_bills vb JOIN vendors v ON vb.vendor_id = v.id
		WHERE vb.org_id = $1 AND vb.status IN ('belum_bayar','sebagian') AND vb.due_date IS NOT NULL
		AND vb.due_date >= NOW() AND vb.due_date <= NOW() + INTERVAL '%d days'
		ORDER BY vb.due_date ASC`, billCols, withinDays)
	rows, err := r.pool.Query(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	bills := []model.VendorBill{}
	for rows.Next() {
		b, err := r.scanBill(rows)
		if err != nil {
			return nil, err
		}
		bills = append(bills, *b)
	}
	return bills, nil
}

func (r *VendorRepo) UpdateBillPaidAmount(ctx context.Context, id uuid.UUID) error {
	_, err := r.pool.Exec(ctx, `UPDATE vendor_bills SET paid_amount = (
		SELECT COALESCE(SUM(vp.amount_idr), 0) FROM vendor_payments vp WHERE vp.vendor_bill_id = $1
	), updated_at = NOW() WHERE id = $1`, id)
	return err
}

func (r *VendorRepo) UpdateBillStatus(ctx context.Context, id uuid.UUID, status string) error {
	_, err := r.pool.Exec(ctx, `UPDATE vendor_bills SET status = $2, updated_at = NOW() WHERE id = $1`, id, status)
	return err
}

// --- Vendor Payments ---

const paymentCols = `id, org_id, vendor_bill_id, vendor_id, payment_date, amount, currency, exchange_rate, amount_idr, source_account, transfer_proof_url, notes, created_at`

func (r *VendorRepo) scanPayment(scanner interface{ Scan(dest ...interface{}) error }) (*model.VendorPayment, error) {
	p := &model.VendorPayment{}
	err := scanner.Scan(&p.ID, &p.OrgID, &p.VendorBillID, &p.VendorID,
		&p.PaymentDate, &p.Amount, &p.Currency, &p.ExchangeRate, &p.AmountIDR,
		&p.SourceAccount, &p.TransferProofURL, &p.Notes, &p.CreatedAt)
	return p, err
}

const paymentInsertCols = `id, org_id, vendor_bill_id, vendor_id, payment_date, amount, currency, exchange_rate, source_account, transfer_proof_url, notes`

func (r *VendorRepo) CreatePayment(ctx context.Context, p *model.VendorPayment) error {
	query := fmt.Sprintf(`INSERT INTO vendor_payments (%s) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
		RETURNING amount_idr, created_at`, paymentInsertCols)
	return r.pool.QueryRow(ctx, query,
		p.ID, p.OrgID, p.VendorBillID, p.VendorID, p.PaymentDate,
		p.Amount, p.Currency, p.ExchangeRate, p.SourceAccount, p.TransferProofURL, p.Notes,
	).Scan(&p.AmountIDR, &p.CreatedAt)
}

func (r *VendorRepo) GetPaymentByID(ctx context.Context, id, orgID uuid.UUID) (*model.VendorPayment, error) {
	p, err := r.scanPayment(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM vendor_payments WHERE id = $1 AND org_id = $2`, paymentCols), id, orgID))
	if err != nil {
		return nil, ErrPaymentNotFound
	}
	return p, nil
}

func (r *VendorRepo) DeletePayment(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM vendor_payments WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrPaymentNotFound
	}
	return nil
}

func (r *VendorRepo) ListPaymentsByBill(ctx context.Context, billID, orgID uuid.UUID) ([]model.VendorPayment, error) {
	rows, err := r.pool.Query(ctx, fmt.Sprintf(`SELECT %s FROM vendor_payments WHERE vendor_bill_id = $1 AND org_id = $2 ORDER BY payment_date DESC`, paymentCols), billID, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	payments := []model.VendorPayment{}
	for rows.Next() {
		p, err := r.scanPayment(rows)
		if err != nil {
			return nil, err
		}
		payments = append(payments, *p)
	}
	return payments, nil
}

func (r *VendorRepo) ListPaymentsByVendor(ctx context.Context, vendorID, orgID uuid.UUID, offset, limit int) ([]model.VendorPayment, int, error) {
	countQuery := `SELECT COUNT(*) FROM vendor_payments WHERE vendor_id = $1 AND org_id = $2`
	query := fmt.Sprintf(`SELECT %s FROM vendor_payments WHERE vendor_id = $1 AND org_id = $2 ORDER BY payment_date DESC LIMIT $3 OFFSET $4`, paymentCols)

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, vendorID, orgID).Scan(&total); err != nil {
		return nil, 0, err
	}

	rows, err := r.pool.Query(ctx, query, vendorID, orgID, limit, offset)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	payments := []model.VendorPayment{}
	for rows.Next() {
		p, err := r.scanPayment(rows)
		if err != nil {
			return nil, 0, err
		}
		payments = append(payments, *p)
	}
	return payments, total, nil
}

// --- Debt Summary ---

func (r *VendorRepo) GetDebtSummary(ctx context.Context, orgID uuid.UUID, vendorID *uuid.UUID) (*model.VendorDebtSummary, error) {
	s := &model.VendorDebtSummary{
		ByStatus: make(map[string]model.BillStatusSummary),
	}

	baseQuery := `SELECT COALESCE(SUM(vb.amount_idr), 0), COALESCE(SUM(vb.paid_amount), 0), COUNT(*) FROM vendor_bills vb WHERE vb.org_id = $1`
	args := []any{orgID}
	if vendorID != nil {
		baseQuery += ` AND vb.vendor_id = $2`
		args = append(args, *vendorID)
	}

	if err := r.pool.QueryRow(ctx, baseQuery, args...).Scan(&s.TotalAmountIDR, &s.TotalPaidIDR, &s.TotalBills); err != nil {
		return nil, err
	}
	s.TotalOutstandingIDR = s.TotalAmountIDR - s.TotalPaidIDR

	statusQuery := `SELECT vb.status, COUNT(*), COALESCE(SUM(vb.amount_idr), 0) FROM vendor_bills vb WHERE vb.org_id = $1`
	statusArgs := []any{orgID}
	if vendorID != nil {
		statusQuery += ` AND vb.vendor_id = $2`
		statusArgs = append(statusArgs, *vendorID)
	}
	statusQuery += ` GROUP BY vb.status`

	rows, err := r.pool.Query(ctx, statusQuery, statusArgs...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var status string
		var count int
		var total int64
		if err := rows.Scan(&status, &count, &total); err != nil {
			return nil, err
		}
		s.ByStatus[status] = model.BillStatusSummary{Count: count, TotalAmount: total}
	}

	return s, nil
}

// --- ParseDate helper ---

func ParseDate(s string) (*time.Time, error) {
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
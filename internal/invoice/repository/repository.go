package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/jamaah-in/v2/internal/invoice/model"
)

type InvoiceRepo struct {
	pool *pgxpool.Pool
}

func NewInvoiceRepo(pool *pgxpool.Pool) *InvoiceRepo {
	return &InvoiceRepo{pool: pool}
}

var (
	ErrInvoiceNotFound  = fmt.Errorf("invoice not found")
	ErrDuplicateNumber  = fmt.Errorf("invoice number already exists")
	ErrScheduleNotFound = fmt.Errorf("payment schedule not found")
	ErrPaymentNotFound  = fmt.Errorf("payment not found")
	ErrAlreadyCancelled = fmt.Errorf("invoice already cancelled")
	ErrAlreadyLunas     = fmt.Errorf("invoice already fully paid")
)

var invoiceCols = `id, org_id, invoice_number, jamaah_id, package_id, registration_id, room_type,
	price_snapshot, discount_amount, surcharge_amount, total_amount, amount_paid, amount_remaining,
	payment_scheme, status, issued_at, due_date, cancelled_at, cancelled_reason, notes, created_at, updated_at`

func (r *InvoiceRepo) scanInvoice(scanner interface{ Scan(dest ...interface{}) error }) (*model.Invoice, error) {
	inv := &model.Invoice{}
	err := scanner.Scan(&inv.ID, &inv.OrgID, &inv.InvoiceNumber, &inv.JamaahID, &inv.PackageID, &inv.RegistrationID,
		&inv.RoomType, &inv.PriceSnapshot, &inv.DiscountAmount, &inv.SurchargeAmount, &inv.TotalAmount,
		&inv.AmountPaid, &inv.AmountRemaining, &inv.PaymentScheme, &inv.Status, &inv.IssuedAt,
		&inv.DueDate, &inv.CancelledAt, &inv.CancelledReason, &inv.Notes, &inv.CreatedAt, &inv.UpdatedAt)
	return inv, err
}

func (r *InvoiceRepo) CreateInvoice(ctx context.Context, inv *model.Invoice) error {
	query := `INSERT INTO invoices (id, org_id, invoice_number, jamaah_id, package_id, registration_id,
		room_type, price_snapshot, discount_amount, surcharge_amount, total_amount, amount_paid, amount_remaining,
		payment_scheme, status, due_date, notes)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17)
		RETURNING issued_at, created_at, updated_at`
	err := r.pool.QueryRow(ctx, query,
		inv.ID, inv.OrgID, inv.InvoiceNumber, inv.JamaahID, inv.PackageID, inv.RegistrationID,
		inv.RoomType, inv.PriceSnapshot, inv.DiscountAmount, inv.SurchargeAmount, inv.TotalAmount,
		inv.AmountPaid, inv.AmountRemaining, inv.PaymentScheme, inv.Status, inv.DueDate, inv.Notes,
	).Scan(&inv.IssuedAt, &inv.CreatedAt, &inv.UpdatedAt)
	if err != nil {
		if isDuplicate(err) {
			return ErrDuplicateNumber
		}
		return fmt.Errorf("create invoice: %w", err)
	}
	return nil
}

func (r *InvoiceRepo) GetInvoiceByID(ctx context.Context, id, orgID uuid.UUID) (*model.Invoice, error) {
	inv, err := r.scanInvoice(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM invoices WHERE id = $1 AND org_id = $2`, invoiceCols), id, orgID))
	if err != nil {
		return nil, ErrInvoiceNotFound
	}
	return inv, nil
}

func (r *InvoiceRepo) GetInvoiceByNumber(ctx context.Context, orgID uuid.UUID, number string) (*model.Invoice, error) {
	inv, err := r.scanInvoice(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM invoices WHERE org_id = $1 AND invoice_number = $2`, invoiceCols), orgID, number))
	if err != nil {
		return nil, ErrInvoiceNotFound
	}
	return inv, nil
}

func (r *InvoiceRepo) UpdateInvoice(ctx context.Context, inv *model.Invoice) error {
	query := `UPDATE invoices SET discount_amount=$2, surcharge_amount=$3, total_amount=$4,
		amount_paid=$5, amount_remaining=$6, due_date=$7, notes=$8, status=$9, updated_at=NOW() WHERE id = $1 AND org_id = $10`
	result, err := r.pool.Exec(ctx, query,
		inv.ID, inv.DiscountAmount, inv.SurchargeAmount, inv.TotalAmount,
		inv.AmountPaid, inv.AmountRemaining, inv.DueDate, inv.Notes, inv.Status, inv.OrgID)
	if err != nil {
		return fmt.Errorf("update invoice: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrInvoiceNotFound
	}
	return nil
}

func (r *InvoiceRepo) CancelInvoice(ctx context.Context, id, orgID uuid.UUID, reason string) error {
	result, err := r.pool.Exec(ctx, `UPDATE invoices SET status = 'batal', cancelled_at = NOW(), cancelled_reason = $3, updated_at = NOW() WHERE id = $1 AND org_id = $2 AND status != 'batal'`, id, orgID, reason)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrAlreadyCancelled
	}
	return nil
}

func (r *InvoiceRepo) UpdateInvoiceStatus(ctx context.Context, id, orgID uuid.UUID, status string) error {
	result, err := r.pool.Exec(ctx, `UPDATE invoices SET status = $3, updated_at = NOW() WHERE id = $1 AND org_id = $2`, id, orgID, status)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrInvoiceNotFound
	}
	return nil
}

func (r *InvoiceRepo) ListInvoices(ctx context.Context, orgID uuid.UUID, status string, offset, limit int) ([]model.Invoice, int, error) {
	countQuery := `SELECT COUNT(*) FROM invoices WHERE org_id = $1`
	query := fmt.Sprintf(`SELECT %s FROM invoices WHERE org_id = $1`, invoiceCols)
	args := []any{orgID}
	if status != "" {
		countQuery += ` AND status = $2`
		query += ` AND status = $2`
		args = append(args, status)
	}

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	query += fmt.Sprintf(` ORDER BY created_at DESC LIMIT $%d OFFSET $%d`, len(args)+1, len(args)+2)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	invoices := []model.Invoice{}
	for rows.Next() {
		inv, err := r.scanInvoice(rows)
		if err != nil {
			return nil, 0, err
		}
		invoices = append(invoices, *inv)
	}
	if err := rows.Err(); err != nil {
		return nil, 0, err
	}
	return invoices, total, nil
}

func (r *InvoiceRepo) GetInvoicesByJamaah(ctx context.Context, orgID, jamaahID uuid.UUID) ([]model.Invoice, error) {
	rows, err := r.pool.Query(ctx, fmt.Sprintf(`SELECT %s FROM invoices WHERE org_id = $1 AND jamaah_id = $2 ORDER BY created_at DESC`, invoiceCols), orgID, jamaahID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	invoices := []model.Invoice{}
	for rows.Next() {
		inv, err := r.scanInvoice(rows)
		if err != nil {
			return nil, err
		}
		invoices = append(invoices, *inv)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return invoices, nil
}

func (r *InvoiceRepo) CreatePaymentSchedule(ctx context.Context, ps *model.PaymentSchedule) error {
	return r.pool.QueryRow(ctx, `INSERT INTO payment_schedules (id, invoice_id, installment_num, amount, due_date, description, is_paid)
		VALUES ($1,$2,$3,$4,$5,$6,$7) RETURNING created_at`,
		ps.ID, ps.InvoiceID, ps.InstallmentNum, ps.Amount, ps.DueDate, ps.Description, ps.IsPaid).Scan(&ps.CreatedAt)
}

func (r *InvoiceRepo) GetPaymentSchedules(ctx context.Context, invoiceID uuid.UUID) ([]model.PaymentSchedule, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, invoice_id, installment_num, amount, due_date, description, is_paid, paid_at, created_at
		FROM payment_schedules WHERE invoice_id = $1 ORDER BY installment_num`, invoiceID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	schedules := []model.PaymentSchedule{}
	for rows.Next() {
		var ps model.PaymentSchedule
		if err := rows.Scan(&ps.ID, &ps.InvoiceID, &ps.InstallmentNum, &ps.Amount, &ps.DueDate, &ps.Description, &ps.IsPaid, &ps.PaidAt, &ps.CreatedAt); err != nil {
			return nil, err
		}
		schedules = append(schedules, ps)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return schedules, nil
}

func (r *InvoiceRepo) MarkSchedulePaid(ctx context.Context, id uuid.UUID) error {
	now := time.Now()
	result, err := r.pool.Exec(ctx, `UPDATE payment_schedules SET is_paid = true, paid_at = $2 WHERE id = $1 AND is_paid = false`, id, now)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrScheduleNotFound
	}
	return nil
}

func (r *InvoiceRepo) CreatePayment(ctx context.Context, p *model.Payment) error {
	return r.pool.QueryRow(ctx, `INSERT INTO payments (id, org_id, invoice_id, amount, payment_method, bank_name, account_number, reference_number, proof_url, notes, received_by, paid_at)
		VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING created_at`,
		p.ID, p.OrgID, p.InvoiceID, p.Amount, p.PaymentMethod, p.BankName, p.AccountNumber,
		p.ReferenceNumber, p.ProofURL, p.Notes, p.ReceivedBy, p.PaidAt).Scan(&p.CreatedAt)
}

func (r *InvoiceRepo) GetPayments(ctx context.Context, invoiceID uuid.UUID) ([]model.Payment, error) {
	rows, err := r.pool.Query(ctx, `SELECT id, org_id, invoice_id, amount, payment_method, bank_name, account_number, reference_number, proof_url, notes, received_by, paid_at, created_at
		FROM payments WHERE invoice_id = $1 ORDER BY paid_at DESC`, invoiceID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	payments := []model.Payment{}
	for rows.Next() {
		var p model.Payment
		if err := rows.Scan(&p.ID, &p.OrgID, &p.InvoiceID, &p.Amount, &p.PaymentMethod, &p.BankName, &p.AccountNumber,
			&p.ReferenceNumber, &p.ProofURL, &p.Notes, &p.ReceivedBy, &p.PaidAt, &p.CreatedAt); err != nil {
			return nil, err
		}
		payments = append(payments, p)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return payments, nil
}

func (r *InvoiceRepo) GetSummary(ctx context.Context, orgID uuid.UUID) (*model.InvoiceSummary, error) {
	s := &model.InvoiceSummary{}
	err := r.pool.QueryRow(ctx, `SELECT COUNT(*), COALESCE(SUM(total_amount),0), COALESCE(SUM(amount_paid),0), COALESCE(SUM(amount_remaining),0),
		COUNT(*) FILTER (WHERE status IN ('belum_bayar','sebagian')),
		COUNT(*) FILTER (WHERE status IN ('belum_bayar','sebagian') AND due_date < NOW())
		FROM invoices WHERE org_id = $1 AND status != 'batal'`, orgID).Scan(
		&s.TotalInvoices, &s.TotalAmount, &s.TotalPaid, &s.TotalRemaining, &s.OutstandingCount, &s.OverdueCount)
	if err != nil {
		return nil, err
	}
	return s, nil
}

func (r *InvoiceRepo) GetPackageRevenue(ctx context.Context, orgID, packageID uuid.UUID) (*model.PackageRevenueSummary, error) {
	s := &model.PackageRevenueSummary{PackageID: packageID}
	err := r.pool.QueryRow(ctx, `SELECT COUNT(*) FILTER (WHERE status != 'batal'),
		COALESCE(SUM(total_amount) FILTER (WHERE status != 'batal'),0),
		COALESCE(SUM(amount_paid) FILTER (WHERE status != 'batal'),0),
		COALESCE(SUM(amount_remaining) FILTER (WHERE status != 'batal'),0),
		COUNT(*) FILTER (WHERE status = 'lunas'),
		COUNT(*) FILTER (WHERE status = 'sebagian'),
		COUNT(*) FILTER (WHERE status = 'belum_bayar'),
		COUNT(*) FILTER (WHERE status = 'batal')
		FROM invoices WHERE org_id = $1 AND package_id = $2`, orgID, packageID).Scan(
		&s.TotalInvoices, &s.TotalAmount, &s.TotalPaid, &s.TotalRemaining,
		&s.LunasCount, &s.SebagianCount, &s.BelumBayarCount, &s.BatalCount)
	if err != nil {
		return nil, err
	}
	return s, nil
}

func (r *InvoiceRepo) ListInvoicesByPackage(ctx context.Context, orgID, packageID uuid.UUID) ([]model.Invoice, error) {
	rows, err := r.pool.Query(ctx, fmt.Sprintf(`SELECT %s FROM invoices WHERE org_id = $1 AND package_id = $2 ORDER BY created_at DESC`, invoiceCols), orgID, packageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	invoices := []model.Invoice{}
	for rows.Next() {
		inv, err := r.scanInvoice(rows)
		if err != nil {
			return nil, err
		}
		invoices = append(invoices, *inv)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return invoices, nil
}

func GenerateInvoiceNumber(orgID uuid.UUID) string {
	now := time.Now()
	return fmt.Sprintf("INV-%s-%04d%02d%02d%04d", orgID.String()[:8], now.Year(), now.Month(), now.Day(), now.Nanosecond()/100000)
}

func isDuplicate(err error) bool {
	return err != nil && (contains(err.Error(), "unique constraint") || contains(err.Error(), "duplicate key"))
}

func contains(s, sub string) bool {
	return len(s) >= len(sub) && searchSubstring(s, sub)
}

func searchSubstring(s, sub string) bool {
	for i := 0; i <= len(s)-len(sub); i++ {
		if s[i:i+len(sub)] == sub {
			return true
		}
	}
	return false
}
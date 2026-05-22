package repository

import (
	"context"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/jamaah-in/v2/internal/finance/model"
)

type FinanceRepo struct {
	pool *pgxpool.Pool
}

func NewFinanceRepo(pool *pgxpool.Pool) *FinanceRepo {
	return &FinanceRepo{pool: pool}
}

var (
	ErrExpenseNotFound = fmt.Errorf("expense not found")
)

const expenseCols = `id, org_id, package_id, category, description, vendor_name, amount, currency, exchange_rate, amount_idr, expense_date, due_date, status, created_at, updated_at`

const insertCols = `id, org_id, package_id, category, description, vendor_name, amount, currency, exchange_rate, expense_date, due_date, status`

func (r *FinanceRepo) scanExpense(scanner interface{ Scan(dest ...interface{}) error }) (*model.TripExpense, error) {
	e := &model.TripExpense{}
	err := scanner.Scan(&e.ID, &e.OrgID, &e.PackageID, &e.Category, &e.Description, &e.VendorName,
		&e.Amount, &e.Currency, &e.ExchangeRate, &e.AmountIDR, &e.ExpenseDate, &e.DueDate,
		&e.Status, &e.CreatedAt, &e.UpdatedAt)
	return e, err
}

func (r *FinanceRepo) CreateExpense(ctx context.Context, e *model.TripExpense) error {
	query := fmt.Sprintf(`INSERT INTO trip_expenses (%s) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
		RETURNING amount_idr, created_at, updated_at`, insertCols)
	err := r.pool.QueryRow(ctx, query,
		e.ID, e.OrgID, e.PackageID, e.Category, e.Description, e.VendorName,
		e.Amount, e.Currency, e.ExchangeRate, e.ExpenseDate, e.DueDate, e.Status,
	).Scan(&e.AmountIDR, &e.CreatedAt, &e.UpdatedAt)
	if err != nil {
		return fmt.Errorf("create expense: %w", err)
	}
	return nil
}

func (r *FinanceRepo) GetExpenseByID(ctx context.Context, id, orgID uuid.UUID) (*model.TripExpense, error) {
	e, err := r.scanExpense(r.pool.QueryRow(ctx, fmt.Sprintf(`SELECT %s FROM trip_expenses WHERE id = $1 AND org_id = $2`, expenseCols), id, orgID))
	if err != nil {
		return nil, ErrExpenseNotFound
	}
	return e, nil
}

func (r *FinanceRepo) UpdateExpense(ctx context.Context, e *model.TripExpense) error {
	query := `UPDATE trip_expenses SET category=$2, description=$3, vendor_name=$4, amount=$5, currency=$6, exchange_rate=$7,
		expense_date=$8, due_date=$9, status=$10, updated_at=NOW() WHERE id = $1 AND org_id = $11`
	result, err := r.pool.Exec(ctx, query,
		e.ID, e.Category, e.Description, e.VendorName, e.Amount, e.Currency, e.ExchangeRate,
		e.ExpenseDate, e.DueDate, e.Status, e.OrgID)
	if err != nil {
		return fmt.Errorf("update expense: %w", err)
	}
	if result.RowsAffected() == 0 {
		return ErrExpenseNotFound
	}
	return nil
}

func (r *FinanceRepo) DeleteExpense(ctx context.Context, id, orgID uuid.UUID) error {
	result, err := r.pool.Exec(ctx, `DELETE FROM trip_expenses WHERE id = $1 AND org_id = $2`, id, orgID)
	if err != nil {
		return err
	}
	if result.RowsAffected() == 0 {
		return ErrExpenseNotFound
	}
	return nil
}

func (r *FinanceRepo) ListExpenses(ctx context.Context, orgID uuid.UUID, category string, status string, offset, limit int) ([]model.TripExpense, int, error) {
	countQuery := `SELECT COUNT(*) FROM trip_expenses WHERE org_id = $1`
	query := fmt.Sprintf(`SELECT %s FROM trip_expenses WHERE org_id = $1`, expenseCols)
	args := []any{orgID}
	argIdx := 2

	if category != "" {
		countQuery += fmt.Sprintf(` AND category = $%d`, argIdx)
		query += fmt.Sprintf(` AND category = $%d`, argIdx)
		args = append(args, category)
		argIdx++
	}
	if status != "" {
		countQuery += fmt.Sprintf(` AND status = $%d`, argIdx)
		query += fmt.Sprintf(` AND status = $%d`, argIdx)
		args = append(args, status)
		argIdx++
	}

	var total int
	if err := r.pool.QueryRow(ctx, countQuery, args...).Scan(&total); err != nil {
		return nil, 0, err
	}

	query += fmt.Sprintf(` ORDER BY expense_date DESC LIMIT $%d OFFSET $%d`, argIdx, argIdx+1)
	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, 0, err
	}
	defer rows.Close()

	expenses := []model.TripExpense{}
	for rows.Next() {
		e, err := r.scanExpense(rows)
		if err != nil {
			return nil, 0, err
		}
		expenses = append(expenses, *e)
	}
	return expenses, total, nil
}

func (r *FinanceRepo) ListExpensesByPackage(ctx context.Context, orgID, packageID uuid.UUID) ([]model.TripExpense, error) {
	rows, err := r.pool.Query(ctx, fmt.Sprintf(`SELECT %s FROM trip_expenses WHERE org_id = $1 AND package_id = $2 ORDER BY expense_date DESC`, expenseCols), orgID, packageID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	expenses := []model.TripExpense{}
	for rows.Next() {
		e, err := r.scanExpense(rows)
		if err != nil {
			return nil, err
		}
		expenses = append(expenses, *e)
	}
	return expenses, nil
}

func (r *FinanceRepo) GetSummary(ctx context.Context, orgID uuid.UUID, packageID *uuid.UUID) (*model.ExpenseSummary, error) {
	query := `SELECT COALESCE(SUM(amount_idr), 0), COUNT(*) FROM trip_expenses WHERE org_id = $1`
	args := []any{orgID}
	if packageID != nil {
		query += ` AND package_id = $2`
		args = append(args, *packageID)
	}

	s := &model.ExpenseSummary{
		ByCategory: make(map[string]model.CategorySummary),
		ByStatus:   make(map[string]int64),
	}

	if err := r.pool.QueryRow(ctx, query, args...).Scan(&s.TotalAmountIDR, &s.TotalExpenses); err != nil {
		return nil, err
	}

	catQuery := `SELECT category, COUNT(*), COALESCE(SUM(amount_idr), 0) FROM trip_expenses WHERE org_id = $1`
	catArgs := []any{orgID}
	if packageID != nil {
		catQuery += ` AND package_id = $2`
		catArgs = append(catArgs, *packageID)
	}
	catQuery += ` GROUP BY category`

	rows, err := r.pool.Query(ctx, catQuery, catArgs...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	for rows.Next() {
		var cat string
		var count int
		var total int64
		if err := rows.Scan(&cat, &count, &total); err != nil {
			return nil, err
		}
		s.ByCategory[cat] = model.CategorySummary{Count: count, TotalAmount: total}
	}

	statusQuery := `SELECT status, COUNT(*) FROM trip_expenses WHERE org_id = $1`
	statusArgs := []any{orgID}
	if packageID != nil {
		statusQuery += ` AND package_id = $2`
		statusArgs = append(statusArgs, *packageID)
	}
	statusQuery += ` GROUP BY status`

	sRows, err := r.pool.Query(ctx, statusQuery, statusArgs...)
	if err != nil {
		return nil, err
	}
	defer sRows.Close()
	for sRows.Next() {
		var status string
		var count int64
		if err := sRows.Scan(&status, &count); err != nil {
			return nil, err
		}
		s.ByStatus[status] = count
	}

	return s, nil
}

func (r *FinanceRepo) GetOverdueExpenses(ctx context.Context, orgID uuid.UUID) ([]model.TripExpense, error) {
	query := fmt.Sprintf(`SELECT %s FROM trip_expenses WHERE org_id = $1 AND status IN ('belum_bayar', 'sebagian') AND due_date IS NOT NULL AND due_date < NOW() ORDER BY due_date ASC`, expenseCols)
	rows, err := r.pool.Query(ctx, query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	expenses := []model.TripExpense{}
	for rows.Next() {
		e, err := r.scanExpense(rows)
		if err != nil {
			return nil, err
		}
		expenses = append(expenses, *e)
	}
	return expenses, nil
}

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
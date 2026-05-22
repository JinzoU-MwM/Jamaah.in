# Jamaah.in v2 API Reference

**Base URL**: `http://localhost:8080/api/v1`
**Auth**: Bearer JWT token in `Authorization` header
**Content-Type**: `application/json`

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register new user + org |
| POST | `/auth/login` | No | Login, returns access_token + refresh_token |
| POST | `/auth/refresh` | No | Refresh access token |
| POST | `/auth/logout` | Yes | Logout (invalidate refresh token) |
| GET | `/auth/me` | Yes | Get current user profile |
| PUT | `/auth/me` | Yes | Update current user profile |

## Organizations & Teams

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/orgs/` | Yes | Create organization |
| GET | `/orgs/` | Yes | Get current organization |
| GET | `/orgs/members` | Yes | List team members |
| GET | `/orgs/users` | Yes | List users in org |
| POST | `/orgs/members` | Yes | Add team member |
| DELETE | `/orgs/members/:userId` | Yes | Remove team member |
| PUT | `/orgs/members/:userId/role` | Yes | Update member role |
| POST | `/orgs/invite` | Yes | Invite member by email |
| POST | `/invite/accept` | Yes | Accept invite |

## Packages

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/packages/` | Yes | Create package |
| GET | `/packages/` | Yes | List packages (paginated) |
| GET | `/packages/:id` | Yes | Get package detail |
| PUT | `/packages/:id` | Yes | Update package |
| DELETE | `/packages/:id` | Yes | Delete package |
| PATCH | `/packages/:id/status` | Yes | Update package status |
| GET | `/packages/:id/quota` | Yes | Get package quota |
| GET | `/packages/:id/profit` | Yes | Get profit projection |
| POST | `/packages/:id/tiers` | Yes | Create pricing tier |
| PUT | `/packages/:id/tiers/:tid` | Yes | Update pricing tier |
| DELETE | `/packages/:id/tiers/:tid` | Yes | Delete pricing tier |
| POST | `/packages/:id/costs` | Yes | Create cost component |
| PUT | `/packages/:id/costs/:cid` | Yes | Update cost component |
| DELETE | `/packages/:id/costs/:cid` | Yes | Delete cost component |
| GET | `/public/packages/:slug` | No | Public package page |

## Jamaah / CRM

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/jamaah/` | Yes | Create jamaah profile |
| GET | `/jamaah/` | Yes | List profiles (paginated) |
| GET | `/jamaah/search/nik/:nik` | Yes | Find by NIK |
| GET | `/jamaah/search/paspor/:paspor` | Yes | Find by passport |
| GET | `/jamaah/dashboard/alerts` | Yes | Dashboard alerts |
| GET | `/jamaah/:id` | Yes | Get profile |
| PUT | `/jamaah/:id` | Yes | Update profile |
| DELETE | `/jamaah/:id` | Yes | Delete profile |
| POST | `/jamaah/:id/register` | Yes | Register to package |
| GET | `/jamaah/:id/registrations/:pkgId` | Yes | Get registration |
| PATCH | `/jamaah/:id/registrations/:pkgId/status` | Yes | Update pipeline status |
| DELETE | `/jamaah/:id/registrations/:pkgId` | Yes | Remove from package |
| GET | `/jamaah/by-package/:pkgId` | Yes | List jamaah by package |
| POST | `/jamaah/:id/notes` | Yes | Add note |
| GET | `/jamaah/:id/notes` | Yes | List notes |
| POST | `/jamaah/:id/follow-ups` | Yes | Add follow-up |
| GET | `/jamaah/follow-ups` | Yes | List follow-ups |
| PATCH | `/jamaah/follow-ups/:followUpId/complete` | Yes | Complete follow-up |
| POST | `/jamaah/:id/documents` | Yes | Upload document |
| GET | `/jamaah/:id/documents` | Yes | List documents |
| PATCH | `/jamaah/:id/documents/:docId/status` | Yes | Update document status |

## Invoices

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/invoices/` | Yes | Create invoice |
| GET | `/invoices/` | Yes | List invoices (paginated) |
| GET | `/invoices/summary` | Yes | Invoice summary |
| GET | `/invoices/number/:number` | Yes | Get by invoice number |
| GET | `/invoices/jamaah/:jamaahId` | Yes | Get invoices by jamaah |
| GET | `/invoices/:id` | Yes | Get invoice detail |
| PUT | `/invoices/:id` | Yes | Update invoice |
| PATCH | `/invoices/:id/cancel` | Yes | Cancel invoice |
| POST | `/invoices/:id/schedules` | Yes | Create payment schedules |
| GET | `/invoices/:id/schedules` | Yes | Get payment schedules |
| POST | `/invoices/:id/payments` | Yes | Record payment |
| GET | `/invoices/:id/payments` | Yes | Get payments |

## Finance / Expenses

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/finance/expenses/` | Yes | Create expense |
| GET | `/finance/expenses/` | Yes | List expenses (paginated) |
| GET | `/finance/expenses/summary` | Yes | Expense summary |
| GET | `/finance/expenses/overdue` | Yes | Get overdue expenses |
| GET | `/finance/expenses/package/:pkgId` | Yes | Expenses by package |
| GET | `/finance/expenses/:id` | Yes | Get expense detail |
| PUT | `/finance/expenses/:id` | Yes | Update expense |
| DELETE | `/finance/expenses/:id` | Yes | Delete expense |

## Vendor & Biaya Operasional

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/vendors/` | Yes | Create vendor |
| GET | `/vendors/` | Yes | List vendors (filter: type, search) |
| GET | `/vendors/:id` | Yes | Get vendor detail |
| PUT | `/vendors/:id` | Yes | Update vendor |
| DELETE | `/vendors/:id` | Yes | Delete vendor (fails if has bills) |
| POST | `/vendors/bills` | Yes | Create vendor bill |
| GET | `/vendors/bills` | Yes | List bills (filter: vendor_id, package_id, status) |
| GET | `/vendors/bills/overdue` | Yes | Get overdue bills |
| GET | `/vendors/bills/due-soon` | Yes | Get bills due soon (default 7 days) |
| GET | `/vendors/bills/summary` | Yes | Vendor debt summary |
| GET | `/vendors/bills/:id` | Yes | Get bill detail |
| PUT | `/vendors/bills/:id` | Yes | Update bill |
| DELETE | `/vendors/bills/:id` | Yes | Delete bill |
| POST | `/vendors/bills/:billId/payments` | Yes | Record payment to vendor |
| GET | `/vendors/bills/:billId/payments` | Yes | List payments for a bill |
| GET | `/vendors/payments/:id` | Yes | Get payment detail |
| DELETE | `/vendors/payments/:id` | Yes | Delete payment |
| GET | `/vendors/:vendorId/payments` | Yes | List payments by vendor (paginated) |

## AI / OCR Scanner

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/scan/jobs` | Yes | Create scan job |
| GET | `/scan/jobs` | Yes | List scan jobs (paginated) |
| GET | `/scan/jobs/:id` | Yes | Get scan job detail |
| GET | `/scan/results/:id` | Yes | Get scan result |
| GET | `/scan/jobs/:jobId/results` | Yes | Get results by job |
| POST | `/export-templates/` | Yes | Create export template |
| GET | `/export-templates/` | Yes | List export templates |
| DELETE | `/export-templates/:id` | Yes | Delete export template |
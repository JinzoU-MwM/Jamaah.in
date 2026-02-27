# Jamaah.in — Improvement Roadmap

> Comprehensive improvement recommendations across Technical/Architecture, User Experience, Operations/DevOps, and Business/Features.
>
> **Date:** 2026-02-27  
> **Version:** v5.0 (P3)

---

## Table of Contents

1. [Technical/Architecture](#1-technicalarchitecture)
2. [User Experience](#2-user-experience)
3. [Operations/DevOps](#3-operationsdevops)
4. [Business/Features](#4-businessfeatures)
5. [Priority Matrix](#5-priority-matrix)

---

## 1. Technical/Architecture

### 1.1 Testing Strategy

| Area | Current State | Recommended | Priority |
|------|---------------|-------------|----------|
| **Unit Tests** | Minimal (`test_validators.py`, `test_cache.py`) | 80%+ coverage for services | 🔴 High |
| **Integration Tests** | Basic API tests (`test_api.py`) | Full endpoint coverage + DB transactions | 🔴 High |
| **E2E Tests** | None | Playwright/Cypress for critical flows | 🟡 Medium |
| **OCR Mocking** | Uses real API | Mock Gemini responses for faster tests | 🔴 High |

#### Action Items
- [ ] Add `pytest-mock` and `pytest-asyncio` to `requirements.txt`
- [ ] Create `tests/conftest.py` with database fixtures and auth mocks
- [ ] Mock Gemini API responses using `responses` library
- [ ] Add E2E tests with Playwright: Login → Upload → Process → Export

### 1.2 Error Handling & Logging

| Issue | Impact | Solution |
|-------|--------|-----------|
| Generic exception handlers | Difficult debugging | Structured error responses with error codes |
| No distributed tracing | Can't track requests across services | Add `opentelemetry` + Sentry integration |
| Email failures silent | Users don't get OTP | Add dead letter queue + retry with exponential backoff |
| No request ID | Hard to correlate logs | Add `X-Request-ID` header middleware |

#### Recommended Stack
```python
# requirements.txt additions
sentry-sdk[fastapi]      # Error tracking
structlog                # Structured logging
opentelemetry-api        # Distributed tracing
opentelemetry-sdk        # Distributed tracing
```

### 1.3 API Design Improvements

| Endpoint | Issue | Improvement |
|----------|-------|-------------|
| `/process-documents/` | No rate limiting on backend | Add `slowapi` with 10 req/min per user |
| `/groups/{id}` | N+1 query on members | Use `selectinload` or `raiseload` |
| SSE `/progress/{session_id}` | No timeout handling | Add connection timeout + heartbeat |
| `/payment/webhook` | No signature verification | Verify Pakasir webhook signatures |

### 1.4 Database Optimization

| Issue | Impact | Solution |
|-------|--------|-----------|
| No indexes on `group_members` fields | Slow filtering by NIK/passport | Add composite indexes |
| No partitioning for large groups | Performance degrades with 1000+ members | Consider table partitioning |
| No connection pooling configuration | Connection exhaustion under load | Tune `SQLAlchemy` pool params |

#### Recommended Indexes
```sql
CREATE INDEX idx_group_members_user_id ON group_members(group_id, user_id);
CREATE INDEX idx_group_members_nik ON group_members(no_identitas);
CREATE INDEX idx_group_members_passport ON group_members(no_paspor);
CREATE INDEX idx_groups_user_id_updated ON groups(user_id, updated_at DESC);
```

### 1.5 Code Quality

| Area | Current State | Recommendation |
|------|---------------|----------------|
| Type hints | Partial | Add full type hints to all services |
| Docstrings | Missing | Add Google-style docstrings |
| Linting | None | Add `ruff` + `pre-commit` hooks |
| Format consistency | Mixed | Enforce `black` formatting |

#### Pre-commit Config
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        additional_dependencies: [pydantic, types-requests]
```

---

## 2. User Experience

### 2.1 Mobile Responsiveness

| Page/Component | Issue | Fix |
|----------------|-------|-----|
| `Dashboard.svelte` | Table not scrollable on mobile | Add horizontal scroll with fixed action column |
| `RoomingPage.svelte` | Drag-drop broken on touch devices | Use `@neodrag/svelte` with touch support |
| `TableResult.svelte` | No pagination, loads all 32 cols | Add mobile-first pagination (10 rows) |
| `ProfilePage.svelte` | Two-column layout on small screens | Stack columns on `< md` breakpoint |

### 2.2 Loading States & Skeletons

| Area | Current | Improvement |
|--------|---------|-------------|
| File upload | Progress bar only | Add skeleton cards for processed items |
| Group loading | Spinner only | Add skeleton table rows |
| Payment status | No feedback | Add step-by-step payment flow UI |

### 2.3 Error Communication

| Scenario | Current | Better |
|----------|---------|--------|
| OCR fails | "Error processing file" | "KTP dengan background batik mungkin sulit dibaca. Coba foto ulang dengan cahaya lebih terang." |
| Payment fails | "Payment error" | "Pembayaran gagal: QRIS expired. Silakan coba lagi." |
| Email not received | "OTP sent" | Show "Resend OTP" button after 30s countdown |

### 2.4 Onboarding Flow

| Current State | Proposed |
|---------------|----------|
| Direct to dashboard after register | Add 3-step onboarding modal: <br>1. Upload demo KTP → See magic ✨ <br>2. Create first group → Try rooming <br>3. View sample itinerary |

### 2.5 Accessibility (WCAG 2.1 AA)

| Issue | Fix |
|-------|-----|
| No ARIA labels on buttons | Add `aria-label` to icon-only buttons |
| Color contrast issues in sidebar | Verify contrast ratio 4.5:1 |
| Keyboard navigation missing in drag-drop | Add keyboard shortcuts |
| Focus management not handled | Add focus traps in modals |

### 2.6 Performance

| Issue | Impact | Solution |
|-------|--------|----------|
| 32-column table re-renders on every edit | Lag on large datasets | Use `svelte-runed` memoization for rows |
| No virtual scrolling | Slow with 500+ rows | Add `svelte-virtual-list` |
| Images not optimized | Slow upload | Add client-side image compression |

---

## 3. Operations/DevOps

### 3.1 CI/CD Pipeline

| Tool | Purpose |
|------|---------|
| **GitHub Actions** | Workflow automation |
| **pytest** | Run tests on every PR |
| **Ruff** | Linting check |
| **Snyk** | Security vulnerability scanning |
| **Docker** | Containerize backend/frontend |

#### GitHub Actions Workflow
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/
      - run: ruff check backend/
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: snyk/actions/python@master
        with: { command: monitor }
```

### 3.2 Monitoring & Alerting

| Metric | Tool | Alert Threshold |
|--------|------|-----------------|
| API response time | Prometheus + Grafana | p95 > 2s |
| Error rate | Sentry | > 5% for 5min |
| Database connections | Postgres exporter | > 80% pool usage |
| OCR API quota | Custom | > 80% Gemini quota used |

### 3.3 Backup Strategy

| Data | Method | Frequency | Retention |
|------|--------|-----------|-----------|
| PostgreSQL | Supabase automated | Hourly | 7 days |
| Uploaded files | S3 versioning | On upload | 30 days |
| Email templates | Git versioned | Per commit | Forever |

### 3.4 Security Hardening

| Area | Current | Hardening |
|-------|---------|-----------|
| JWT secret | `.env` file | Rotate monthly, store in Vault |
| CORS | `ALLOWED_ORIGINS` | Strict whitelist, no wildcard |
| File upload | Size limit only | Add virus scanning + MIME validation |
| SQL injection | SQLAlchemy ORM safe | Add `sqlmap` scanning in CI |
| API keys | `.env` committed | Add `.env.example` only |

### 3.5 Deployment Automation

| Environment | Platform | Strategy |
|-------------|----------|-----------|
| **Backend** | Railway/Vercel | Docker container, blue-green deploy |
| **Frontend** | Vercel | Edge network, automatic previews |
| **Database** | Supabase | Managed, auto-backup |

---

## 4. Business/Features

### 4.1 Analytics & Reporting

| Feature | Description | Value |
|---------|-------------|-------|
| **User Retention** | Track D1/D7/D30 retention | Understand churn |
| **Feature Usage** | Heatmap of used features | Prioritize development |
| **Revenue Dashboard** | MRR, churn, LTV | Business intelligence |
| **Export Insights** | Most common errors, fields fixed | Product improvement |

### 4.2 User Engagement

| Feature | Impact |
|---------|--------|
| **Email Digest** | Weekly "5 pilgrims added this week" summary |
| **In-app Tips** | Contextual tips ("Did you know you can auto-assign rooms?") |
| **Gamification** | Badges for milestones (100 scans, 10 groups) |
| **Referral Program** | 1 month free for each referral |

### 4.3 Multi-Tenancy Improvements

| Current | Enhancement |
|---------|-------------|
| Single org per user | Multiple organizations with role-based access |
| No audit logs | Track who changed what, when |
| No team collaboration | Real-time sync with WebSockets |

### 4.4 Integrations

| Integration | Benefit |
|-------------|---------|
| **WhatsApp Business API** | Send automated reminders, confirmations |
| **Siskopatuh API** | Direct submission (if available) |
| **Google Sheets** | Sync data to customer's spreadsheets |
| **Zapier** | Connect to 5000+ apps |

### 4.5 Monetization Enhancements

| Feature | Pricing |
|---------|---------|
| **Team Plan** | Rp 100,000/month (5 users) |
| **Enterprise** | Custom (SLA, dedicated support) |
| **API Access** | Rp 50,000/month (per 1000 calls) |
| **White Label** | Custom branding (Enterprise only) |

### 4.6 New Features (P4)

| Priority | Feature | Description |
|----------|---------|-------------|
| 🔴 High | **Bulk WhatsApp** | Send messages to entire group at once |
| 🔴 High | **Document Templates** | Upload custom Excel templates |
| 🟡 Medium | **AI Assistant** | Chat with your pilgrim data |
| 🟡 Medium | **QR Check-in** | Pilgrims scan QR at airport |
| 🟢 Low | **Weather Widget** | Show Jeddah/Mecca/Madinah forecast |

---

## 5. Priority Matrix

### Quick Wins (1-2 weeks)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | Add loading skeletons | 🟢 Low | 🔴 High |
| 2 | Improve error messages | 🟢 Low | 🔴 High |
| 3 | Add Sentry integration | 🟢 Low | 🔴 High |
| 4 | Set up pre-commit hooks | 🟡 Medium | 🔴 High |
| 5 | Add mobile table scrolling | 🟢 Low | 🟡 Medium |

### Medium-Term (1-2 months)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | Full test coverage (80%+) | 🔴 High | 🔴 High |
| 2 | CI/CD pipeline | 🔴 High | 🔴 High |
| 3 | Mobile responsiveness audit | 🟡 Medium | 🔴 High |
| 4 | Database indexing | 🟢 Low | 🟡 Medium |
| 5 | Analytics dashboard | 🟡 Medium | 🔴 High |

### Long-Term (3-6 months)

| # | Item | Effort | Impact |
|---|------|--------|--------|
| 1 | E2E testing suite | 🔴 High | 🔴 High |
| 2 | Multi-org support | 🔴 High | 🔴 High |
| 3 | WhatsApp Business API | 🔴 High | 🔴 High |
| 4 | Real-time collaboration | 🔴 High | 🔴 High |
| 5 | Enterprise features | 🔴 High | 🟡 Medium |

---

## Summary

| Category | Key Priorities |
|----------|---------------|
| **Technical** | Testing, error handling, monitoring |
| **UX** | Mobile-first, loading states, better errors |
| **DevOps** | CI/CD, security hardening, monitoring |
| **Business** | Analytics, engagement, integrations |

**Estimated Effort:** ~6-9 months for full implementation

---

*Generated by Claude Code - 2026-02-27*

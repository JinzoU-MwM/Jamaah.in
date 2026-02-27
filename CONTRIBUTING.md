# Contributing to Jamaah.in

Thank you for your interest in contributing!

## Development Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend-svelte
npm install
```

### Database

Ensure `.env` is configured with `DATABASE_URL`.

## Running Tests

```bash
# Backend
cd backend
pytest -v                    # Run all tests
pytest --cov=.              # With coverage
pytest tests/test_validators.py  # Specific file
```

## Code Style

- Python: Follow PEP 8, formatted with Black, linted with Ruff
- Svelte: Use Svelte 5 Runes, follow existing patterns

## Adding New Features

1. Write tests first (TDD)
2. Implement feature
3. Ensure tests pass
4. Update documentation
5. Commit with conventional commits

## Commit Message Format

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- test: Tests
- refactor: Code refactoring
- chore: Maintenance
- perf: Performance improvement
```

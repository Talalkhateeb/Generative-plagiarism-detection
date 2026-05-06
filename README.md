# Generative Plagiarism Detection

Web application for analyzing textual content and detecting semantic plagiarism with AI-assisted retrieval.

## Team

1. Tala Al-Khatteb
2. Farah Al-Kayyem

## Supervisors

1. PhD Riad Sonbol
2. Eng. Raghad Al-Hossny

## Project Structure

The repository is easiest to work with when you treat these folders as the real project code:

```text
.
|-- GPD_back/         # Django backend
|-- GPD_front/        # Frontend
|-- AI/               # AI retrieval and analysis service code
`-- storage_service/  # Standalone FastAPI + MinIO microservice
```

Generated and local-only folders should not be edited as app source:

```text
GPD_back/.venv/
GPD_front/node_modules/
GPD_front/.vite/
__pycache__/
.pytest_cache/
GPD_back/media/
storage/
```

If your editor opens files under `GPD_back/.venv/Lib/site-packages/`, you are looking at installed package code, not your project source.

## Notes

- `storage_service/` is intentionally outside `GPD_back/` because it runs as a separate service and is accessed by URL.
- OTP registration and email verification stay inside `GPD_back/apps/accounts/`.
- Backend helper scripts live in `GPD_back/scripts/`.
- Backend tests live in `GPD_back/tests/`.

## Testing

Backend unit and integration tests use `pytest-django` with the dedicated SQL Server settings module at `GPD_Back.test_settings`.

Install backend test dependencies:

```bash
cd GPD_back
pip install -r requirements-dev.txt
```

Run backend unit and integration tests:

```bash
cd GPD_back
pytest tests/test_unit_auth.py tests/test_integration_auth_admin.py --cov=apps --cov-report=term-missing
```

If you need to point pytest at a specific SQL Server test database, set `TEST_DB_NAME` before running:

```bash
cd GPD_back
$env:TEST_DB_NAME="GPD_test"
pytest
```

Run the Locust performance suite for 50 concurrent users with a 10 second ramp-up:

```bash
cd GPD_back
locust -f locustfile.py --headless -u 50 -r 5 --run-time 30s --host http://localhost:8000
```

Frontend E2E tests use Playwright with mocked API responses to exercise the UI flows deterministically.

Install frontend dependencies and Playwright browsers:

```bash
cd GPD_front
npm install
npx playwright install
```

Run the Playwright suite:

```bash
cd GPD_front
npm run test:e2e
```

If you want the full CI sequence locally, run the suites in this order:

```bash
cd GPD_back
pytest tests/test_unit_auth.py tests/test_integration_auth_admin.py --cov=apps --cov-report=term-missing
locust -f locustfile.py --headless -u 50 -r 5 --run-time 30s --host http://localhost:8000
cd ..\GPD_front
npm run test:e2e
```

# API Validation Matrix

This project should be validated with four layers:

1. `Unit tests`
2. `Integration/API tests`
3. `Manual smoke test`
4. `Locust/load test`

## Automated Coverage

### Unit tests

Current suite:
- `tests/test_unit_auth.py`

Focus:
- serializer validation
- password and account actions
- upgrade-plan validation

### Integration/API tests

Current suites:
- `tests/test_integration_auth_admin.py`
- `tests/test_integration_api_matrix.py`

Covered route groups:
- `POST /api/auth/login/`
- `POST /api/auth/register/send-otp/`
- `POST /api/auth/register/verify-otp/`
- `POST /api/auth/logout/`
- `POST /api/auth/token/refresh/`
- `GET/PATCH /api/auth/me/`
- `POST /api/auth/change-password/`
- `DELETE /api/auth/me/delete/`
- `PATCH /api/auth/me/upgrade-plan/`
- `GET/POST/PATCH/DELETE /api/plans/`
- `GET/POST /api/workspaces/`
- `GET/PATCH/DELETE /api/workspaces/{id}/`
- `GET/POST/DELETE /api/workspaces/{id}/sources/`
- `GET/POST/DELETE /api/workspaces/{id}/documents/`
- `POST /api/workspaces/{id}/submit/`
- `GET /api/workspaces/{id}/results/`
- `GET /api/workspaces/{id}/report/`
- `GET /api/submissions/history/`
- `GET /api/admin/accounts/`
- `GET/PATCH /api/admin/accounts/{id}/`
- `POST /api/results/callback/`

## Manual Smoke Test

Run the backend and test these flows once end to end in browser or Postman:

- Sign up with OTP
- Log in as regular user
- View and edit profile
- Upgrade plan
- Create workspace
- Upload at least 2 sources and 1 document
- Submit analysis
- View results page
- Download report
- Log in as admin
- Search users in admin accounts page
- Change a user status

Suggested checklist:

- Does each request return the expected status code?
- Does the UI show the expected success or error message?
- Does the database state actually change?
- Do uploaded files appear in storage?
- Does analysis completion update workspace and submission status?

## Locust / Load Test

Locust script:
- `locustfile.py`

Browser UI command from `GPD_back/`:

```powershell
locust -f .\locustfile.py --host http://127.0.0.1:8000
```

Open:

```text
http://localhost:8089
```

Current load-test journeys:
- public plan browsing
- login
- profile fetch
- submissions history
- workspace browsing and CRUD
- admin account list/search/detail

## Remaining Gaps

These areas still deserve extra attention even after the current test pass:

- true end-to-end file upload against the real storage service
- true end-to-end submission processing against the AI pipeline
- negative-path tests for every single endpoint
- permission tests for more non-owner and inactive-user cases
- browser-side smoke coverage for the full auth and analysis flow

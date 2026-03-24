# Veritas.AI — Django REST Framework Backend

## Setup & Run

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply migrations
python manage.py makemigrations accounts plans workspaces submissions results
python manage.py migrate

# 3. Seed initial data (plans + demo users)
python manage.py shell < seed_data.py

# 4. Run development server
python manage.py runserver 8000
```

## URL Structure

| Method | Endpoint | Description | UC |
|--------|----------|-------------|-----|
| POST | `/api/auth/register/` | Register + select plan | UC-2, UC-7 |
| POST | `/api/auth/login/` | Login → JWT tokens | UC-1 |
| POST | `/api/auth/token/refresh/` | Refresh access token | — |
| POST | `/api/auth/logout/` | Blacklist token | — |
| GET/PATCH | `/api/auth/me/` | View/update profile | — |
| POST | `/api/auth/change-password/` | Change password | — |
| GET | `/api/plans/` | List plans (public) | UC-7 |
| POST | `/api/plans/` | Create plan (admin) | UC-8 |
| GET/PUT/DELETE | `/api/plans/{id}/` | Plan detail (admin) | UC-8 |
| GET | `/api/workspaces/` | List workspaces | UC-3 |
| POST | `/api/workspaces/` | Create workspace | UC-3 |
| GET/PATCH/DELETE | `/api/workspaces/{id}/` | Workspace detail | UC-3 |
| GET/POST | `/api/workspaces/{id}/sources/` | List/upload sources | UC-3 |
| DELETE | `/api/workspaces/{id}/sources/{src_id}/` | Delete source | UC-3 |
| GET/POST | `/api/workspaces/{id}/documents/` | List/upload documents | UC-4 |
| DELETE | `/api/workspaces/{id}/documents/{doc_id}/` | Delete document | UC-4 |
| POST | `/api/workspaces/{id}/submit/` | Submit for analysis | UC-4, UC-5 |
| GET | `/api/workspaces/{id}/results/` | Get results | UC-6 |
| GET | `/api/workspaces/{id}/report/` | Download report | UC-6 |
| GET | `/api/submissions/history/` | Submission history | UC-10 |
| GET | `/api/admin/accounts/` | List all users | UC-9 |
| GET/PATCH | `/api/admin/accounts/{id}/` | Edit user status | UC-9 |

## Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@veritas.ai | admin123 |
| User  | user@veritas.ai  | user123  |

## React Frontend Integration

In your React project, update `src/services/api.ts`:

```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
})
```

Set `.env` in your React project:
```
VITE_API_URL=http://localhost:8000/api
```

### Login Flow
```typescript
// POST /api/auth/login/
const { data } = await api.post('/auth/login/', { email, password })
localStorage.setItem('access_token',  data.access)
localStorage.setItem('refresh_token', data.refresh)
// data.user = { id, name, email, role, status, plan, date_joined }
```

### Register Flow
```typescript
// POST /api/auth/register/
const { data } = await api.post('/auth/register/', {
  name, email, password, confirm_password, plan_id
})
```

### Submit Documents
```typescript
// POST /api/workspaces/{id}/submit/
const { data } = await api.post(`/workspaces/${id}/submit/`, {
  source_ids: [1, 2, 3],
  document_ids: [4]
})
// Returns submission with result embedded
```

## Production Notes

1. **Database**: Switch SQLite → PostgreSQL in settings.py
2. **Message Broker**: Uncomment Celery tasks in `apps/results/tasks.py`  
   ```bash
   pip install celery[rabbitmq]
   celery -A veritas_project worker --loglevel=info
   ```
3. **CORS**: Set `CORS_ALLOW_ALL_ORIGINS = False` and configure `CORS_ALLOWED_ORIGINS`
4. **Secret Key**: Set `SECRET_KEY` environment variable
5. **Media Files**: Configure S3 or similar for file storage

## Architecture

```
veritas_backend/
├── manage.py
├── requirements.txt
├── seed_data.py
├── veritas_project/
│   ├── settings.py       ← JWT, CORS, REST_FRAMEWORK config
│   └── urls.py           ← Main URL routing
└── apps/
    ├── accounts/         ← User model, auth (UC-1, UC-2, UC-9)
    ├── plans/            ← Subscription plans (UC-7, UC-8)
    ├── workspaces/       ← Workspace + file management (UC-3)
    ├── submissions/      ← Submit + history (UC-4, UC-10)
    └── results/          ← AI results + reports (UC-5, UC-6)
```

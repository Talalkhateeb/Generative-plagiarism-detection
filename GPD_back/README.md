# GPD.AI Django Backend

## Setup And Run

```bash
pip install -r requirements.txt
python manage.py makemigrations accounts plans workspaces submissions results
python manage.py migrate
python manage.py shell < scripts/seed_data.py
python manage.py runserver 8000
```

## Service Boundary

This folder contains the Django backend only.

- OTP registration, account verification, and email auth live in `apps/accounts/`.
- File storage is handled by the separate root-level `storage_service/`.
- Django talks to that service through `STORAGE_SERVICE_URL` and `minio_client.py`.

## Key Areas

- `apps/accounts/`: auth, OTP, profiles, admin account controls
- `apps/plans/`: subscription plans
- `apps/workspaces/`: workspaces, source files, submitted documents
- `apps/submissions/`: submission history
- `apps/results/`: analysis results and reporting
- `scripts/`: backend helper scripts such as seed data
- `GPD_Back/settings.py`: database, JWT, email, storage and AI service URLs

## Architecture

```text
GPD_back/
|-- manage.py
|-- minio_client.py
|-- scripts/
|   `-- seed_data.py
|-- GPD_Back/
|   |-- settings.py
|   `-- urls.py
|-- tests/
|   |-- test_api.py
|   |-- test_integration.py
|   |-- test_performance.py
|   `-- test_unit.py
`-- apps/
    |-- accounts/
    |-- plans/
    |-- workspaces/
    |-- submissions/
    `-- results/

storage_service/
`-- main.py
```

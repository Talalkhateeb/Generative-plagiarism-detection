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
`-- storage_service/  # Standalone FastAPI + MinIO microservice
```

Generated and local-only folders should not be edited as app source:

```text
GPD_back/.venv/
GPD_front/node_modules/
__pycache__/
.pytest_cache/
GPD_back/media/
```

If your editor opens files under `GPD_back/.venv/Lib/site-packages/`, you are looking at installed package code, not your project source.

## Notes

- `storage_service/` is intentionally outside `GPD_back/` because it runs as a separate service and is accessed by URL.
- OTP registration and email verification stay inside `GPD_back/apps/accounts/`.

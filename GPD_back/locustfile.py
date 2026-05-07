"""
Performance test targets:
- POST /api/auth/login/
- GET /api/plans/
- GET /api/auth/me/
- GET /api/workspaces/
- POST /api/workspaces/
- GET /api/workspaces/{id}/
- PATCH /api/workspaces/{id}/
- DELETE /api/workspaces/{id}/
- GET /api/submissions/history/
- GET /api/admin/accounts/
- GET /api/admin/accounts/{id}/

Suggested run:
locust -f locustfile.py --headless -u 50 -r 5 --run-time 30s --host http://localhost:8000

Results summary template:
- Total users: 50 concurrent users
- Ramp-up: 10 seconds at 5 users/second
- Measure: p95 latency, failure rate, and requests/second for auth, plans, workspace, history, and admin flows
- Replace this section with captured numbers after each run
"""

import os
import random
import time

from locust import HttpUser, between, task
from locust.exception import StopUser


def _env_or_default(name, default):
    """Use the default when the environment variable is unset or blank."""
    value = os.getenv(name)
    if value is None:
        return default

    cleaned = value.strip()
    return cleaned or default


class BaseAuthenticatedUser(HttpUser):
    wait_time = between(1, 3)

    email = ""
    password = ""
    token = None
    refresh_token = None

    def _login(self, request_name="POST /api/auth/login/"):
        with self.client.post(
            "/api/auth/login/",
            json={"email": self.email, "password": self.password},
            name=request_name,
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                detail = ""
                try:
                    payload = response.json()
                    detail = payload.get("detail") or payload.get("error") or str(payload)
                except Exception:
                    detail = response.text
                response.failure(
                    f"Login failed for {self.email} with status {response.status_code}: {detail}"
                )
                return None

            payload = response.json()
            token = payload.get("access")
            if not token:
                response.failure(f"Login succeeded for {self.email} but no access token was returned.")
                return None

            self.refresh_token = payload.get("refresh")
            response.success()
            return token

    def _authorized_json(self, method, path, *, request_name, expected_statuses=(200,), **kwargs):
        with self.client.request(
            method,
            path,
            name=request_name,
            catch_response=True,
            **kwargs,
        ) as response:
            if response.status_code not in expected_statuses:
                detail = ""
                try:
                    detail = str(response.json())
                except Exception:
                    detail = response.text
                response.failure(
                    f"{request_name} returned {response.status_code} for {self.email}: {detail}"
                )
                return None

            response.success()
            if response.text:
                try:
                    return response.json()
                except Exception:
                    return response.text
            return {}

    def _workspace_name(self):
        return f"Locust Workspace {int(time.time() * 1000)}-{random.randint(1000, 9999)}"

    def on_start(self):
        if not self.email or not self.password:
            raise StopUser(
                f"Locust credentials for {self.__class__.__name__} are missing. "
                "Check the LOCUST_* environment variables."
            )

        self.token = self._login()
        if not self.token:
            raise StopUser(f"Unable to authenticate Locust user {self.email}")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})


class RegularUser(BaseAuthenticatedUser):
    weight = 4
    email = _env_or_default("LOCUST_USER_EMAIL", "user@example.com").lower()
    password = _env_or_default("LOCUST_USER_PASSWORD", "StrongPass123!")

    @task(2)
    def browse_plans(self):
        self.client.get("/api/plans/", name="GET /api/plans/")

    @task(2)
    def view_profile(self):
        self.client.get("/api/auth/me/", name="GET /api/auth/me/")

    @task(1)
    def view_submission_history(self):
        self.client.get("/api/submissions/history/", name="GET /api/submissions/history/")

    @task(3)
    def workspace_journey(self):
        workspaces = self._authorized_json(
            "GET",
            "/api/workspaces/",
            request_name="GET /api/workspaces/",
        )
        if workspaces is None:
            return

        if workspaces:
            workspace = random.choice(workspaces)
            workspace_id = workspace.get("id")
            if workspace_id:
                self._authorized_json(
                    "GET",
                    f"/api/workspaces/{workspace_id}/",
                    request_name="GET /api/workspaces/[id]/",
                )
            return

        created = self._authorized_json(
            "POST",
            "/api/workspaces/",
            request_name="POST /api/workspaces/",
            expected_statuses=(201,),
            json={"name": self._workspace_name()},
        )
        if not created:
            return

        workspace_id = created.get("id")
        if not workspace_id:
            return

        self._authorized_json(
            "GET",
            f"/api/workspaces/{workspace_id}/",
            request_name="GET /api/workspaces/[id]/",
        )
        self._authorized_json(
            "PATCH",
            f"/api/workspaces/{workspace_id}/",
            request_name="PATCH /api/workspaces/[id]/",
            json={"name": f"{created.get('name', 'Locust Workspace')} Updated"},
        )
        self._authorized_json(
            "DELETE",
            f"/api/workspaces/{workspace_id}/",
            request_name="DELETE /api/workspaces/[id]/",
            expected_statuses=(204,),
        )

    @task(1)
    def login_again(self):
        token = self._login()
        if token:
            self.token = token
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})


class AdminUser(BaseAuthenticatedUser):
    weight = 1
    email = _env_or_default("LOCUST_ADMIN_EMAIL", "admin@example.com").lower()
    password = _env_or_default("LOCUST_ADMIN_PASSWORD", "StrongPass123!")

    @task(1)
    def browse_plans(self):
        self.client.get("/api/plans/", name="GET /api/plans/")

    @task(3)
    def list_accounts(self):
        self.client.get("/api/admin/accounts/", name="GET /api/admin/accounts/")

    @task(2)
    def search_active_accounts(self):
        self.client.get(
            "/api/admin/accounts/?status=active&search=user",
            name="GET /api/admin/accounts/?search",
        )

    @task(2)
    def inspect_account_detail(self):
        accounts = self._authorized_json(
            "GET",
            "/api/admin/accounts/",
            request_name="GET /api/admin/accounts/",
        )
        if not accounts:
            return

        results = accounts.get("results") if isinstance(accounts, dict) else accounts
        if not results:
            return

        account = random.choice(results)
        account_id = account.get("id")
        if not account_id:
            return

        self._authorized_json(
            "GET",
            f"/api/admin/accounts/{account_id}/",
            request_name="GET /api/admin/accounts/[id]/",
        )

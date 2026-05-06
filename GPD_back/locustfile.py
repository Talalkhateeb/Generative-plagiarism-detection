"""
Performance test targets:
- POST /api/auth/login/
- GET /api/auth/me/
- GET /api/admin/accounts/

Suggested run:
locust -f locustfile.py --headless -u 50 -r 5 --run-time 30s --host http://localhost:8000

Results summary template:
- Total users: 50 concurrent users
- Ramp-up: 10 seconds at 5 users/second
- Measure: p95 latency, failure rate, and requests/second for login, me, and admin account list
- Replace this section with captured numbers after each run
"""

import os

from locust import HttpUser, between, task
from locust.exception import StopUser


class BaseAuthenticatedUser(HttpUser):
    wait_time = between(1, 3)

    email = ""
    password = ""
    token = None

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

            token = response.json().get("access")
            if not token:
                response.failure(f"Login succeeded for {self.email} but no access token was returned.")
                return None

            response.success()
            return token

    def on_start(self):
        self.token = self._login()
        if not self.token:
            raise StopUser(f"Unable to authenticate Locust user {self.email}")
        self.client.headers.update({"Authorization": f"Bearer {self.token}"})


class RegularUser(BaseAuthenticatedUser):
    weight = 4
    email = os.getenv("LOCUST_USER_EMAIL", "user@example.com")
    password = os.getenv("LOCUST_USER_PASSWORD", "StrongPass123!")

    @task(2)
    def view_profile(self):
        self.client.get("/api/auth/me/", name="GET /api/auth/me/")

    @task(1)
    def login_again(self):
        token = self._login()
        if token:
            self.token = token
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})


class AdminUser(BaseAuthenticatedUser):
    weight = 1
    email = os.getenv("LOCUST_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("LOCUST_ADMIN_PASSWORD", "StrongPass123!")

    @task
    def list_accounts(self):
        self.client.get("/api/admin/accounts/", name="GET /api/admin/accounts/")

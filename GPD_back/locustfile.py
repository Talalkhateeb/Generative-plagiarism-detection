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


class BaseAuthenticatedUser(HttpUser):
    wait_time = between(1, 3)

    email = ""
    password = ""
    token = None

    def on_start(self):
        response = self.client.post(
            "/api/auth/login/",
            json={"email": self.email, "password": self.password},
            name="POST /api/auth/login/",
        )
        if response.status_code == 200:
            self.token = response.json().get("access")
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
        self.client.post(
            "/api/auth/login/",
            json={"email": self.email, "password": self.password},
            name="POST /api/auth/login/",
        )


class AdminUser(BaseAuthenticatedUser):
    weight = 1
    email = os.getenv("LOCUST_ADMIN_EMAIL", "admin@example.com")
    password = os.getenv("LOCUST_ADMIN_PASSWORD", "StrongPass123!")

    @task
    def list_accounts(self):
        self.client.get("/api/admin/accounts/", name="GET /api/admin/accounts/")


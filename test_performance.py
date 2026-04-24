"""
Performance Tests — GPD.AI Plagiarism Detection System
Uses Locust to simulate concurrent users hitting the most critical endpoints.

Run (headless, 10 users, 60 seconds):
    locust -f test_performance.py --headless -u 10 -r 2 --run-time 60s \
           --host http://localhost:8000 --html results/performance_report.html

Run (with web UI at http://localhost:8089):
    locust -f test_performance.py --host http://localhost:8000
"""
import random
from locust import HttpUser, task, between, events


# ── Test data ─────────────────────────────────────────────────────────────────
USERS = [
    {"email": "perf_user1@gpd.com", "password": "TestPass123!"},
    {"email": "perf_user2@gpd.com", "password": "TestPass123!"},
    {"email": "perf_user3@gpd.com", "password": "TestPass123!"},
]


class GPDUser(HttpUser):
    """
    Simulates a typical GPD.AI user:
      1. Login → get JWT
      2. Browse plans
      3. List workspaces
      4. Create a workspace
      5. View workspace detail
      6. Check submission history
    """
    wait_time = between(1, 3)   # realistic think-time between requests
    token: str = ""
    workspace_ids: list = []

    # ── Setup: authenticate once per virtual user ─────────────────────────────

    def on_start(self):
        """Called once when a new virtual user starts. Performs login."""
        creds = random.choice(USERS)
        with self.client.post(
            "/api/auth/login/",
            json={"email": creds["email"], "password": creds["password"]},
            catch_response=True,
            name="POST /api/auth/login/",
        ) as resp:
            if resp.status_code == 200:
                self.token = resp.json().get("access", "")
                resp.success()
            else:
                # Mark as failure — user will still run but token will be ""
                resp.failure(f"Login failed: {resp.status_code}")

    def _headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    # ── Tasks ─────────────────────────────────────────────────────────────────

    @task(3)
    def list_plans(self):
        """Public endpoint — no auth required. High weight = called frequently."""
        self.client.get("/api/plans/", name="GET /api/plans/")

    @task(5)
    def list_workspaces(self):
        """Most-visited authenticated endpoint."""
        with self.client.get(
            "/api/workspaces/",
            headers=self._headers(),
            catch_response=True,
            name="GET /api/workspaces/",
        ) as resp:
            if resp.status_code == 200:
                data = resp.json()
                # Cache IDs for later use in get_workspace_detail
                ids = [w["id"] for w in data] if isinstance(data, list) else \
                      [w["id"] for w in data.get("results", [])]
                if ids:
                    self.workspace_ids = ids
                resp.success()
            elif resp.status_code == 401:
                resp.failure("Unauthorized — token may have expired")
            else:
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def create_workspace(self):
        """POST a new workspace — tests write throughput."""
        name = f"Perf WS {random.randint(1000, 9999)}"
        with self.client.post(
            "/api/workspaces/",
            json={"name": name},
            headers=self._headers(),
            catch_response=True,
            name="POST /api/workspaces/",
        ) as resp:
            if resp.status_code == 201:
                new_id = resp.json().get("id")
                if new_id:
                    self.workspace_ids.append(new_id)
                resp.success()
            else:
                resp.failure(f"Create failed: {resp.status_code}")

    @task(3)
    def get_workspace_detail(self):
        """Fetch a workspace by ID — tests DB lookup performance."""
        if not self.workspace_ids:
            return
        ws_id = random.choice(self.workspace_ids)
        with self.client.get(
            f"/api/workspaces/{ws_id}/",
            headers=self._headers(),
            catch_response=True,
            name="GET /api/workspaces/{id}/",
        ) as resp:
            if resp.status_code in (200, 404):
                resp.success()
            else:
                resp.failure(f"Unexpected {resp.status_code}")

    @task(2)
    def submission_history(self):
        """Paginated history query — tests queryset performance."""
        self.client.get(
            "/api/submissions/history/",
            headers=self._headers(),
            name="GET /api/submissions/history/",
        )

    @task(1)
    def get_profile(self):
        """Cheap auth-check endpoint."""
        self.client.get(
            "/api/auth/me/",
            headers=self._headers(),
            name="GET /api/auth/me/",
        )

    # ── Teardown ──────────────────────────────────────────────────────────────

    def on_stop(self):
        """Logout when virtual user finishes to blacklist token."""
        if self.token:
            self.client.post(
                "/api/auth/logout/",
                json={"refresh": ""},   # best-effort cleanup
                headers=self._headers(),
                name="POST /api/auth/logout/",
            )


# ── Event hook: print summary thresholds after test ──────────────────────────

@events.quitting.add_listener
def print_summary(environment, **kwargs):
    stats = environment.stats
    total = stats.total
    print("\n" + "═" * 60)
    print("  GPD Performance Test Summary")
    print("═" * 60)
    print(f"  Total requests  : {total.num_requests}")
    print(f"  Failures        : {total.num_failures}  "
          f"({100 * total.fail_ratio:.1f}%)")
    print(f"  Avg response    : {total.avg_response_time:.1f} ms")
    print(f"  95th percentile : {total.get_response_time_percentile(0.95):.0f} ms")
    print(f"  99th percentile : {total.get_response_time_percentile(0.99):.0f} ms")
    print(f"  RPS             : {total.current_rps:.1f}")
    print("═" * 60)

    # CI gate: fail if error rate > 1% or 95th p > 2000 ms
    if total.fail_ratio > 0.01:
        print("  ❌ FAIL: Error rate exceeds 1%")
        environment.process_exit_code = 1
    elif total.get_response_time_percentile(0.95) > 2000:
        print("  ❌ FAIL: 95th percentile exceeds 2000 ms")
        environment.process_exit_code = 1
    else:
        print("  ✅ PASS: Performance within thresholds")

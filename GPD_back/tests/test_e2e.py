"""
E2E Tests — GPD.AI Plagiarism Detection System
Uses Playwright to automate real user flows through the browser UI.

Prerequisites:
    pip install pytest-playwright
    playwright install chromium

Run:
    pytest tests/test_e2e.py -v --headed        # with browser visible
    pytest tests/test_e2e.py -v                 # headless (CI mode)
"""
import pytest
import re
from playwright.sync_api import Page, expect

# ── Base URL — override with BASE_URL env var in CI ──────────────────────────
BASE_URL = "http://localhost:3000"     # React/Next.js frontend


# ══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture
def logged_in_page(page: Page):
    """
    Fixture: navigate to login page, fill credentials, click submit.
    Returns the page after successful login (landed on dashboard).
    """
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("Email").fill("perf_user1@gpd.com")
    page.get_by_label("Password").fill("TestPass123!")
    page.get_by_role("button", name=re.compile(r"log in|sign in", re.IGNORECASE)).click()
    # Wait for redirect to dashboard
    page.wait_for_url(re.compile(r"/dashboard|/workspaces"), timeout=10_000)
    return page


# ══════════════════════════════════════════════════════════════════════════════
# UC-1: LOGIN FLOW
# ══════════════════════════════════════════════════════════════════════════════

class TestLoginE2E:

    def test_login_with_valid_credentials(self, page: Page):
        """
        SCENARIO: User opens /login, fills in email+password, clicks Login.
        EXPECTED: Redirected to /dashboard (or /workspaces), sees their name.
        """
        page.goto(f"{BASE_URL}/login")

        expect(page).to_have_title(re.compile(r"GPD|Login|Sign In", re.IGNORECASE))

        page.get_by_label("Email").fill("perf_user1@gpd.com")
        page.get_by_label("Password").fill("TestPass123!")
        page.get_by_role("button", name=re.compile(r"log in|sign in", re.IGNORECASE)).click()

        # Should land on dashboard
        expect(page).to_have_url(re.compile(r"/dashboard|/workspaces"), timeout=10_000)

    def test_login_with_wrong_password_shows_error(self, page: Page):
        """
        SCENARIO: User submits wrong password.
        EXPECTED: Error message visible. URL stays on /login.
        """
        page.goto(f"{BASE_URL}/login")
        page.get_by_label("Email").fill("perf_user1@gpd.com")
        page.get_by_label("Password").fill("WRONG_PASSWORD")
        page.get_by_role("button", name=re.compile(r"log in|sign in", re.IGNORECASE)).click()

        # Error message must appear
        error = page.get_by_role("alert").or_(page.locator("[data-testid='error-msg']"))
        expect(error).to_be_visible(timeout=5_000)
        expect(page).to_have_url(re.compile(r"/login"))

    def test_login_required_fields_validation(self, page: Page):
        """
        SCENARIO: User clicks Login without filling anything.
        EXPECTED: Validation errors shown inline (HTML5 or custom).
        """
        page.goto(f"{BASE_URL}/login")
        page.get_by_role("button", name=re.compile(r"log in|sign in", re.IGNORECASE)).click()
        # Either browser native validation or a custom error div must appear
        invalid_fields = page.locator("input:invalid, [data-testid='field-error']")
        expect(invalid_fields.first).to_be_visible(timeout=3_000)


# ══════════════════════════════════════════════════════════════════════════════
# UC-2: REGISTRATION FLOW (OTP 2-step)
# ══════════════════════════════════════════════════════════════════════════════

class TestRegistrationE2E:

    def test_registration_page_renders(self, page: Page):
        """
        SCENARIO: User navigates to /register.
        EXPECTED: Registration form is visible with name, email, password fields.
        """
        page.goto(f"{BASE_URL}/register")
        expect(page.get_by_label("Name").or_(page.get_by_placeholder("Name"))).to_be_visible()
        expect(page.get_by_label("Email")).to_be_visible()
        expect(page.get_by_label("Password")).to_be_visible()

    def test_password_mismatch_shows_error(self, page: Page):
        """
        SCENARIO: User enters mismatched passwords.
        EXPECTED: Error displayed before form submission.
        """
        page.goto(f"{BASE_URL}/register")
        page.get_by_label("Name").or_(page.get_by_placeholder("Name")).fill("Test User")
        page.get_by_label("Email").fill("newuser@gpd.com")
        page.get_by_label("Password").fill("Pass123!")
        page.get_by_label(re.compile(r"confirm", re.IGNORECASE)).fill("DifferentPass!")
        page.get_by_role("button", name=re.compile(r"sign up|register|next", re.IGNORECASE)).click()

        error = page.locator("[data-testid='error-msg'], .error, [role='alert']")
        expect(error.first).to_be_visible(timeout=5_000)


# ══════════════════════════════════════════════════════════════════════════════
# UC-3: WORKSPACE MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

class TestWorkspaceE2E:

    def test_create_workspace(self, logged_in_page: Page):
        """
        SCENARIO: Logged-in user clicks "New Workspace", types a name, submits.
        EXPECTED: New workspace card appears in the list.
        """
        page = logged_in_page
        ws_name = "E2E Test Workspace"

        # Click "New Workspace" or "+" button
        page.get_by_role("button",
            name=re.compile(r"new workspace|create|add workspace|\+", re.IGNORECASE)
        ).first.click()

        # Fill in workspace name
        name_input = page.get_by_label(re.compile(r"name", re.IGNORECASE)).or_(
            page.get_by_placeholder(re.compile(r"workspace name", re.IGNORECASE))
        )
        name_input.fill(ws_name)

        # Submit
        page.get_by_role("button", name=re.compile(r"create|save|submit", re.IGNORECASE)).click()

        # New workspace must appear in the list
        expect(page.get_by_text(ws_name)).to_be_visible(timeout=8_000)

    def test_rename_workspace(self, logged_in_page: Page):
        """
        SCENARIO: User renames an existing workspace.
        EXPECTED: Updated name visible immediately.
        """
        page = logged_in_page
        original_name = "E2E Test Workspace"
        new_name = "Renamed E2E Workspace"

        # Open the workspace or its context menu
        ws_card = page.get_by_text(original_name).first
        ws_card.click()

        # Find rename/edit button
        page.get_by_role("button", name=re.compile(r"rename|edit", re.IGNORECASE)).click()

        name_input = page.get_by_role("textbox").first
        name_input.clear()
        name_input.fill(new_name)
        page.get_by_role("button", name=re.compile(r"save|confirm|ok", re.IGNORECASE)).click()

        expect(page.get_by_text(new_name)).to_be_visible(timeout=5_000)

    def test_delete_workspace(self, logged_in_page: Page):
        """
        SCENARIO: User deletes a workspace.
        EXPECTED: Workspace disappears from the list.
        """
        page = logged_in_page
        ws_name = "Renamed E2E Workspace"

        # Open delete flow
        page.get_by_text(ws_name).first.click()
        page.get_by_role("button", name=re.compile(r"delete|remove", re.IGNORECASE)).click()

        # Confirm dialog
        confirm_btn = page.get_by_role("button",
            name=re.compile(r"confirm|yes|delete", re.IGNORECASE)
        )
        if confirm_btn.is_visible():
            confirm_btn.click()

        # Workspace should no longer appear
        expect(page.get_by_text(ws_name)).not_to_be_visible(timeout=8_000)


# ══════════════════════════════════════════════════════════════════════════════
# UC-7: PLAN SELECTION
# ══════════════════════════════════════════════════════════════════════════════

class TestPlanSelectionE2E:

    def test_plans_page_displays_plans(self, page: Page):
        """
        SCENARIO: Unauthenticated user visits /plans (or /register's plan step).
        EXPECTED: At least one plan card is visible with a price.
        """
        page.goto(f"{BASE_URL}/plans")
        # At least one plan card must be rendered
        plan_cards = page.locator("[data-testid='plan-card'], .plan-card, .pricing-card")
        expect(plan_cards.first).to_be_visible(timeout=8_000)


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION / LOGOUT
# ══════════════════════════════════════════════════════════════════════════════

class TestNavigationE2E:

    def test_logout_redirects_to_login(self, logged_in_page: Page):
        """
        SCENARIO: Logged-in user clicks Logout.
        EXPECTED: Redirected to /login. Protected pages no longer accessible.
        """
        page = logged_in_page
        page.get_by_role("button",
            name=re.compile(r"logout|sign out|log out", re.IGNORECASE)
        ).or_(
            page.get_by_role("menuitem",
                name=re.compile(r"logout|sign out", re.IGNORECASE))
        ).click()

        expect(page).to_have_url(re.compile(r"/login"), timeout=8_000)

    def test_protected_route_redirects_when_not_logged_in(self, page: Page):
        """
        SCENARIO: Unauthenticated user tries to visit /workspaces directly.
        EXPECTED: Redirected to /login.
        """
        page.goto(f"{BASE_URL}/workspaces")
        expect(page).to_have_url(re.compile(r"/login"), timeout=8_000)

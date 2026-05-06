import { expect, test, type Page } from "@playwright/test";

const userToken = "fake-access-token";
const refreshToken = "fake-refresh-token";

const starterPlan = {
  id: 1,
  name: "Starter",
  price: 0,
  checks_per_month: 10,
  max_sources: 5,
  max_documents: 3,
};

function mockCommonUserApis(page: Page, userOverride: Record<string, unknown> = {}) {
  const user = {
    id: 101,
    name: "Test User",
    email: "test.user@example.com",
    role: "user",
    status: "active",
    plan: "Starter",
    date_joined: "2026-05-06",
    ...userOverride,
  };

  return Promise.all([
    page.route("**/api/plans/**", async (route) => {
      await route.fulfill({ json: [starterPlan] });
    }),
    page.route("**/api/submissions/history/**", async (route) => {
      await route.fulfill({ json: [] });
    }),
    page.route("**/api/workspaces/**", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({ json: [] });
        return;
      }
      await route.continue();
    }),
    page.route("**/api/auth/me/**", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          json: {
            id: user.id,
            name: user.name,
            email: user.email,
            role: user.role,
            status: user.status,
            plan: user.plan,
            date_joined: user.date_joined,
            is_email_verified: true,
          },
        });
        return;
      }
      if (route.request().method() === "PATCH") {
        const body = route.request().postDataJSON();
        user.name = body.name ?? user.name;
        user.email = body.email ?? user.email;
        await route.fulfill({ json: { ...user } });
        return;
      }
      await route.continue();
    }),
  ]);
}

function seedAuth(page: Page, user: Record<string, unknown>) {
  return page.addInitScript(
    ({ seededUser, access, refresh }) => {
      window.localStorage.setItem("access_token", access);
      window.localStorage.setItem("refresh_token", refresh);
      window.localStorage.setItem("GPD_user", JSON.stringify(seededUser));
    },
    { seededUser: user, access: userToken, refresh: refreshToken }
  );
}

test("full registration flow lands on the dashboard", async ({ page }) => {
  await mockCommonUserApis(page);

  await page.route("**/api/auth/register/send-otp/", async (route) => {
    await route.fulfill({
      json: { message: "Verification code sent to test.user@example.com. Check your inbox." },
    });
  });

  await page.route("**/api/auth/register/verify-otp/", async (route) => {
    await route.fulfill({
      json: {
        access: userToken,
        refresh: refreshToken,
        user: {
          id: 101,
          name: "Test User",
          email: "test.user@example.com",
          role: "user",
          status: "active",
          plan: "Starter",
          date_joined: "2026-05-06",
        },
      },
    });
  });

  await page.goto("/login");
  await page.getByRole("button", { name: "Sign Up" }).click();
  await page.getByPlaceholder("Your name").fill("Test User");
  await page.getByPlaceholder("you@example.com").fill("test.user@example.com");
  await page.getByPlaceholder("Min 6 characters").fill("StrongPass123!");
  await page.getByPlaceholder("Repeat password").fill("StrongPass123!");
  await page.getByRole("button", { name: /Continue/i }).click();
  await page.getByRole("button", { name: /Starter/i }).click();
  await page.getByRole("button", { name: "Send Verification Code" }).click();
  await expect(page.getByText("Check your email")).toBeVisible();

  const otpInputs = page.locator('input[inputmode="numeric"]');
  for (let i = 0; i < 6; i += 1) {
    await otpInputs.nth(i).fill(String(i + 1));
  }
  await page.getByRole("button", { name: "Verify & Create Account" }).click();

  await expect(page.getByText("Welcome, Test!")).toBeVisible();
});

test("login flow shows the dashboard for valid credentials", async ({ page }) => {
  await mockCommonUserApis(page);

  await page.route("**/api/auth/login/", async (route) => {
    await route.fulfill({
      json: {
        access: userToken,
        refresh: refreshToken,
        user: {
          id: 101,
          name: "Test User",
          email: "test.user@example.com",
          role: "user",
          status: "active",
          plan: "Starter",
          date_joined: "2026-05-06",
        },
      },
    });
  });

  await page.goto("/login");
  await page.getByPlaceholder("you@example.com").fill("test.user@example.com");
  await page.locator('input[type="password"]').first().fill("StrongPass123!");
  await page.getByRole("button", { name: "Log In" }).nth(1).click();

  await expect(page.getByText("Welcome, Test!")).toBeVisible();
});

test("profile page updates the displayed name after save", async ({ page }) => {
  const user = {
    id: 101,
    name: "Test User",
    email: "test.user@example.com",
    role: "user",
    status: "active",
    plan: "Starter",
    date_joined: "2026-05-06",
  };

  await seedAuth(page, user);
  await mockCommonUserApis(page, user);
  await page.goto("/profile");

  await page.locator('input[value="Test User"]').fill("Updated User");
  await page.getByRole("button", { name: "Save Changes" }).click();

  await expect(page.getByText("Changes saved successfully")).toBeVisible();
  await expect(page.locator("p.font-bold").first()).toHaveText("Updated User");
});

test("admin can search a user and set status to inactive", async ({ page }) => {
  const admin = {
    id: 1,
    name: "Admin User",
    email: "admin@example.com",
    role: "admin",
    status: "active",
    plan: "Starter",
    date_joined: "2026-05-06",
  };
  const accounts = [
    {
      id: 41,
      name: "Alice Johnson",
      email: "alice@example.com",
      role: "user",
      status: "active",
      plan_name: "Starter",
      date_joined: "2026-05-05T00:00:00Z",
    },
  ];

  await seedAuth(page, admin);
  await mockCommonUserApis(page, admin);
  await page.route("**/api/plans/**", async (route) => {
    await route.fulfill({ json: [starterPlan] });
  });
  await page.route("**/api/admin/accounts/**", async (route) => {
    const method = route.request().method();
    if (method === "GET") {
      await route.fulfill({ json: { results: accounts } });
      return;
    }
    if (method === "PATCH") {
      accounts[0].status = "inactive";
      await route.fulfill({ json: accounts[0] });
      return;
    }
    await route.continue();
  });

  await page.goto("/admin/accounts");
  await page.getByPlaceholder("Name or email").fill("alice@example.com");
  const userRow = page.locator("div.group", { hasText: "alice@example.com" }).first();
  await expect(userRow).toBeVisible();
  await userRow.getByRole("button").click();
  await page.getByRole("button", { name: /Inactive/i }).click();
  await page.getByRole("button", { name: "Save Changes" }).click();

  await expect(page.getByText("Account updated successfully")).toBeVisible();
  await expect(page.getByText("inactive").first()).toBeVisible();
});

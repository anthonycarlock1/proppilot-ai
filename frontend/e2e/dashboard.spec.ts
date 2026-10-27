import { test, expect } from "@playwright/test";
import { writeFile } from "node:fs/promises";

const response = {
  reply:
    "The model predicts HVAC. Arrange an HVAC inspection. This prediction is advisory.",
  foundation_model: "browser-test-model",
  tool_results: [
    {
      tool: "assess_maintenance",
      result: {
        category: "hvac",
        urgency_assessment: {
          urgency: "high",
          recommended_priority: "high",
          probabilities: { low: 0.1, medium: 0.1, high: 0.7, emergency: 0.1 },
          provider: "sagemaker",
          model_version: "0.1.0",
          policy_version: "0.1.0",
          confirmed_hazards: [],
          escalation_reasons: [],
          manual_review_required: true,
        },
        probabilities: {
          hvac: 0.7,
          plumbing: 0.1,
          electrical: 0.1,
          general: 0.1,
        },
        provider: "sagemaker",
        model_version: "0.1.0",
      },
    },
  ],
};

test.beforeEach(async ({page}, info) => {
  if (!info.title.startsWith('real browser')) await page.route('**/api/tickets**',route=>route.fulfill({json:{items:[],next_cursor:null}}));
});

test("empty dashboard, chat success, activity and filtering", async ({
  page,
}) => {
  await page.route("**/api/chat", (route) => route.fulfill({ json: response }));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Welcome back, Anthony." }),
  ).toBeVisible();
  await expect(page.getByText("Your next step starts here")).toBeVisible();
  await page.getByRole("button", { name: "AC not cooling" }).click();
  await expect(page.getByLabel("Describe the maintenance issue")).toHaveValue(
    /air conditioner/,
  );
  await page.getByRole("button", { name: "Send request", exact: true }).click();
  await expect(page.getByText(response.reply)).toBeVisible();
  await expect(page.getByText("Priority: high", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Manual review required", { exact: true }).first(),
  ).toBeVisible();
  await expect(page.getByText("Hosted model · v0.1.0")).toBeVisible();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "Close assistant" })
    .click();
  await expect(
    page.getByRole("cell", { name: "HVAC", exact: true }),
  ).toBeVisible();
  await page.getByLabel("Filter by category").selectOption("plumbing");
  await expect(page.getByText("No matching requests")).toBeVisible();
  await page.getByLabel("Filter by category").selectOption("all");
  await page.getByLabel("Search requests").fill("not a matching request");
  await expect(page.getByText("No matching requests")).toBeVisible();
});

test("failed chat preserves input and does not invent activity", async ({
  page,
}) => {
  await page.route("**/api/chat", (route) =>
    route.fulfill({
      status: 502,
      json: { detail: "Simulated dependency failure" },
    }),
  );
  await page.goto("/");
  await page.getByRole("button", { name: "New request", exact: true }).click();
  await page
    .getByLabel("Describe the maintenance issue")
    .fill("The kitchen faucet is dripping.");
  await page.getByRole("button", { name: "Send request", exact: true }).click();
  await expect(page.getByRole("alert")).toContainText("could not complete");
  await expect(page.getByLabel("Describe the maintenance issue")).toHaveValue(
    "The kitchen faucet is dripping.",
  );
  await page.keyboard.press("Escape");
  await expect(page.getByText("Your next step starts here")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "New request", exact: true }),
  ).toBeFocused();
});

test("mobile navigation and assistant fit the viewport", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page
    .getByRole("navigation")
    .getByRole("button", { name: "AI assistant" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.screenshot({ path: "test-results/mobile.png", fullPage: true });
});

test("real browser request reaches Bedrock and SageMaker", async ({ page }) => {
  test.skip(
    process.env.PROPPILOT_LIVE_TEST !== "1",
    "Explicit opt-in for paid real-cloud calls",
  );
  test.setTimeout(240_000);
  await page.goto("/");
  await page.getByRole("button", { name: "AC not cooling" }).click();
  const network = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/chat") &&
      response.request().method() === "POST",
    { timeout: 230_000 },
  );
  await page.getByRole("button", { name: "Send request", exact: true }).click();
  const actual = await network;
  expect(actual.status()).toBe(200);
  const result = await actual.json();
  expect(result.tool_results[0].result.provider).toBe("sagemaker");
  expect(result.tool_results[0].result.category).toBe("hvac");
  expect(result.tool_results[0].result.urgency_assessment.provider).toBe(
    "sagemaker",
  );
  expect(
    result.tool_results[0].result.urgency_assessment.manual_review_required,
  ).toBe(true);
  await expect(
    page.getByText("Hosted urgency model", { exact: false }),
  ).toBeVisible();
  await expect(page.getByText("Hosted model · v0.1.0")).toBeVisible();
  await page.screenshot({ path: "test-results/live-chat.png", fullPage: true });
  expect(result.ticket_draft?.assessment_id).toBeTruthy();
  await page.getByRole('button',{name:'Review & create ticket',exact:true}).click();
  const confirmation=page.getByRole('form',{name:'Confirm maintenance ticket'});
  await confirmation.getByLabel('Property name',{exact:true}).fill('Portfolio Browser Verification (fictional)');
  await confirmation.getByLabel('Unit (optional)',{exact:true}).fill('QA');
  await confirmation.getByRole('checkbox').check();
  const created=page.waitForResponse(response=>response.url().endsWith('/api/tickets') && response.request().method()==='POST');
  await confirmation.getByRole('button',{name:'Confirm & create ticket',exact:true}).click();
  const creation=await created; expect([200,201]).toContain(creation.status());
  const createdBody=await creation.json(); const ticketId=createdBody.ticket.ticket_id;
  await expect(page.getByText('Ticket saved',{exact:true})).toBeVisible();
  await page.keyboard.press('Escape'); await page.reload();
  await page.getByRole('navigation').getByRole('button',{name:/^Tickets/}).click();
  const row=page.getByRole('row').filter({hasText:ticketId});
  await expect(row).toBeVisible();
  await row.getByRole('button',{name:'Start work',exact:true}).click();
  await row.getByRole('button',{name:'Resolve ticket',exact:true}).click();
  await expect(row.getByRole('button',{name:'Resolve ticket',exact:true})).toHaveCount(0);
  await page.reload(); await page.getByRole('navigation').getByRole('button',{name:/^Tickets/}).click();
  await expect(page.getByRole('row').filter({hasText:ticketId}).getByText('Resolved',{exact:true}).last()).toBeVisible();
  await page.screenshot({path:'test-results/live-tickets.png',fullPage:true});
  const persistedResponse=await page.request.get('/api/tickets/'+ticketId);
  expect(persistedResponse.status()).toBe(200);
  const persistedTicket=await persistedResponse.json(); expect(persistedTicket.status).toBe('resolved');
  expect(persistedTicket.version).toBe(3);
  await writeFile(
    process.env.PROPPILOT_EVIDENCE_PATH || "../docs/frontend-verification.json",
    JSON.stringify(
      {
        verified_at_utc: new Date().toISOString(),
        frontend_url: process.env.FRONTEND_URL || "http://127.0.0.1:5173",
        deployment_base_url: process.env.FRONTEND_URL || "http://127.0.0.1:5173",
        path: "Chrome -> React -> frontend proxy -> Bedrock/LangChain -> category and urgency APIs -> two SageMaker endpoints",
        result,
        persisted_ticket: persistedTicket,
        note: "Fictional QA ticket retained as resolved; browser reload verified persistence.",
      },
      null,
      2,
    ) + "\n",
  );
});

test("confirmed hazards are explicit request data", async ({ page }) => {
  let sent: any;
  await page.route("**/api/chat", async (route) => {
    sent = route.request().postDataJSON();
    await route.fulfill({ status: 502, json: { detail: "Test failure" } });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "New request", exact: true }).click();
  await page
    .getByText("Report a confirmed hazard (optional)", { exact: true })
    .click();
  await page.getByLabel("Gas odor", { exact: true }).check();
  await page
    .getByLabel("Describe the maintenance issue")
    .fill("I can smell gas near the stove.");
  await page.getByRole("button", { name: "Send request", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  expect(sent.confirmed_hazards).toEqual(["gas_odor"]);
  await expect(page.getByLabel("Gas odor", { exact: true })).toBeChecked();
});

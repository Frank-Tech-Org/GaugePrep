import { expect, test } from "@playwright/test";

const SLOW_3G = {
  offline: false,
  latency: 400,
  downloadThroughput: (400 * 1024) / 8,
  uploadThroughput: (400 * 1024) / 8,
};

test.use({ viewport: { width: 360, height: 740 }, locale: "fr-CA" });

test("on slow 3G the heading shows and the language menu opens within 3 s", async ({
  page,
  context,
}) => {
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", SLOW_3G);
  const start = Date.now();
  await page.goto("/", { waitUntil: "commit" });
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible({
    timeout: 3000,
  });
  await page.locator("summary", { hasText: "FR" }).click();
  await expect(page.locator("details[open]")).toHaveCount(1);
  expect(Date.now() - start).toBeLessThan(3000);
});

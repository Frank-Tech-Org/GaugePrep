import { expect, test, type Page } from "@playwright/test";

// WHY: on slow 3G the framework JavaScript lands after the page is read, so the shell's own
// controls must work from the HTML and the boot script alone (D-39).
async function openWithoutScripts(page: Page, locale: string) {
  await page.route(/\/_next\/static\/.*\.js$/, (route) => route.abort());
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  expect(locale).toBeTruthy();
}

test.use({ viewport: { width: 360, height: 740 }, locale: "fr-CA" });

test("a French browser reads French before any framework script", async ({
  page,
}) => {
  await openWithoutScripts(page, "fr-CA");
  await expect(page.getByText("Sachez où vous en êtes.")).toBeVisible();
  await expect(page.getByText("Know where you stand.")).toBeHidden();
});

test("the language menu opens, switches every string and remembers the pick", async ({
  page,
}) => {
  await openWithoutScripts(page, "fr-CA");
  await page.locator("summary", { hasText: "FR" }).click();
  await page.getByRole("radio", { name: "English" }).check();
  await expect(page.getByText("Know where you stand.")).toBeVisible();
  await expect(page.getByText("Sachez où vous en êtes.")).toBeHidden();
  await expect(page.locator("details[open]")).toHaveCount(0);
  await page.reload();
  await expect(page.getByText("Know where you stand.")).toBeVisible();
});

test("the theme menu applies a pick that survives a reload", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await openWithoutScripts(page, "fr-CA");
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(9, 39, 44)",
  );
  await page.locator("summary", { hasText: "Thème" }).click();
  await page.getByRole("radio", { name: "Clair" }).check();
  await expect(page.locator("body")).toHaveCSS(
    "background-color",
    "rgb(246, 243, 236)",
  );
  await page.reload();
  await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
});

test("both menus work by keyboard alone and keep 44 px targets", async ({
  page,
}) => {
  await openWithoutScripts(page, "fr-CA");
  const language = page.locator("summary", { hasText: "FR" });
  const theme = page.locator("summary", { hasText: "Thème" });
  for (const summary of [theme, language]) {
    const box = await summary.boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
    expect(box?.width).toBeGreaterThanOrEqual(44);
  }
  await language.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("details[open]")).toHaveCount(1);
  await page.keyboard.press("Escape");
  await expect(page.locator("details[open]")).toHaveCount(0);
  await expect(language).toBeFocused();
  await page.keyboard.press("Enter");
  await page.keyboard.press("Tab");
  await page.keyboard.press("ArrowDown");
  await page.keyboard.press("Space");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByText("Know where you stand.")).toBeVisible();
  for (const radio of await page.locator("input[data-setting]").all()) {
    const box = await radio.locator("xpath=ancestor::label").boundingBox();
    expect(box?.height).toBeGreaterThanOrEqual(44);
  }
});

// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { BOOT_SCRIPT } from "./boot-script";
import { applyTheme, parseThemeChoice } from "./theme";

describe("parseThemeChoice", () => {
  it("keeps an explicit light or dark pick", () => {
    expect(parseThemeChoice("light")).toBe("light");
    expect(parseThemeChoice("dark")).toBe("dark");
  });

  it("follows the system for anything else", () => {
    expect(parseThemeChoice(null)).toBe("system");
    expect(parseThemeChoice("system")).toBe("system");
    expect(parseThemeChoice("purple")).toBe("system");
  });
});

describe("applyTheme", () => {
  it("sets data-theme for a pick and clears it for the system", () => {
    const root = document.createElement("html");
    applyTheme(root, "dark");
    expect(root.dataset.theme).toBe("dark");
    applyTheme(root, "system");
    expect(root.hasAttribute("data-theme")).toBe(false);
  });
});

describe("boot script", () => {
  const root = document.documentElement;

  function run(languages: string[]) {
    Object.defineProperty(navigator, "languages", {
      value: languages,
      configurable: true,
    });
    new Function(BOOT_SCRIPT)();
  }

  beforeEach(() => {
    localStorage.clear();
    root.removeAttribute("data-theme");
    root.lang = "en";
  });

  afterEach(() => localStorage.clear());

  it("applies a stored theme and language before paint", () => {
    localStorage.setItem("gp.theme", "light");
    localStorage.setItem("gp.locale", "fr");
    run(["en-US"]);
    expect(root.dataset.theme).toBe("light");
    expect(root.lang).toBe("fr");
  });

  it("leaves the theme to the system when nothing is stored", () => {
    run(["en-US"]);
    expect(root.hasAttribute("data-theme")).toBe(false);
  });

  it.each([
    [["fr-CA"], "fr"],
    [["fr"], "fr"],
    [["en-GB"], "en"],
    [["de"], "en"],
  ])("picks the language from %j", (languages, expected) => {
    run(languages);
    expect(root.lang).toBe(expected);
  });
});

describe("boot script menus", () => {
  const root = document.documentElement;

  function menu(setting: string, values: string[]) {
    const details = document.createElement("details");
    details.open = true;
    const summary = document.createElement("summary");
    summary.tabIndex = 0;
    details.append(summary);
    for (const value of values) {
      const input = document.createElement("input");
      input.type = "radio";
      input.name = setting;
      input.value = value;
      input.dataset.setting = setting;
      details.append(input);
    }
    document.body.append(details);
    return details;
  }

  function change(input: Element | undefined) {
    input?.dispatchEvent(new Event("change", { bubbles: true }));
  }

  beforeEach(() => {
    localStorage.clear();
    root.removeAttribute("data-theme");
    document.body.replaceChildren();
    new Function(BOOT_SCRIPT)();
  });

  it("applies and stores a language pick, then closes the menu", () => {
    const details = menu("locale", ["fr", "en"]);
    change(details.querySelectorAll("input")[0]);
    expect(root.lang).toBe("fr");
    expect(localStorage.getItem("gp.locale")).toBe("fr");
    expect(details.open).toBe(false);
  });

  it("applies a theme pick and clears it for the system", () => {
    const details = menu("theme", ["system", "light", "dark"]);
    const [system, , dark] = Array.from(details.querySelectorAll("input"));
    change(dark);
    expect(root.dataset.theme).toBe("dark");
    expect(localStorage.getItem("gp.theme")).toBe("dark");
    change(system);
    expect(root.hasAttribute("data-theme")).toBe(false);
  });

  it("ignores a value it does not know", () => {
    const details = menu("locale", ["de"]);
    change(details.querySelector("input") ?? undefined);
    expect(localStorage.getItem("gp.locale")).toBeNull();
    expect(details.open).toBe(true);
  });

  it("closes on Escape and returns focus to the summary", () => {
    const details = menu("locale", ["fr", "en"]);
    document.body.dispatchEvent(
      new KeyboardEvent("keydown", { key: "Escape", bubbles: true }),
    );
    expect(details.open).toBe(false);
    expect(document.activeElement).toBe(details.querySelector("summary"));
  });

  it("closes on a click outside", () => {
    const details = menu("locale", ["fr", "en"]);
    document.body.click();
    expect(details.open).toBe(false);
  });
});

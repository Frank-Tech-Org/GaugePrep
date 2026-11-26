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

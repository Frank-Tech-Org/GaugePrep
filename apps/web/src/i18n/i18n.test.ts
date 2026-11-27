import { describe, expect, it } from "vitest";
import en from "../messages/en/shell.json";
import { flatten, messagesFor } from "./catalogues";
import { detectLocale } from "./locale";
import { translate } from "./translate";

const featureFiles = import.meta.glob<Record<string, string>>(
  "../messages/*/*.json",
  { eager: true, import: "default" },
);

function keysByLanguage(): Record<string, Record<string, string[]>> {
  const result: Record<string, Record<string, string[]>> = {};
  for (const [path, messages] of Object.entries(featureFiles)) {
    const [, language, file] = /messages\/(\w+)\/(\w+)\.json$/.exec(path) ?? [];
    (result[language] ??= {})[file] = Object.keys(messages).sort();
  }
  return result;
}

describe("detectLocale", () => {
  it("opens French for a French browser", () => {
    expect(detectLocale(null, ["fr-CA", "en"])).toBe("fr");
    expect(detectLocale(null, ["fr"])).toBe("fr");
  });

  it("opens English for any other browser", () => {
    expect(detectLocale(null, ["en-US"])).toBe("en");
    expect(detectLocale(null, ["de"])).toBe("en");
    expect(detectLocale(null, [])).toBe("en");
  });

  it("keeps the stored choice over the browser language", () => {
    expect(detectLocale("en", ["fr-FR"])).toBe("en");
    expect(detectLocale("fr", ["en-US"])).toBe("fr");
  });

  it("ignores a stored value that is not a language we have", () => {
    expect(detectLocale("xx", ["fr"])).toBe("fr");
  });
});

describe("translate", () => {
  it("returns the text for a key", () => {
    expect(translate({ "a.b": "Hello" }, "a.b")).toBe("Hello");
  });

  it("fills placeholders and leaves unknown ones", () => {
    expect(
      translate({ k: "Hi {name}, {n} left {x}" }, "k", { name: "A", n: 3 }),
    ).toBe("Hi A, 3 left {x}");
  });

  it("returns the key when it is missing", () => {
    expect(translate({}, "missing.key")).toBe("missing.key");
  });
});

describe("catalogues", () => {
  it("has the same files and keys in French and English", () => {
    const { fr, en: english } = keysByLanguage();
    expect(fr).toEqual(english);
  });

  it("uses the same placeholders in both languages", () => {
    const placeholders = (text: string) => text.match(/\{\w+\}/g)?.sort() ?? [];
    const fr = messagesFor("fr");
    const en = messagesFor("en");
    for (const key of Object.keys(en)) {
      expect(placeholders(fr[key])).toEqual(placeholders(en[key]));
    }
  });

  it("leaves no message empty", () => {
    for (const locale of ["fr", "en"] as const) {
      for (const text of Object.values(messagesFor(locale))) {
        expect(text.trim()).not.toBe("");
      }
    }
  });

  it("flattens feature files into feature.key entries", () => {
    expect(flatten({ shell: en })["shell.skipToContent"]).toBe(
      en.skipToContent,
    );
  });
});

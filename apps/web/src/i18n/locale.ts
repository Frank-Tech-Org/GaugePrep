export const LOCALES = ["fr", "en"] as const;
export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";
export const LOCALE_STORAGE_KEY = "gp.locale";

export function isLocale(value: unknown): value is Locale {
  return LOCALES.some((locale) => locale === value);
}

/** The stored choice wins; otherwise French when the browser's first language is French. */
export function detectLocale(
  stored: string | null,
  languages: readonly string[],
): Locale {
  if (isLocale(stored)) return stored;
  return /^fr(-|_|$)/i.test(languages[0] ?? "") ? "fr" : DEFAULT_LOCALE;
}

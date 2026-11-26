import enHome from "../messages/en/home.json";
import enShell from "../messages/en/shell.json";
import frHome from "../messages/fr/home.json";
import frShell from "../messages/fr/shell.json";
import type { Locale } from "./locale";
import type { Messages } from "./translate";

const en = { shell: enShell, home: enHome };
// Typed against English so a key missing in French fails the type check.
const fr: typeof en = { shell: frShell, home: frHome };

export type MessageKey = {
  [
    Feature in keyof typeof en
  ]: `${Feature}.${keyof (typeof en)[Feature] & string}`;
}[keyof typeof en];

const byLocale = { en, fr } as const;

/** Flattens one language's per-feature catalogues into `feature.key` entries. */
export function flatten(
  catalogue: Readonly<Record<string, Messages>>,
): Messages {
  return Object.fromEntries(
    Object.entries(catalogue).flatMap(([feature, messages]) =>
      Object.entries(messages).map(([key, text]) => [
        `${feature}.${key}`,
        text,
      ]),
    ),
  );
}

const flat: Record<Locale, Messages> = {
  en: flatten(byLocale.en),
  fr: flatten(byLocale.fr),
};

export function messagesFor(locale: Locale): Messages {
  return flat[locale];
}

"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { readStored, writeStored } from "../lib/safe-storage";
import { messagesFor, type MessageKey } from "./catalogues";
import { detectLocale, LOCALE_STORAGE_KEY, type Locale } from "./locale";
import { translate, type Params } from "./translate";

type I18n = {
  /** Null until the browser's choice is known; text renders in both languages until then. */
  locale: Locale | null;
  setLocale: (locale: Locale) => void;
};

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale | null>(null);

  useEffect(() => {
    const detected = detectLocale(
      readStored(LOCALE_STORAGE_KEY),
      navigator.languages?.length ? navigator.languages : [navigator.language],
    );
    document.documentElement.lang = detected;
    setLocaleState(detected);
  }, []);

  const setLocale = useCallback((next: Locale) => {
    writeStored(LOCALE_STORAGE_KEY, next);
    document.documentElement.lang = next;
    setLocaleState(next);
  }, []);

  const value = useMemo(() => ({ locale, setLocale }), [locale, setLocale]);
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n needs an I18nProvider");
  return context;
}

/** Text for one key in the active language; before it is known, one `<span>` per language. */
export function Msg({ id, params }: { id: MessageKey; params?: Params }) {
  const { locale } = useI18n();
  if (locale) return <>{translate(messagesFor(locale), id, params)}</>;
  return (
    <>
      <span data-locale="fr">{translate(messagesFor("fr"), id, params)}</span>
      <span data-locale="en">{translate(messagesFor("en"), id, params)}</span>
    </>
  );
}

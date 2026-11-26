"use client";

import type { ReactNode } from "react";
import type { MessageKey } from "../i18n/catalogues";
import { LOCALES, type Locale } from "../i18n/locale";
import { Msg, useI18n } from "../i18n/provider";
import { useTheme } from "../theme/provider";
import { THEME_CHOICES, type ThemeChoice } from "../theme/theme";
import styles from "./Header.module.css";
import { SettingMenu, type SettingOption } from "./SettingMenu";

// WHY: the product name is the same in both languages, so it stays out of the catalogues.
const BRAND_NAME = "GaugePrep";

const LANGUAGE_LABELS: Record<Locale, MessageKey> = {
  fr: "shell.languageFr",
  en: "shell.languageEn",
};

const THEME_LABELS: Record<ThemeChoice, MessageKey> = {
  system: "shell.themeSystem",
  light: "shell.themeLight",
  dark: "shell.themeDark",
};

const LANGUAGE_OPTIONS: readonly SettingOption<Locale>[] = LOCALES.map(
  (value) => ({ value, labelKey: LANGUAGE_LABELS[value] }),
);

const THEME_OPTIONS: readonly SettingOption<ThemeChoice>[] = THEME_CHOICES.map(
  (value) => ({ value, labelKey: THEME_LABELS[value] }),
);

function Icon({ children }: { children: ReactNode }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function Header() {
  const { locale, setLocale } = useI18n();
  const { choice, setChoice } = useTheme();

  return (
    <header className={styles.header}>
      <div className={styles.inner}>
        <a href="/" className={styles.logo}>
          <img
            className={styles.logoLight}
            src="/brand/lockup.svg"
            alt={BRAND_NAME}
            width="858"
            height="256"
          />
          <img
            className={styles.logoDark}
            src="/brand/lockup-white.svg"
            alt={BRAND_NAME}
            width="858"
            height="256"
          />
        </a>
        <div className={styles.controls}>
          <SettingMenu
            setting="theme"
            legendKey="shell.theme"
            trigger={
              <>
                <Icon>
                  <circle cx="12" cy="12" r="9" />
                  <path d="M12 3v18a9 9 0 0 0 0-18z" fill="currentColor" />
                </Icon>
                <Msg id="shell.theme" />
              </>
            }
            options={THEME_OPTIONS}
            value={choice}
            onChange={setChoice}
          />
          <SettingMenu
            setting="locale"
            legendKey="shell.language"
            trigger={
              <>
                <Icon>
                  <circle cx="12" cy="12" r="9" />
                  <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
                </Icon>
                <span className={styles.code}>
                  <Msg id="shell.languageCurrent" />
                </span>
              </>
            }
            options={LANGUAGE_OPTIONS}
            value={locale}
            onChange={setLocale}
          />
        </div>
      </div>
    </header>
  );
}

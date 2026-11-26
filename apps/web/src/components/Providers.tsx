"use client";

import type { ReactNode } from "react";
import { I18nProvider } from "../i18n/provider";
import { ThemeProvider } from "../theme/provider";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <I18nProvider>
      <ThemeProvider>{children}</ThemeProvider>
    </I18nProvider>
  );
}

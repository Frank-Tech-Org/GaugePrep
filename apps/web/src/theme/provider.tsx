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
import {
  applyTheme,
  parseThemeChoice,
  THEME_STORAGE_KEY,
  type ThemeChoice,
} from "./theme";

type ThemeState = {
  choice: ThemeChoice | null;
  setChoice: (choice: ThemeChoice) => void;
};

const ThemeContext = createContext<ThemeState | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [choice, setChoiceState] = useState<ThemeChoice | null>(null);

  useEffect(() => {
    setChoiceState(parseThemeChoice(readStored(THEME_STORAGE_KEY)));
  }, []);

  const setChoice = useCallback((next: ThemeChoice) => {
    writeStored(THEME_STORAGE_KEY, next);
    applyTheme(document.documentElement, next);
    setChoiceState(next);
  }, []);

  const value = useMemo(() => ({ choice, setChoice }), [choice, setChoice]);
  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme(): ThemeState {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme needs a ThemeProvider");
  return context;
}

"use client";

import {
  useEffect,
  useId,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from "react";
import type { MessageKey } from "../i18n/catalogues";
import { Msg } from "../i18n/provider";
import styles from "./SettingMenu.module.css";

export type SettingOption<V extends string> = {
  value: V;
  labelKey: MessageKey;
};

type Props<V extends string> = {
  legendKey: MessageKey;
  trigger: ReactNode;
  options: readonly SettingOption<V>[];
  value: V | null;
  onChange: (value: V) => void;
};

/** A button that opens a group of native radios; Escape and outside clicks close it. */
export function SettingMenu<V extends string>({
  legendKey,
  trigger,
  options,
  value,
  onChange,
}: Props<V>) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelId = useId();
  const name = useId();

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const radios = rootRef.current?.querySelectorAll<HTMLInputElement>("input");
    const checked = Array.from(radios ?? []).find((input) => input.checked);
    (checked ?? radios?.[0])?.focus();
  }, [open]);

  function onKeyDown(event: KeyboardEvent) {
    if (event.key !== "Escape" || !open) return;
    setOpen(false);
    buttonRef.current?.focus();
  }

  function choose(next: V) {
    onChange(next);
    setOpen(false);
    buttonRef.current?.focus();
  }

  return (
    <div ref={rootRef} className={styles.root} onKeyDown={onKeyDown}>
      <button
        ref={buttonRef}
        type="button"
        className={styles.button}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((current) => !current)}
      >
        {trigger}
      </button>
      <fieldset id={panelId} className={styles.panel} hidden={!open}>
        <legend className={styles.legend}>
          <Msg id={legendKey} />
        </legend>
        {options.map((option) => (
          <label key={option.value} className={styles.option}>
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => choose(option.value)}
            />
            <span>
              <Msg id={option.labelKey} />
            </span>
          </label>
        ))}
      </fieldset>
    </div>
  );
}

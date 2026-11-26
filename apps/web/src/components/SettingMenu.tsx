"use client";

import { useId, type ReactNode } from "react";
import type { MessageKey } from "../i18n/catalogues";
import { Msg } from "../i18n/provider";
import styles from "./SettingMenu.module.css";

export type SettingOption<V extends string> = {
  value: V;
  labelKey: MessageKey;
};

type Props<V extends string> = {
  /** Read by the boot script, which applies the choice before React loads. */
  setting: "theme" | "locale";
  legendKey: MessageKey;
  trigger: ReactNode;
  options: readonly SettingOption<V>[];
  value: V | null;
  onChange: (value: V) => void;
};

/** A native disclosure holding a radio group; the boot script opens, closes and applies it. */
export function SettingMenu<V extends string>({
  setting,
  legendKey,
  trigger,
  options,
  value,
  onChange,
}: Props<V>) {
  const name = useId();

  return (
    <details className={styles.root}>
      <summary className={styles.button}>{trigger}</summary>
      <fieldset className={styles.panel}>
        <legend className={styles.legend}>
          <Msg id={legendKey} />
        </legend>
        {options.map((option) => (
          <label key={option.value} className={styles.option}>
            <input
              type="radio"
              name={name}
              data-setting={setting}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange(option.value)}
            />
            <span>
              <Msg id={option.labelKey} />
            </span>
          </label>
        ))}
      </fieldset>
    </details>
  );
}

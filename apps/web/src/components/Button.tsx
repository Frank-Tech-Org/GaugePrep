import type { ButtonHTMLAttributes, ReactNode } from "react";
import styles from "./Button.module.css";

type Variant = "primary" | "secondary" | "ghost";

type Props = {
  variant?: Variant;
  /** Renders a link that looks like the button, for moves between pages. */
  href?: string;
  children: ReactNode;
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className">;

/** The brand Button (docs/design/brand/components/Button) on our tokens, md size. */
export function Button({
  variant = "primary",
  href,
  children,
  ...rest
}: Props) {
  const className = `${styles.button} ${styles[variant]}`;
  if (href !== undefined) {
    return (
      <a className={className} href={href}>
        {children}
      </a>
    );
  }
  return (
    <button type="button" className={className} {...rest}>
      {children}
    </button>
  );
}

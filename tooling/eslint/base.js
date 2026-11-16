// Shared ESLint base for every TypeScript package; the Next.js scaffold adds its own rules on top.
import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  js.configs.recommended,
  tseslint.configs.recommended,
);

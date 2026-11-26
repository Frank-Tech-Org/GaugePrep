import base from "../../tooling/eslint/base.js";

export default [
  { ignores: ["**/.next/**", "**/out/**", "**/dist/**", "**/next-env.d.ts"] },
  ...base,
];

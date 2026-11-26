import base from "../../tooling/eslint/base.js";

export default [
  { ignores: [".next/**", "out/**", "next-env.d.ts", "dist/**"] },
  ...base,
];

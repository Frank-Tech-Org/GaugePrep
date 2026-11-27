import { readFileSync } from "node:fs";
import { join } from "node:path";
import process from "node:process";

type Token = { name: string; value?: { light?: string; dark?: string } };

const SOURCE = join(process.cwd(), "../../docs/design/brand/tokens.json");

/** The computed-style form (rgb(r, g, b)) of a themed brand colour. */
export function brandRgb(name: string, mode: "light" | "dark"): string {
  const tokens: { color: { tokens: Token[] } } = JSON.parse(
    readFileSync(SOURCE, "utf8"),
  );
  const hex = tokens.color.tokens.find((t) => t.name === name)?.value?.[mode];
  if (!hex) throw new Error(`no token ${name}`);
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return `rgb(${r}, ${g}, ${b})`;
}

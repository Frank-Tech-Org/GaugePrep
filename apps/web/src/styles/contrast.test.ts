import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

const css = readFileSync(new URL("./tokens.css", import.meta.url), "utf8");

function block(selector: string): string {
  const start = css.indexOf(selector);
  return css.slice(start, css.indexOf("}", start));
}

function colours(source: string): Record<string, string> {
  const result: Record<string, string> = {};
  for (const [, name, hex] of source.matchAll(
    /--([\w-]+):\s*(#[0-9A-Fa-f]{6})/g,
  )) {
    result[name] = hex;
  }
  return result;
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((index) => {
    const channel = parseInt(hex.slice(index, index + 2), 16) / 255;
    return channel <= 0.03928
      ? channel / 12.92
      : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function ratio(a: string, b: string): number {
  const [light, dark] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (light + 0.05) / (dark + 0.05);
}

const light = colours(block(":root {"));
const dark = { ...light, ...colours(block('[data-theme="dark"]')) };

describe.each([
  ["light", light],
  ["dark", dark],
])("%s theme", (_name, theme) => {
  it.each([
    ["text", "bg"],
    ["text", "surface"],
    ["text-muted", "bg"],
    ["text-muted", "surface"],
    ["on-accent", "accent"],
  ])("%s on %s reaches 4.5:1", (foreground, background) => {
    const fg =
      theme[foreground] ?? theme[foreground.replace("accent", "amber")];
    const bg = theme[background] ?? theme.amber;
    expect(ratio(fg, bg)).toBeGreaterThanOrEqual(4.5);
  });
});

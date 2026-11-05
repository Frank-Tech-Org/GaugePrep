import { describe, expect, it } from "vitest";
import { isCommit, isEnvironment, renderPlaceholder } from "./placeholder";

const SHA = "4b42ae2c0ffee0123456789abcdef0123456789a";

describe("renderPlaceholder", () => {
  it("shows the product, the environment and the commit", () => {
    const html = renderPlaceholder("staging", SHA);
    expect(html).toContain("<h1>GaugePrep</h1>");
    expect(html).toContain('<strong id="environment">staging</strong>');
    expect(html).toContain(`<code id="commit">${SHA}</code>`);
  });

  it("accepts a short commit", () => {
    expect(renderPlaceholder("dev", "4b42ae2")).toContain("4b42ae2");
  });

  it("rejects a commit that is not plain hex", () => {
    expect(() => renderPlaceholder("dev", "<script>alert(1)</script>")).toThrow(
      /commit/,
    );
    expect(() => renderPlaceholder("dev", "")).toThrow(/commit/);
  });

  it("rejects an unknown environment", () => {
    expect(() =>
      renderPlaceholder("production" as unknown as "dev", SHA),
    ).toThrow(/environment/i);
  });
});

describe("guards", () => {
  it("knows dev and staging only", () => {
    expect(isEnvironment("dev")).toBe(true);
    expect(isEnvironment("staging")).toBe(true);
    expect(isEnvironment("production")).toBe(false);
  });

  it("rejects uppercase and too-short commits", () => {
    expect(isCommit("ABCDEF1")).toBe(false);
    expect(isCommit("abc12")).toBe(false);
  });
});

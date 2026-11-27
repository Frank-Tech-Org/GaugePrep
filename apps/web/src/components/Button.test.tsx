// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Button } from "./Button";

afterEach(cleanup);

describe("Button", () => {
  it("renders a button that calls onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>Réessayer</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Réessayer" }));
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("renders a link when it has an href", () => {
    render(<Button href="/">Accueil</Button>);
    expect(
      screen.getByRole("link", { name: "Accueil" }).getAttribute("href"),
    ).toBe("/");
  });
});

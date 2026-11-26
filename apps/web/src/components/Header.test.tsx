// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { Msg } from "../i18n/provider";
import { Header } from "./Header";
import { Providers } from "./Providers";

function setBrowserLanguages(languages: string[]) {
  Object.defineProperty(navigator, "languages", {
    value: languages,
    configurable: true,
  });
}

function renderShell() {
  return render(
    <Providers>
      <Header />
      <p>
        <Msg id="home.title" />
      </p>
    </Providers>,
  );
}

beforeEach(() => {
  localStorage.clear();
  document.documentElement.removeAttribute("data-theme");
  setBrowserLanguages(["en-US"]);
});

afterEach(cleanup);

describe("shell language and theme", () => {
  it("opens in French for a French browser", async () => {
    setBrowserLanguages(["fr-CA"]);
    renderShell();
    expect(await screen.findByText("Sachez où vous en êtes.")).toBeTruthy();
    expect(document.documentElement.lang).toBe("fr");
  });

  it("switches every string to English and remembers it", async () => {
    setBrowserLanguages(["fr-FR"]);
    const user = userEvent.setup();
    renderShell();
    await user.click(await screen.findByRole("button", { name: /FR/ }));
    await user.click(screen.getByRole("radio", { name: "English" }));
    expect(screen.getByText("Know where you stand.")).toBeTruthy();
    expect(screen.queryByText("Sachez où vous en êtes.")).toBeNull();
    expect(localStorage.getItem("gp.locale")).toBe("en");
    cleanup();
    renderShell();
    expect(await screen.findByText("Know where you stand.")).toBeTruthy();
  });

  it("works by keyboard alone", async () => {
    const user = userEvent.setup();
    renderShell();
    const button = await screen.findByRole("button", { name: /EN/ });
    button.focus();
    await user.keyboard("{Enter}");
    expect(button.getAttribute("aria-expanded")).toBe("true");
    await user.keyboard("{ArrowUp}{Escape}");
    expect(button.getAttribute("aria-expanded")).toBe("false");
    expect(document.activeElement).toBe(button);
  });

  it("keeps a light pick and sets it on the page", async () => {
    const user = userEvent.setup();
    renderShell();
    await user.click(await screen.findByRole("button", { name: /Theme/ }));
    await user.click(screen.getByRole("radio", { name: "Light" }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(localStorage.getItem("gp.theme")).toBe("light");
  });
});

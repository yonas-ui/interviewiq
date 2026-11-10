
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import Login from "./Login";

afterEach(() => {
  cleanup();
  localStorage.clear();
});

describe("login flow", () => {
  it("redirects unauthenticated users to the sign-in form", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(screen.getByRole("button", { name: "Sign in" }).textContent).toBe("Sign in");
  });

  it("shows the registration fields when switching modes", () => {
    render(
      <MemoryRouter>
        <Login />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "No account? Register" }));

    expect(screen.getByText("Name")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Create account" })).toBeTruthy();
  });
});

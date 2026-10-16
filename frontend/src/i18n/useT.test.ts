import { beforeEach, describe, expect, it } from "vitest";
import { useT } from "./useT";

describe("translations", () => {
  beforeEach(() => localStorage.clear());
  it("uses the selected language", () => {
    localStorage.setItem("lang", "hi");
    expect(useT()("pods")).toBe("पॉड");
  });
  it("falls back to English for an unsupported language", () => {
    localStorage.setItem("lang", "xx");
    expect(useT()("unknown")).toBe("Unknown");
  });
});

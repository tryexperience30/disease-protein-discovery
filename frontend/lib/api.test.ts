import { afterEach, describe, expect, it, vi } from "vitest";
import { apiGet } from "@/lib/api";

describe("api failure state", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("surfaces backend detail on 404", async () => {
    vi.stubGlobal(
      "fetch",
      async () =>
        ({
          ok: false,
          status: 404,
          json: async () => ({ detail: "Unknown disease ID: X" }),
        }) as Response
    );
    await expect(apiGet("/api/diseases/X")).rejects.toThrow("Unknown disease ID: X");
  });
});

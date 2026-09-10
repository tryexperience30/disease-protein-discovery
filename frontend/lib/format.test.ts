import { describe, expect, it } from "vitest";
import { apiUrl } from "@/lib/api";
import { formatInt, formatScore, nodeColor } from "@/lib/format";

describe("format helpers", () => {
  it("formats integers", () => {
    expect(formatInt(21557)).toContain("21");
    expect(formatInt(null)).toBe("—");
  });

  it("formats scores", () => {
    expect(formatScore(0.123456)).toBe("0.1235");
    expect(formatScore(null)).toBe("—");
  });

  it("colors node types", () => {
    expect(nodeColor("associated")).toBe("#4aa3f0");
    expect(nodeColor("predicted")).toBe("#e3a04a");
  });
});

describe("api url", () => {
  it("prefixes the backend origin", () => {
    expect(apiUrl("/api/diseases")).toContain("/api/diseases");
  });
});

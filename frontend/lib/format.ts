export function formatInt(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}

export function formatScore(n: number | null | undefined, digits = 4): string {
  if (n == null || Number.isNaN(n)) return "—";
  if (Math.abs(n) > 0 && Math.abs(n) < 1e-3) return n.toExponential(2);
  return n.toFixed(digits);
}

export function nodeColor(type: string): string {
  if (type === "associated") return "#4aa3f0";
  if (type === "predicted") return "#e3a04a";
  return "#6d7b8d";
}

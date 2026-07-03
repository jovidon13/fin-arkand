/**
 * Money helpers. The API sends amounts as STRINGS (money-in-JSON contract) to
 * avoid float error. Parse only for display/formatting — never do arithmetic on
 * the parsed float for anything authoritative.
 */

export type MoneyString = string;

const FORMATTER = new Intl.NumberFormat("ru-RU", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function parseMoney(value: MoneyString | number | null | undefined): number {
  if (value === null || value === undefined || value === "") return 0;
  const n = typeof value === "number" ? value : Number(value);
  return Number.isFinite(n) ? n : 0;
}

/** Format an amount with thousands separators and 2 decimals (сомони). */
export function formatMoney(
  value: MoneyString | number | null | undefined,
  opts: { sign?: boolean; currency?: string } = {},
): string {
  const n = parseMoney(value);
  const body = FORMATTER.format(Math.abs(n));
  const sign = opts.sign ? (n > 0 ? "+" : n < 0 ? "−" : "") : n < 0 ? "−" : "";
  const currency = opts.currency ? ` ${opts.currency}` : "";
  return `${sign}${body}${currency}`;
}

/** CSS variable for the money color by sign (design tokens: money-in/out/zero). */
export function signColor(value: MoneyString | number): string {
  const n = parseMoney(value);
  if (n > 0) return "var(--money-in)";
  if (n < 0) return "var(--money-out)";
  return "var(--money-zero)";
}

/** Color a value where income is green and expense is red, given a tx kind. */
export function kindColor(kind: "income" | "expense" | string): string {
  return kind === "income" ? "var(--money-in)" : "var(--money-out)";
}

import { formatMoney, kindColor, parseMoney, signColor } from "@/shared/lib";
import type { MoneyString } from "@/shared/lib/money";

interface MoneyProps {
  value: MoneyString | number;
  /** When set, colors by transaction kind (income green / expense red). */
  kind?: "income" | "expense" | string;
  /** Show explicit + for positive values. */
  showSign?: boolean;
  /** Color by numeric sign (default true). */
  colored?: boolean;
  currency?: string;
}

/**
 * Money display. Colour is design-token semantics, never the brand crimson:
 * income = green, expense/negative = signalling red, zero = dark ink.
 */
export function Money({
  value,
  kind,
  showSign = false,
  colored = true,
  currency,
}: MoneyProps) {
  const color = !colored
    ? "var(--money-zero)"
    : kind
      ? kindColor(kind)
      : signColor(value);
  const display =
    kind === "expense" && parseMoney(value) > 0
      ? `−${formatMoney(value, { currency })}`
      : formatMoney(value, { sign: showSign, currency });
  return (
    <span className="ak-money" style={{ color }}>
      {display}
    </span>
  );
}

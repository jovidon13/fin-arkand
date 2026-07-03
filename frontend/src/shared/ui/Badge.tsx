import type { ReactNode } from "react";

type Tone = "neutral" | "success" | "warning" | "error" | "info" | "brand";

const TONE_STYLE: Record<Tone, { bg: string; color: string }> = {
  neutral: { bg: "var(--n-100)", color: "var(--n-700)" },
  success: { bg: "#e7f4ec", color: "var(--success)" },
  warning: { bg: "#fdf1e3", color: "var(--warning)" },
  error: { bg: "#fdeaea", color: "var(--error)" },
  info: { bg: "#e8eefb", color: "var(--info)" },
  brand: { bg: "var(--crimson-50)", color: "var(--brand)" },
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  const s = TONE_STYLE[tone];
  return (
    <span className="ak-badge" style={{ background: s.bg, color: s.color }}>
      {children}
    </span>
  );
}

/** Maps a domain status string to a tone + Russian label. */
const STATUS_TONE: Record<string, Tone> = {
  // transactions
  draft: "neutral",
  pending: "warning",
  confirmed: "success",
  rejected: "error",
  void: "neutral",
  // debts
  open: "warning",
  partially_settled: "info",
  settled: "success",
  // transfers / approvals
  approved: "success",
  // payroll
  calculated: "info",
  paid: "success",
};

export function StatusBadge({ status, label }: { status: string; label?: string }) {
  const tone = STATUS_TONE[status] ?? "neutral";
  return <Badge tone={tone}>{label ?? status}</Badge>;
}

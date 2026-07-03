import type { ReactNode } from "react";

export function Spinner() {
  return <span className="ak-spinner" />;
}

export function Loading({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="ak-empty" style={{ display: "flex", gap: 10, justifyContent: "center" }}>
      <Spinner /> {label}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="ak-empty">{children}</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="ak-empty" style={{ color: "var(--error)" }}>
      {message}
    </div>
  );
}

export function Stat({
  label,
  value,
  color,
}: {
  label: ReactNode;
  value: ReactNode;
  color?: string;
}) {
  return (
    <div className="ak-stat">
      <div className="ak-stat__label">{label}</div>
      <div className="ak-stat__value" style={{ color }}>
        {value}
      </div>
    </div>
  );
}

export function StatGrid({ children }: { children: ReactNode }) {
  return <div className="ak-stat-grid">{children}</div>;
}

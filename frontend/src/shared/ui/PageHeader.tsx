import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <div className="ak-page-header">
      <div>
        <div className="ak-page-header__title">{title}</div>
        {subtitle && <div className="ak-page-header__subtitle">{subtitle}</div>}
      </div>
      {actions && <div style={{ display: "flex", gap: 10 }}>{actions}</div>}
    </div>
  );
}

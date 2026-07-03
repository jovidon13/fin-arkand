import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { Input } from "@/shared/ui";

export interface Period {
  date_from?: string;
  date_to?: string;
}

export function PeriodFilter({
  value,
  onChange,
  children,
}: {
  value: Period;
  onChange: (p: Period) => void;
  children?: ReactNode;
}) {
  const { t } = useTranslation();
  return (
    <div
      style={{
        display: "flex",
        gap: 12,
        alignItems: "flex-end",
        flexWrap: "wrap",
        marginBottom: 18,
      }}
    >
      <label style={{ fontSize: 13, fontWeight: 600, color: "var(--n-700)" }}>
        {t("common.from")}
        <Input
          type="date"
          value={value.date_from ?? ""}
          onChange={(e) => onChange({ ...value, date_from: e.target.value || undefined })}
          style={{ marginTop: 4 }}
        />
      </label>
      <label style={{ fontSize: 13, fontWeight: 600, color: "var(--n-700)" }}>
        {t("common.to")}
        <Input
          type="date"
          value={value.date_to ?? ""}
          onChange={(e) => onChange({ ...value, date_to: e.target.value || undefined })}
          style={{ marginTop: 4 }}
        />
      </label>
      {children}
    </div>
  );
}

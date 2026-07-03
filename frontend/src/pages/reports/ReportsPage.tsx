import { useTranslation } from "react-i18next";

import { Card, PageHeader } from "@/shared/ui";

// NOTE: placeholder — replaced by the full implementation.
export function ReportsPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("reports.title")} subtitle={t("reports.subtitle")} />
      <Card>{t("common.loading")}</Card>
    </>
  );
}

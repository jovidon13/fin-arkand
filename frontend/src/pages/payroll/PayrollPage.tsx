import { useTranslation } from "react-i18next";

import { Card, PageHeader } from "@/shared/ui";

// NOTE: placeholder — replaced by the full implementation.
export function PayrollPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("payroll.title")} subtitle={t("payroll.subtitle")} />
      <Card>{t("common.loading")}</Card>
    </>
  );
}

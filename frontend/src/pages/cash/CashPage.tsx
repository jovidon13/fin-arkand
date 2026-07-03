import { useTranslation } from "react-i18next";

import { Card, PageHeader } from "@/shared/ui";

// NOTE: placeholder — replaced by the full implementation.
export function CashPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("cash.title")} subtitle={t("cash.subtitle")} />
      <Card>{t("common.loading")}</Card>
    </>
  );
}

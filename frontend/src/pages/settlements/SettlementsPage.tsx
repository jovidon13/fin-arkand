import { useTranslation } from "react-i18next";

import { Card, PageHeader } from "@/shared/ui";

// NOTE: placeholder — replaced by the full implementation.
export function SettlementsPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("settlements.title")} subtitle={t("settlements.subtitle")} />
      <Card>{t("common.loading")}</Card>
    </>
  );
}

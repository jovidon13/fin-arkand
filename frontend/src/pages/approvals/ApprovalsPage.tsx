import { useTranslation } from "react-i18next";

import { Card, PageHeader } from "@/shared/ui";

// NOTE: placeholder — replaced by the full implementation.
export function ApprovalsPage() {
  const { t } = useTranslation();
  return (
    <>
      <PageHeader title={t("approvals.title")} subtitle={t("approvals.subtitle")} />
      <Card>{t("common.loading")}</Card>
    </>
  );
}

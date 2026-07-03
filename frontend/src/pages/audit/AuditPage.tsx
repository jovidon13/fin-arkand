import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuditLogs, type AuditLog } from "@/entities/audit";
import { formatDateTime } from "@/shared/lib";
import { Card, type Column, Input, Loading, PageHeader, Table } from "@/shared/ui";

export function AuditPage() {
  const { t } = useTranslation();
  const [action, setAction] = useState("");
  const { data, isLoading } = useAuditLogs({ action: action || undefined });

  const columns: Column<AuditLog>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDateTime(r.created_at) },
    { key: "action", header: "Действие", render: (r) => <code>{r.action}</code> },
    { key: "actor", header: "Кто", render: (r) => r.actor_name ?? "система" },
    { key: "target", header: "Объект", render: (r) => `${r.target_type ?? "—"} #${r.object_id ?? "—"}` },
  ];

  return (
    <>
      <PageHeader title={t("nav.audit")} subtitle="Журнал всех операций (кто, что, когда)" />
      <Card>
        <Input
          placeholder="Фильтр по действию, напр. transfer.approved"
          value={action}
          onChange={(e) => setAction(e.target.value)}
          style={{ maxWidth: 360, marginBottom: 16 }}
        />
        {isLoading ? (
          <Loading />
        ) : (
          <Table columns={columns} rows={data?.results ?? []} rowKey={(r) => r.id} />
        )}
      </Card>
    </>
  );
}

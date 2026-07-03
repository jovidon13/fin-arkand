import { useTranslation } from "react-i18next";

import { useUsers, type AppUser } from "@/entities/user";
import { Badge, Card, type Column, Loading, PageHeader, Table } from "@/shared/ui";

export function UsersPage() {
  const { t } = useTranslation();
  const { data, isLoading } = useUsers();

  const columns: Column<AppUser>[] = [
    { key: "username", header: t("auth.username"), render: (r) => r.username },
    { key: "name", header: "Имя", render: (r) => r.full_name || "—" },
    { key: "role", header: "Роль", render: (r) => <Badge tone="brand">{r.role_name ?? "—"}</Badge> },
    { key: "business", header: t("common.business"), render: (r) => r.business_name ?? "—" },
    {
      key: "active",
      header: t("common.status"),
      render: (r) => (
        <Badge tone={r.is_active ? "success" : "neutral"}>{r.is_active ? "Активен" : "Выкл"}</Badge>
      ),
    },
  ];

  return (
    <>
      <PageHeader title={t("nav.users")} subtitle="Пользователи и роли (администратор)" />
      <Card>
        {isLoading ? (
          <Loading />
        ) : (
          <Table columns={columns} rows={data?.results ?? []} rowKey={(r) => r.id} />
        )}
      </Card>
    </>
  );
}

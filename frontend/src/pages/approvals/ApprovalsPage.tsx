import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { useBusinesses } from "@/entities/business";
import {
  useApprovalRequests,
  type ApprovalFilters,
  type ApprovalRequest,
} from "@/entities/approval";
import { CreateApprovalRequestModal, VoteButtons } from "@/features/approval";
import { formatDate } from "@/shared/lib";
import {
  Button,
  Card,
  type Column,
  Loading,
  Money,
  PageHeader,
  Select,
  StatusBadge,
  Table,
} from "@/shared/ui";
import { PeriodFilter, type Period } from "@/widgets/period-filter";

export function ApprovalsPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const canCreate = (user?.can_manage_finance || user?.is_finance_staff) ?? false;
  const isOwner = user?.is_owner ?? false;

  const [period, setPeriod] = useState<Period>({});
  const [business, setBusiness] = useState<number | "">("");
  const [status, setStatus] = useState<string>("");
  const [open, setOpen] = useState(false);

  const businesses = useBusinesses();
  const filters: ApprovalFilters = useMemo(
    () => ({
      ...period,
      business: business || undefined,
      status: status || undefined,
      ordering: "-occurred_on",
    }),
    [period, business, status],
  );
  const requests = useApprovalRequests(filters);

  const columns: Column<ApprovalRequest>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDate(r.occurred_on) },
    { key: "business", header: t("common.business"), render: (r) => r.business_name ?? "—" },
    { key: "purpose", header: t("approvals.purpose"), render: (r) => r.purpose },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} kind="expense" />,
    },
    {
      key: "progress",
      header: t("approvals.progress"),
      numeric: true,
      render: (r) => `${r.approvals_count} / ${r.required_votes}`,
    },
    {
      key: "status",
      header: t("common.status"),
      render: (r) => <StatusBadge status={r.status} label={r.status_display} />,
    },
    {
      key: "actions",
      header: t("common.actions"),
      render: (r) =>
        isOwner && r.status === "pending" ? <VoteButtons requestId={r.id} /> : "—",
    },
  ];

  return (
    <>
      <PageHeader
        title={t("approvals.title")}
        subtitle={t("approvals.rule")}
        actions={
          canCreate && (
            <Button onClick={() => setOpen(true)}>+ {t("approvals.new_request")}</Button>
          )
        }
      />

      <Card bodyClassName="ak-filters">
        <PeriodFilter value={period} onChange={setPeriod}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--n-700)" }}>
            {t("common.business")}
            <Select
              value={business}
              placeholder={t("common.all")}
              onChange={(e) => setBusiness(e.target.value ? Number(e.target.value) : "")}
              options={(businesses.data ?? []).map((b) => ({ value: b.id, label: b.name }))}
              style={{ marginTop: 4 }}
            />
          </label>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--n-700)" }}>
            {t("common.status")}
            <Select
              value={status}
              placeholder={t("common.all")}
              onChange={(e) => setStatus(e.target.value)}
              options={[
                { value: "pending", label: t("status.pending") },
                { value: "approved", label: t("status.approved") },
                { value: "rejected", label: t("status.rejected") },
              ]}
              style={{ marginTop: 4 }}
            />
          </label>
        </PeriodFilter>

        {requests.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={columns}
            rows={requests.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <CreateApprovalRequestModal open={open} onClose={() => setOpen(false)} />
    </>
  );
}

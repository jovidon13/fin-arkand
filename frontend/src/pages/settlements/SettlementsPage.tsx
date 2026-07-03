import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import {
  useApproveTransfer,
  useDebtRegistry,
  useRejectTransfer,
  useTransfers,
  type DebtRegistryRow,
  type Transfer,
} from "@/entities/settlement";
import { CreateTransferModal, SettleDebtModal } from "@/features/settlement";
import { toApiError } from "@/shared/api";
import { formatDate } from "@/shared/lib";
import {
  Badge,
  Button,
  Card,
  type Column,
  Loading,
  Money,
  PageHeader,
  StatusBadge,
  Table,
  useToast,
} from "@/shared/ui";

export function SettlementsPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const { user } = useAuth();
  const canManage = user?.can_manage_finance ?? false;

  const [transferOpen, setTransferOpen] = useState(false);
  const [settleFor, setSettleFor] = useState<DebtRegistryRow | null>(null);

  const registry = useDebtRegistry();
  const transfers = useTransfers({ ordering: "-occurred_on" });

  const approve = useApproveTransfer();
  const reject = useRejectTransfer();

  const act = async (
    fn: { mutateAsync: (id: number) => Promise<unknown> },
    id: number,
    ok: string,
  ) => {
    try {
      await fn.mutateAsync(id);
      toast.push(ok, "success");
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const debtColumns: Column<DebtRegistryRow>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDate(r.occurred_on) },
    { key: "debtor", header: t("settlements.debtor"), render: (r) => r.debtor_name },
    { key: "creditor", header: t("settlements.creditor"), render: (r) => r.creditor_name },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} colored={false} />,
    },
    {
      key: "outstanding",
      header: t("settlements.outstanding"),
      numeric: true,
      render: (r) => <Money value={r.outstanding} />,
    },
    {
      key: "barter",
      header: t("settlements.barter"),
      render: (r) => (r.is_barter ? <Badge tone="info">{t("settlements.barter")}</Badge> : "—"),
    },
    {
      key: "status",
      header: t("common.status"),
      render: (r) => <StatusBadge status={r.status} label={t(`status.${r.status}`)} />,
    },
    {
      key: "actions",
      header: t("common.actions"),
      render: (r) =>
        canManage && r.status !== "settled" ? (
          <Button size="sm" variant="secondary" onClick={() => setSettleFor(r)}>
            {t("settlements.close_debt")}
          </Button>
        ) : (
          "—"
        ),
    },
  ];

  const transferColumns: Column<Transfer>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDate(r.occurred_on) },
    {
      key: "route",
      header: t("settlements.transfer"),
      render: (r) => `${r.from_business_name ?? r.from_business} → ${r.to_business_name ?? r.to_business}`,
    },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} colored={false} />,
    },
    {
      key: "barter",
      header: t("settlements.barter"),
      render: (r) => (r.is_barter ? <Badge tone="info">{t("settlements.barter")}</Badge> : "—"),
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
        canManage && r.status === "pending" ? (
          <div style={{ display: "flex", gap: 6 }}>
            <Button
              size="sm"
              variant="success"
              onClick={() => act(approve, r.id, t("settlements.msg_transfer_approved"))}
            >
              {t("common.approve")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => act(reject, r.id, t("settlements.msg_transfer_rejected"))}
            >
              {t("common.reject")}
            </Button>
          </div>
        ) : (
          "—"
        ),
    },
  ];

  return (
    <>
      <PageHeader
        title={t("settlements.title")}
        subtitle={t("settlements.subtitle")}
        actions={
          canManage && (
            <Button onClick={() => setTransferOpen(true)}>+ {t("settlements.add_transfer")}</Button>
          )
        }
      />

      <Card header={t("settlements.registry")}>
        {registry.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={debtColumns}
            rows={registry.data ?? []}
            rowKey={(r) => r.debt_id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <Card header={t("settlements.transfers")}>
        {transfers.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={transferColumns}
            rows={transfers.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <CreateTransferModal open={transferOpen} onClose={() => setTransferOpen(false)} />
      <SettleDebtModal
        open={settleFor !== null}
        debtId={settleFor?.debt_id ?? null}
        outstanding={settleFor?.outstanding ?? ""}
        onClose={() => setSettleFor(null)}
      />
    </>
  );
}

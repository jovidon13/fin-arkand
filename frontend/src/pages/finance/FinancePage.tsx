import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { useBusinesses } from "@/entities/business";
import {
  useConfirmTransaction,
  useRejectTransaction,
  useProfitByBusiness,
  useTransactions,
  type Transaction,
  type TransactionFilters,
} from "@/entities/transaction";
import { toApiError } from "@/shared/api";
import { formatDate } from "@/shared/lib";
import {
  Button,
  Card,
  type Column,
  Loading,
  Money,
  PageHeader,
  Select,
  Stat,
  StatGrid,
  StatusBadge,
  Table,
  useToast,
} from "@/shared/ui";
import { AddTransactionModal } from "@/features/finance";
import { PeriodFilter, type Period } from "@/widgets/period-filter";

export function FinancePage() {
  const { t } = useTranslation();
  const toast = useToast();
  const { user } = useAuth();
  const canManage = user?.can_manage_finance ?? false;

  const [period, setPeriod] = useState<Period>({});
  const [business, setBusiness] = useState<number | "">("");
  const [modal, setModal] = useState<null | "income" | "expense">(null);

  const businesses = useBusinesses();
  const filters: TransactionFilters = useMemo(
    () => ({
      ...period,
      business: business || undefined,
      ordering: "-occurred_on",
    }),
    [period, business],
  );
  const txs = useTransactions(filters);
  const profit = useProfitByBusiness(period);

  const confirm = useConfirmTransaction();
  const reject = useRejectTransaction();

  const totals = useMemo(() => {
    const rows = profit.data ?? [];
    const income = rows.reduce((s, r) => s + Number(r.income), 0);
    const expense = rows.reduce((s, r) => s + Number(r.expense), 0);
    return { income, expense, profit: income - expense };
  }, [profit.data]);

  const act = async (fn: typeof confirm, id: number, ok: string) => {
    try {
      await fn.mutateAsync(id);
      toast.push(ok, "success");
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const columns: Column<Transaction>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDate(r.occurred_on) },
    { key: "business", header: t("common.business"), render: (r) => r.business_name },
    {
      key: "kind",
      header: t("common.category"),
      render: (r) => r.category_name ?? r.kind_display,
    },
    { key: "counterparty", header: t("finance.counterparty"), render: (r) => r.counterparty || "—" },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} kind={r.kind} />,
    },
    { key: "method", header: t("common.method"), render: (r) => r.method_display },
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
              onClick={() => act(confirm, r.id, "Подтверждено")}
            >
              {t("common.confirm")}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => act(reject, r.id, "Отклонено")}>
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
        title={t("finance.title")}
        subtitle={t("finance.subtitle")}
        actions={
          canManage && (
            <>
              <Button variant="success" onClick={() => setModal("income")}>
                + {t("finance.add_income")}
              </Button>
              <Button variant="danger" onClick={() => setModal("expense")}>
                + {t("finance.add_expense")}
              </Button>
            </>
          )
        }
      />

      <StatGrid>
        <Stat label={t("money.income")} value={<Money value={totals.income} colored={false} />} color="var(--money-in)" />
        <Stat label={t("money.expense")} value={<Money value={totals.expense} colored={false} />} color="var(--money-out)" />
        <Stat label={t("money.profit")} value={<Money value={totals.profit} />} />
      </StatGrid>

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
        </PeriodFilter>

        {txs.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={columns}
            rows={txs.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <AddTransactionModal open={modal !== null} kind={modal ?? "income"} onClose={() => setModal(null)} />
    </>
  );
}

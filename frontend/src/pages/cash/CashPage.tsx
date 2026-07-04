import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import {
  useCashOperations,
  useCashRegisters,
  type CashOperation,
  type CashOperationFilters,
  type CashRegister,
} from "@/entities/cash";
import { formatDate, kindColor } from "@/shared/lib";
import {
  Badge,
  Button,
  Card,
  type Column,
  EmptyState,
  Loading,
  Money,
  PageHeader,
  Select,
  Table,
} from "@/shared/ui";
import { AddCashOperationModal } from "@/features/cash";
import { OperationDocumentsModal } from "@/features/documents";
import { PeriodFilter, type Period } from "@/widgets/period-filter";

function RegisterCard({ r }: { r: CashRegister }) {
  const { t } = useTranslation();
  return (
    <Card>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
          <strong style={{ fontSize: 15 }}>{r.name}</strong>
          <Badge tone={r.is_active ? "success" : "neutral"}>
            {r.is_active ? t("status.open") : t("cash.inactive")}
          </Badge>
        </div>
        <div style={{ fontSize: 13, color: "var(--n-600)" }}>
          {r.business_name ?? r.code}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontSize: 12, color: "var(--n-600)" }}>{t("money.balance")}</span>
          <span style={{ fontSize: 18, fontWeight: 700 }}>
            <Money value={r.balance} />
          </span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 12 }}>
          <span style={{ fontSize: 12, color: "var(--n-600)" }}>{t("cash.limit")}</span>
          <span style={{ fontSize: 13, color: "var(--n-700)" }}>
            <Money value={r.turnover_limit} colored={false} />
          </span>
        </div>
      </div>
    </Card>
  );
}

export function CashPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  // Кассир заводит операции своей кассы (изоляция гарантируется бэкендом:
  // список касс уже отфильтрован по ответственности, чужая касса → 403).
  const canAdd = (user?.can_manage_finance || user?.is_cashier) ?? false;

  const [period, setPeriod] = useState<Period>({});
  const [register, setRegister] = useState<number | "">("");
  const [modal, setModal] = useState(false);
  const [docsFor, setDocsFor] = useState<number | null>(null);

  const registers = useCashRegisters();

  const filters: CashOperationFilters = useMemo(
    () => ({
      ...period,
      register: register || undefined,
    }),
    [period, register],
  );
  const operations = useCashOperations(filters);

  const columns: Column<CashOperation>[] = [
    { key: "date", header: t("common.date"), render: (r) => formatDate(r.occurred_on) },
    { key: "register", header: t("cash.register"), render: (r) => r.register_name },
    {
      key: "kind",
      header: t("common.category"),
      render: (r) => (
        <span style={{ color: kindColor(r.kind), fontWeight: 600 }}>{r.kind_display}</span>
      ),
    },
    {
      key: "counterparty",
      header: t("finance.counterparty"),
      render: (r) => r.counterparty || "—",
    },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} kind={r.kind} />,
    },
    { key: "method", header: t("common.method"), render: (r) => r.method_display },
    { key: "created_by", header: t("finance.created_by"), render: (r) => r.created_by_name || "—" },
    {
      key: "docs",
      header: "📎",
      render: (r) => (
        <Button size="sm" variant="ghost" onClick={() => setDocsFor(r.id)}>
          📎 {r.documents_count ?? 0}
        </Button>
      ),
    },
  ];

  return (
    <>
      <PageHeader
        title={t("cash.title")}
        subtitle={t("cash.subtitle")}
        actions={
          canAdd && (
            <Button onClick={() => setModal(true)}>+ {t("cash.add_operation")}</Button>
          )
        }
      />

      {registers.isLoading ? (
        <Loading />
      ) : (registers.data ?? []).length === 0 ? (
        <Card>
          <EmptyState>{t("common.no_data")}</EmptyState>
        </Card>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: 14,
            marginBottom: 18,
          }}
        >
          {(registers.data ?? []).map((r) => (
            <RegisterCard key={r.id} r={r} />
          ))}
        </div>
      )}

      <Card bodyClassName="ak-filters">
        <PeriodFilter value={period} onChange={setPeriod}>
          <label style={{ fontSize: 13, fontWeight: 600, color: "var(--n-700)" }}>
            {t("cash.register")}
            <Select
              value={register}
              placeholder={t("common.all")}
              onChange={(e) => setRegister(e.target.value ? Number(e.target.value) : "")}
              options={(registers.data ?? []).map((r) => ({ value: r.id, label: r.name }))}
              style={{ marginTop: 4 }}
            />
          </label>
        </PeriodFilter>

        <div style={{ fontSize: 12, color: "var(--n-600)", marginBottom: 12 }}>
          {t("cash.limit_note")}
        </div>

        {operations.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={columns}
            rows={operations.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <AddCashOperationModal open={modal} onClose={() => setModal(false)} />
      <OperationDocumentsModal
        open={docsFor !== null}
        target="cashoperation"
        objectId={docsFor}
        canUpload={canAdd}
        onClose={() => setDocsFor(null)}
      />
    </>
  );
}

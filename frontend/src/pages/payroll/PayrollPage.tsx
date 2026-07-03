import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import {
  useApprovePayroll,
  useEmployees,
  usePayPayroll,
  usePayrollItems,
  usePayrollRuns,
  type Employee,
  type PayrollItem,
  type PayrollRun,
} from "@/entities/payroll";
import { RunPayrollModal } from "@/features/payroll";
import { toApiError } from "@/shared/api";
import { MONTHS_RU } from "@/shared/lib";
import {
  Badge,
  Button,
  Card,
  type Column,
  Loading,
  Money,
  PageHeader,
  Stat,
  StatGrid,
  StatusBadge,
  Table,
  useToast,
} from "@/shared/ui";

function monthLabel(month: number): string {
  return MONTHS_RU[month - 1] ?? String(month);
}

export function PayrollPage() {
  const { t } = useTranslation();
  const toast = useToast();
  const { user } = useAuth();
  const canManage = user?.can_manage_finance ?? false;

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);

  const runs = usePayrollRuns({ ordering: "-year,-month" });
  const employees = useEmployees({ is_active: true });
  const items = usePayrollItems(selectedRun);

  const approve = useApprovePayroll();
  const pay = usePayPayroll();

  const latestRun = runs.data?.results[0];

  const act = async (fn: typeof approve, id: number, ok: string) => {
    try {
      await fn.mutateAsync(id);
      toast.push(ok, "success");
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const runColumns: Column<PayrollRun>[] = [
    { key: "year", header: t("payroll.year"), render: (r) => r.year },
    { key: "month", header: t("payroll.period_month"), render: (r) => monthLabel(r.month) },
    {
      key: "status",
      header: t("common.status"),
      render: (r) => <StatusBadge status={r.status} label={r.status_display} />,
    },
    {
      key: "items_count",
      header: t("payroll.items_count"),
      numeric: true,
      render: (r) => r.items_count ?? 0,
    },
    {
      key: "total",
      header: t("common.total"),
      numeric: true,
      render: (r) => <Money value={r.total} colored={false} />,
    },
    {
      key: "actions",
      header: t("common.actions"),
      render: (r) => (
        <div style={{ display: "flex", gap: 6 }}>
          <Button
            size="sm"
            variant={selectedRun === r.id ? "primary" : "ghost"}
            onClick={() => setSelectedRun(selectedRun === r.id ? null : r.id)}
          >
            {t("payroll.items")}
          </Button>
          {canManage && r.status === "calculated" && (
            <Button
              size="sm"
              variant="success"
              onClick={() => act(approve, r.id, t("payroll.approve_success"))}
            >
              {t("common.approve")}
            </Button>
          )}
          {canManage && r.status === "approved" && (
            <Button
              size="sm"
              variant="success"
              onClick={() => act(pay, r.id, t("payroll.pay_success"))}
            >
              {t("payroll.pay")}
            </Button>
          )}
        </div>
      ),
    },
  ];

  const employeeColumns: Column<Employee>[] = [
    { key: "full_name", header: t("payroll.employee"), render: (r) => r.full_name },
    { key: "business", header: t("common.business"), render: (r) => r.business_name ?? "—" },
    { key: "position", header: t("payroll.position"), render: (r) => r.position || "—" },
    {
      key: "salary_type",
      header: t("payroll.salary_type"),
      render: (r) => r.salary_type_display ?? r.salary_type,
    },
    {
      key: "base_salary",
      header: t("payroll.base"),
      numeric: true,
      render: (r) => <Money value={r.base_salary} colored={false} />,
    },
    {
      key: "is_salesperson",
      header: t("payroll.salesperson"),
      render: (r) =>
        r.is_salesperson ? (
          <Badge tone="brand">{t("common.yes")}</Badge>
        ) : (
          <Badge tone="neutral">{t("common.no")}</Badge>
        ),
    },
    { key: "scheme", header: t("payroll.scheme"), render: (r) => r.scheme_name ?? "—" },
  ];

  const itemColumns: Column<PayrollItem>[] = [
    { key: "employee_name", header: t("payroll.employee"), render: (r) => r.employee_name ?? "—" },
    {
      key: "base_amount",
      header: t("payroll.base"),
      numeric: true,
      render: (r) => <Money value={r.base_amount} colored={false} />,
    },
    {
      key: "bonus_amount",
      header: t("payroll.bonus"),
      numeric: true,
      render: (r) => <Money value={r.bonus_amount} colored={false} />,
    },
    {
      key: "total_amount",
      header: t("common.total"),
      numeric: true,
      render: (r) => <Money value={r.total_amount} />,
    },
  ];

  return (
    <>
      <PageHeader
        title={t("payroll.title")}
        subtitle={t("payroll.subtitle")}
        actions={
          canManage && (
            <Button onClick={() => setModalOpen(true)}>+ {t("payroll.run")}</Button>
          )
        }
      />

      <StatGrid>
        <Stat
          label={t("payroll.fund")}
          value={<Money value={latestRun?.total ?? 0} colored={false} />}
          color="var(--brand)"
        />
      </StatGrid>

      <Card header={t("payroll.runs")}>
        {runs.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={runColumns}
            rows={runs.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      {selectedRun !== null && (
        <Card header={t("payroll.items")}>
          {items.isLoading ? (
            <Loading />
          ) : (
            <Table
              columns={itemColumns}
              rows={items.data?.results ?? []}
              rowKey={(r) => r.id}
              empty={t("common.no_data")}
            />
          )}
        </Card>
      )}

      <Card header={t("payroll.employees")}>
        {employees.isLoading ? (
          <Loading />
        ) : (
          <Table
            columns={employeeColumns}
            rows={employees.data?.results ?? []}
            rowKey={(r) => r.id}
            empty={t("common.no_data")}
          />
        )}
      </Card>

      <RunPayrollModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  );
}

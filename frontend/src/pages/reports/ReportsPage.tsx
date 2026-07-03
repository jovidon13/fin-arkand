import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  useCashReport,
  usePayrollReport,
  usePnlReport,
  useSettlementsReport,
  type BusinessProfitRow,
  type CashRegisterRow,
  type DebtRow,
  type PayrollFundRow,
} from "@/entities/report";
import { formatMoney } from "@/shared/lib";
import {
  Button,
  Card,
  type Column,
  ErrorState,
  Loading,
  Money,
  PageHeader,
  Stat,
  StatGrid,
  StatusBadge,
  Table,
} from "@/shared/ui";
import { PeriodFilter, type Period } from "@/widgets/period-filter";

const CAT_COLORS = [
  "var(--cat-kras)",
  "var(--cat-biryuza)",
  "var(--cat-yantar)",
  "var(--cat-slanets)",
  "var(--cat-sliva)",
  "var(--cat-zelen)",
];

type Tab = "pnl" | "cash" | "settlements" | "payroll";

const TABS: Tab[] = ["pnl", "cash", "settlements", "payroll"];

export function ReportsPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>({});
  const [tab, setTab] = useState<Tab>("pnl");

  return (
    <>
      <PageHeader title={t("reports.title")} subtitle={t("reports.subtitle")} />

      <PeriodFilter value={period} onChange={setPeriod} />

      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 18 }}>
        {TABS.map((k) => (
          <Button
            key={k}
            size="sm"
            variant={tab === k ? "primary" : "ghost"}
            onClick={() => setTab(k)}
          >
            {t(`reports.${k}`)}
          </Button>
        ))}
      </div>

      {tab === "pnl" && <PnlSection period={period} />}
      {tab === "cash" && <CashSection period={period} />}
      {tab === "settlements" && <SettlementsSection period={period} />}
      {tab === "payroll" && <PayrollSection />}
    </>
  );
}

function PnlSection({ period }: { period: Period }) {
  const { t } = useTranslation();
  const { data, isLoading, isError } = usePnlReport(period);

  const columns: Column<BusinessProfitRow>[] = [
    { key: "business", header: t("common.business"), render: (r) => r.business_name },
    {
      key: "income",
      header: t("money.income"),
      numeric: true,
      render: (r) => <Money value={r.income} colored={false} />,
    },
    {
      key: "expense",
      header: t("money.expense"),
      numeric: true,
      render: (r) => <Money value={r.expense} colored={false} />,
    },
    {
      key: "profit",
      header: t("money.profit"),
      numeric: true,
      render: (r) => <Money value={r.profit} />,
    },
  ];

  const chartData = (data?.by_business ?? []).map((b) => ({
    name: b.business_name,
    profit: Number(b.profit),
  }));

  if (isLoading) return <Loading />;
  if (isError || !data) return <ErrorState message={t("common.no_data")} />;

  return (
    <>
      <StatGrid>
        <Stat
          label={t("money.income")}
          value={<Money value={data.consolidated.income} colored={false} />}
          color="var(--money-in)"
        />
        <Stat
          label={t("money.expense")}
          value={<Money value={data.consolidated.expense} colored={false} />}
          color="var(--money-out)"
        />
        <Stat label={t("money.profit")} value={<Money value={data.consolidated.profit} />} />
      </StatGrid>

      <Card header={t("reports.by_business")}>
        <Table
          columns={columns}
          rows={data.by_business}
          rowKey={(r) => r.business_id}
          empty={t("common.no_data")}
        />
      </Card>

      <Card header={t("money.profit") + " · " + t("reports.by_business")}>
        <div style={{ width: "100%", height: 340 }}>
          <ResponsiveContainer>
            <BarChart data={chartData} margin={{ top: 8, right: 12, bottom: 8, left: 12 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--n-200)" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: "var(--n-600)" }} />
              <YAxis
                tick={{ fontSize: 12, fill: "var(--n-600)" }}
                tickFormatter={(v) => formatMoney(v)}
                width={90}
              />
              <Tooltip formatter={(v: number) => formatMoney(v)} />
              <Bar dataKey="profit" name={t("money.profit")} radius={[4, 4, 0, 0]}>
                {chartData.map((_, i) => (
                  <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </>
  );
}

function CashSection({ period }: { period: Period }) {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useCashReport(period);

  const columns: Column<CashRegisterRow>[] = [
    { key: "register", header: t("cash.register"), render: (r) => r.register_name },
    { key: "business", header: t("common.business"), render: (r) => r.business_name },
    {
      key: "balance",
      header: t("money.balance"),
      numeric: true,
      render: (r) => <Money value={r.balance} colored={false} />,
    },
    {
      key: "turnover",
      header: t("money.turnover"),
      numeric: true,
      render: (r) => <Money value={r.turnover} colored={false} />,
    },
    {
      key: "limit",
      header: t("cash.limit"),
      numeric: true,
      render: (r) => <Money value={r.limit} colored={false} />,
    },
  ];

  if (isLoading) return <Loading />;
  if (isError || !data) return <ErrorState message={t("common.no_data")} />;

  return (
    <>
      <StatGrid>
        <Stat
          label={t("money.balance")}
          value={<Money value={data.total_balance} colored={false} />}
        />
        <Stat
          label={t("money.turnover")}
          value={<Money value={data.total_turnover} colored={false} />}
        />
      </StatGrid>

      <Card header={t("reports.cash")}>
        <Table
          columns={columns}
          rows={data.registers}
          rowKey={(r) => r.register_id}
          empty={t("common.no_data")}
        />
      </Card>
    </>
  );
}

function SettlementsSection({ period }: { period: Period }) {
  const { t } = useTranslation();
  const { data, isLoading, isError } = useSettlementsReport(period);

  const columns: Column<DebtRow>[] = [
    {
      key: "parties",
      header: t("settlements.debtor") + " → " + t("settlements.creditor"),
      render: (r) => `${r.debtor_name} → ${r.creditor_name}`,
    },
    {
      key: "outstanding",
      header: t("settlements.outstanding"),
      numeric: true,
      render: (r) => <Money value={r.outstanding} colored={false} />,
    },
    {
      key: "amount",
      header: t("common.amount"),
      numeric: true,
      render: (r) => <Money value={r.amount} colored={false} />,
    },
    {
      key: "status",
      header: t("common.status"),
      render: (r) => <StatusBadge status={r.status} label={t(`status.${r.status}`)} />,
    },
  ];

  if (isLoading) return <Loading />;
  if (isError || !data) return <ErrorState message={t("common.no_data")} />;

  return (
    <>
      <StatGrid>
        <Stat
          label={t("settlements.outstanding")}
          value={<Money value={data.total_outstanding} colored={false} />}
          color="var(--warning)"
        />
      </StatGrid>

      <Card header={t("reports.settlements")}>
        <Table
          columns={columns}
          rows={data.registry}
          rowKey={(r) => `${r.debtor_id}-${r.creditor_id}`}
          empty={t("common.no_data")}
        />
      </Card>
    </>
  );
}

function PayrollSection() {
  const { t } = useTranslation();
  const { data, isLoading, isError } = usePayrollReport();

  const columns: Column<PayrollFundRow>[] = [
    { key: "business", header: t("common.business"), render: (r) => r.business_name },
    {
      key: "fund",
      header: t("payroll.fund"),
      numeric: true,
      render: (r) => <Money value={r.fund} colored={false} />,
    },
  ];

  if (isLoading) return <Loading />;
  if (isError || !data) return <ErrorState message={t("common.no_data")} />;

  return (
    <>
      <StatGrid>
        <Stat label={t("payroll.fund")} value={<Money value={data.fund} colored={false} />} />
      </StatGrid>

      <Card header={t("reports.by_business")}>
        <Table
          columns={columns}
          rows={data.by_business}
          rowKey={(r) => r.business_id}
          empty={t("common.no_data")}
        />
      </Card>
    </>
  );
}

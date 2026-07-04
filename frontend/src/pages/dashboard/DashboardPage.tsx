import { useState } from "react";
import { useTranslation } from "react-i18next";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useDashboard, type ExternalDebtRow } from "@/entities/report";
import { formatMoney } from "@/shared/lib";
import { Card, ErrorState, Loading, Money, PageHeader, Stat, StatGrid } from "@/shared/ui";
import { PeriodFilter, type Period } from "@/widgets/period-filter";

const CAT_COLORS = [
  "var(--cat-kras)",
  "var(--cat-biryuza)",
  "var(--cat-yantar)",
  "var(--cat-slanets)",
  "var(--cat-sliva)",
  "var(--cat-zelen)",
];

export function DashboardPage() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>({});
  const { data, isLoading, isError } = useDashboard(period);

  const chartData = (data?.by_business ?? []).map((b) => ({
    name: b.business_name,
    profit: Number(b.profit),
    income: Number(b.income),
    expense: Number(b.expense),
  }));

  return (
    <>
      <PageHeader title={t("nav.dashboard")} subtitle={t("reports.consolidated")} />

      {data && (
        <StatGrid>
          <Stat
            label={"📈 " + t("dashboard.income_today")}
            value={<Money value={data.today.income} colored={false} />}
            color="var(--money-in)"
          />
          <Stat
            label={"📉 " + t("dashboard.expense_today")}
            value={<Money value={data.today.expense} colored={false} />}
            color="var(--money-out)"
          />
          <Stat
            label={"💎 " + t("dashboard.profit_today")}
            value={<Money value={data.today.profit} />}
          />
        </StatGrid>
      )}

      <PeriodFilter value={period} onChange={setPeriod} />

      {isLoading && <Loading />}
      {isError && <ErrorState message="Не удалось загрузить данные" />}

      {data && (
        <>
          <StatGrid>
            <Stat label={t("money.income")} value={<Money value={data.income} colored={false} />} color="var(--money-in)" />
            <Stat label={t("money.expense")} value={<Money value={data.expense} colored={false} />} color="var(--money-out)" />
            <Stat label={t("money.profit")} value={<Money value={data.profit} />} />
            <Stat label={t("money.balance") + " · " + t("nav.cash")} value={<Money value={data.cash_balance} colored={false} />} />
            <Stat label={t("settlements.outstanding")} value={<Money value={data.open_debts} colored={false} />} color="var(--warning)" />
            <Stat label={t("payroll.fund")} value={<Money value={data.payroll_fund} colored={false} />} />
          </StatGrid>

          <Card header={t("reports.by_business")}>
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
                  <Legend />
                  <Bar dataKey="profit" name={t("money.profit")} radius={[4, 4, 0, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={CAT_COLORS[i % CAT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>

          <div
            style={{
              display: "grid",
              gap: 16,
              gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            }}
          >
            <Card header={`💰 ${t("dashboard.receivables")}`}>
              <DebtList
                rows={data.receivables}
                total={data.receivables_total}
                totalLabel={t("common.total")}
                empty={t("common.no_data")}
                tone="var(--money-in)"
              />
            </Card>
            <Card header={`📕 ${t("dashboard.payables")}`}>
              <DebtList
                rows={data.payables}
                total={data.payables_total}
                totalLabel={t("common.total")}
                empty={t("common.no_data")}
                tone="var(--money-out)"
              />
            </Card>
          </div>
        </>
      )}
    </>
  );
}

function DebtList({
  rows,
  total,
  totalLabel,
  empty,
  tone,
}: {
  rows: ExternalDebtRow[];
  total: string;
  totalLabel: string;
  empty: string;
  tone: string;
}) {
  if (rows.length === 0) return <div style={{ color: "var(--n-500)", padding: "8px 0" }}>{empty}</div>;
  return (
    <div>
      <ul style={{ listStyle: "none", margin: 0, padding: 0 }}>
        {rows.map((r) => (
          <li
            key={r.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: 12,
              padding: "9px 0",
              borderBottom: "1px solid var(--n-100)",
            }}
          >
            <span style={{ fontWeight: 600, color: "var(--n-800)" }}>
              {r.counterparty}
              {r.business_name && (
                <span style={{ color: "var(--n-500)", fontWeight: 400 }}> · {r.business_name}</span>
              )}
            </span>
            <span style={{ fontWeight: 700, color: tone, whiteSpace: "nowrap" }}>
              <Money value={r.outstanding} colored={false} />
            </span>
          </li>
        ))}
      </ul>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          paddingTop: 10,
          fontWeight: 700,
        }}
      >
        <span>{totalLabel}</span>
        <span style={{ color: tone }}>
          <Money value={total} colored={false} />
        </span>
      </div>
    </div>
  );
}

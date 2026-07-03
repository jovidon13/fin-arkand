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

import { useDashboard } from "@/entities/report";
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
        </>
      )}
    </>
  );
}

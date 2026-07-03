import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { PeriodParams } from "@/shared/api";

import type {
  CashReport,
  DashboardData,
  PayrollReport,
  PnlReport,
  SettlementsReport,
} from "../model/types";

export function useDashboard(period: PeriodParams = {}) {
  return useQuery({
    queryKey: ["report", "dashboard", period],
    queryFn: async () => {
      const { data } = await api.get<DashboardData>("/reports/dashboard", { params: period });
      return data;
    },
  });
}

export function usePnlReport(period: PeriodParams = {}) {
  return useQuery({
    queryKey: ["report", "pnl", period],
    queryFn: async () => {
      const { data } = await api.get<PnlReport>("/reports/pnl", { params: period });
      return data;
    },
  });
}

export function useCashReport(period: PeriodParams = {}) {
  return useQuery({
    queryKey: ["report", "cash", period],
    queryFn: async () => {
      const { data } = await api.get<CashReport>("/reports/cash", { params: period });
      return data;
    },
  });
}

export function useSettlementsReport(period: PeriodParams = {}) {
  return useQuery({
    queryKey: ["report", "settlements", period],
    queryFn: async () => {
      const { data } = await api.get<SettlementsReport>("/reports/settlements", {
        params: period,
      });
      return data;
    },
  });
}

export function usePayrollReport(params: { year?: number; month?: number } = {}) {
  return useQuery({
    queryKey: ["report", "payroll", params],
    queryFn: async () => {
      const { data } = await api.get<PayrollReport>("/reports/payroll", { params });
      return data;
    },
  });
}

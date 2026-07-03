import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type {
  Employee,
  EmployeeFilters,
  PayrollItem,
  PayrollRun,
  PayrollRunFilters,
  PayrollScheme,
  RunPayrollPayload,
} from "../model/types";

const RUNS_KEY = "payroll-runs";
const EMPLOYEES_KEY = "employees";
const SCHEMES_KEY = "payroll-schemes";
const ITEMS_KEY = "payroll-items";

export function useEmployees(filters: EmployeeFilters = {}) {
  return useQuery({
    queryKey: [EMPLOYEES_KEY, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Employee>>("/employees", {
        params: filters,
      });
      return data;
    },
  });
}

export function usePayrollSchemes() {
  return useQuery({
    queryKey: [SCHEMES_KEY],
    queryFn: async () => {
      const { data } = await api.get<Paginated<PayrollScheme>>("/payroll-schemes");
      return data;
    },
  });
}

export function usePayrollRuns(filters: PayrollRunFilters = {}) {
  return useQuery({
    queryKey: [RUNS_KEY, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<PayrollRun>>("/payroll-runs", {
        params: filters,
      });
      return data;
    },
  });
}

export function usePayrollItems(runId: number | null) {
  return useQuery({
    queryKey: [ITEMS_KEY, runId],
    enabled: runId !== null,
    queryFn: async () => {
      const { data } = await api.get<Paginated<PayrollItem>>(
        `/payroll-runs/${runId}/items`,
      );
      return data;
    },
  });
}

export function useRunPayroll() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: RunPayrollPayload) => {
      const { data } = await api.post<PayrollRun>("/payroll-runs", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [RUNS_KEY] });
      void qc.invalidateQueries({ queryKey: [ITEMS_KEY] });
    },
  });
}

function usePayrollRunAction(action: "approve" | "pay") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<PayrollRun>(`/payroll-runs/${id}/${action}`, {});
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [RUNS_KEY] });
      void qc.invalidateQueries({ queryKey: [ITEMS_KEY] });
    },
  });
}

export const useApprovePayroll = () => usePayrollRunAction("approve");
export const usePayPayroll = () => usePayrollRunAction("pay");

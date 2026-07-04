import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type {
  ProfitRow,
  Transaction,
  TransactionCreate,
  TransactionFilters,
} from "../model/types";

const KEY = "transactions";

export function useTransactions(filters: TransactionFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Transaction>>("/transactions", {
        params: filters,
      });
      return data;
    },
  });
}

export function useProfitByBusiness(params: { date_from?: string; date_to?: string } = {}) {
  return useQuery({
    queryKey: ["finance-profit", params],
    queryFn: async () => {
      const { data } = await api.get<ProfitRow[]>("/finance/profit", { params });
      return data;
    },
  });
}

export function useCreateTransaction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TransactionCreate) => {
      const { data } = await api.post<Transaction>("/transactions", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [KEY] });
      void qc.invalidateQueries({ queryKey: ["finance-profit"] });
    },
  });
}

function useTxAction(action: "check" | "confirm" | "reject" | "void") {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<Transaction>(`/transactions/${id}/${action}`, {});
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [KEY] });
      void qc.invalidateQueries({ queryKey: ["finance-profit"] });
    },
  });
}

export const useCheckTransaction = () => useTxAction("check");
export const useConfirmTransaction = () => useTxAction("confirm");
export const useRejectTransaction = () => useTxAction("reject");
export const useVoidTransaction = () => useTxAction("void");

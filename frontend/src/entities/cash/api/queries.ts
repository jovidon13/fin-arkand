import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type {
  CashOperation,
  CashOperationCreate,
  CashOperationFilters,
  CashRegister,
} from "../model/types";

const REGISTERS_KEY = "cash-registers";
const OPERATIONS_KEY = "cash-operations";

export function useCashRegisters() {
  return useQuery({
    queryKey: [REGISTERS_KEY],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CashRegister>>("/cash-registers", {
        params: { page_size: 200 },
      });
      return data.results;
    },
  });
}

export function useCashOperations(filters: CashOperationFilters = {}) {
  return useQuery({
    queryKey: [OPERATIONS_KEY, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<CashOperation>>("/cash-operations", {
        params: { ...filters, ordering: "-occurred_on" },
      });
      return data;
    },
  });
}

export function useCreateCashOperation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CashOperationCreate) => {
      const { data } = await api.post<CashOperation>("/cash-operations", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [OPERATIONS_KEY] });
      void qc.invalidateQueries({ queryKey: [REGISTERS_KEY] });
    },
  });
}

export function useSetCashLimit() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, limit }: { id: number; limit: string }) => {
      const { data } = await api.post<CashRegister>(`/cash-registers/${id}/set_limit`, {
        limit,
      });
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [REGISTERS_KEY] });
    },
  });
}

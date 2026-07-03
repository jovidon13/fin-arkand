import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type {
  Debt,
  DebtFilters,
  DebtRegistryParams,
  DebtRegistryRow,
  Settlement,
  SettlePayload,
  Transfer,
  TransferCreate,
  TransferFilters,
} from "../model/types";

const TRANSFERS = "transfers";
const DEBTS = "debts";
const REGISTRY = "debt-registry";

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  void qc.invalidateQueries({ queryKey: [TRANSFERS] });
  void qc.invalidateQueries({ queryKey: [DEBTS] });
  void qc.invalidateQueries({ queryKey: [REGISTRY] });
}

export function useTransfers(filters: TransferFilters = {}) {
  return useQuery({
    queryKey: [TRANSFERS, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Transfer>>("/transfers", {
        params: filters,
      });
      return data;
    },
  });
}

export function useCreateTransfer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TransferCreate) => {
      const { data } = await api.post<Transfer>("/transfers", payload);
      return data;
    },
    onSuccess: () => invalidateAll(qc),
  });
}

export function useApproveTransfer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<Debt>(`/transfers/${id}/approve`, {});
      return data;
    },
    onSuccess: () => invalidateAll(qc),
  });
}

export function useRejectTransfer() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<Transfer>(`/transfers/${id}/reject`, {});
      return data;
    },
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDebts(filters: DebtFilters = {}) {
  return useQuery({
    queryKey: [DEBTS, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Debt>>("/debts", {
        params: filters,
      });
      return data;
    },
  });
}

export function useSettleDebt() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: number; payload: SettlePayload }) => {
      const { data } = await api.post<Settlement>(`/debts/${id}/settle`, payload);
      return data;
    },
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDebtRegistry(params: DebtRegistryParams = {}) {
  return useQuery({
    queryKey: [REGISTRY, params],
    queryFn: async () => {
      const { data } = await api.get<DebtRegistryRow[]>("/debts/registry", {
        params,
      });
      return data;
    },
  });
}

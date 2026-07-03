import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type {
  ApprovalFilters,
  ApprovalRequest,
  CreateRequestPayload,
  VotePayload,
} from "../model/types";

const KEY = "approval-requests";

export function useApprovalRequests(filters: ApprovalFilters = {}) {
  return useQuery({
    queryKey: [KEY, filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<ApprovalRequest>>("/approval-requests", {
        params: filters,
      });
      return data;
    },
  });
}

export function usePendingApprovals(filters: ApprovalFilters = {}) {
  return useQuery({
    queryKey: [KEY, "pending", filters],
    queryFn: async () => {
      const { data } = await api.get<Paginated<ApprovalRequest> | ApprovalRequest[]>(
        "/approval-requests/pending",
        { params: filters },
      );
      return Array.isArray(data) ? data : data.results;
    },
  });
}

export function useCreateApprovalRequest() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateRequestPayload) => {
      const { data } = await api.post<ApprovalRequest>("/approval-requests", payload);
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [KEY] });
    },
  });
}

export function useCastVote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...payload }: VotePayload & { id: number }) => {
      const { data } = await api.post<ApprovalRequest>(
        `/approval-requests/${id}/vote`,
        payload,
      );
      return data;
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: [KEY] });
    },
  });
}

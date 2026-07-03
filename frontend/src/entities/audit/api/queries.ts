import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

export interface AuditLog {
  id: number;
  action: string;
  actor: number | null;
  actor_name: string | null;
  target_type: string | null;
  object_id: string | null;
  before: unknown;
  after: unknown;
  meta: unknown;
  created_at: string;
}

export function useAuditLogs(params: { action?: string; page?: number } = {}) {
  return useQuery({
    queryKey: ["audit-logs", params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AuditLog>>("/audit-logs", { params });
      return data;
    },
  });
}

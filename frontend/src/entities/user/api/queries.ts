import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

export interface AppUser {
  id: number;
  username: string;
  full_name: string;
  email: string;
  phone: string;
  role: number | null;
  role_code: string | null;
  role_name: string | null;
  business: number | null;
  business_name: string | null;
  is_active: boolean;
}

export interface Role {
  id: number;
  code: string;
  name: string;
}

export function useUsers(params: { role?: number; page?: number } = {}) {
  return useQuery({
    queryKey: ["users", params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<AppUser>>("/users", { params });
      return data;
    },
  });
}

export function useRoles() {
  return useQuery({
    queryKey: ["roles"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Role>>("/roles", { params: { page_size: 50 } });
      return data.results;
    },
    staleTime: 10 * 60 * 1000,
  });
}

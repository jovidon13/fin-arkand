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

export interface Owner {
  id: number;
  full_name: string;
  username: string;
}

/** Руководители (владельцы) — recipient picker for «выдача руководителю».
 * Readable by finance staff (unlike the admin-only full user list). */
export function useOwners() {
  return useQuery({
    queryKey: ["owners"],
    queryFn: async () => {
      const { data } = await api.get<Owner[]>("/owners");
      return data;
    },
    staleTime: 10 * 60 * 1000,
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

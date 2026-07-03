import { useQuery } from "@tanstack/react-query";

import { api } from "@/shared/api";
import type { Paginated } from "@/shared/api";

import type { Business, ExpenseCategory } from "../model/types";

export function useBusinesses() {
  return useQuery({
    queryKey: ["businesses"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<Business>>("/businesses", {
        params: { page_size: 200 },
      });
      return data.results;
    },
    staleTime: 5 * 60 * 1000,
  });
}

export function useExpenseCategories() {
  return useQuery({
    queryKey: ["expense-categories"],
    queryFn: async () => {
      const { data } = await api.get<Paginated<ExpenseCategory>>("/expense-categories", {
        params: { page_size: 200 },
      });
      return data.results;
    },
    staleTime: 5 * 60 * 1000,
  });
}

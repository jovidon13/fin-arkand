import { z } from "zod";

export const txKinds = ["income", "expense"] as const;
export const payMethods = ["cash", "transfer"] as const;
export const txStatuses = [
  "draft",
  "pending",
  "awaiting_owner",
  "confirmed",
  "rejected",
  "void",
] as const;

export const transactionSchema = z.object({
  id: z.number(),
  business: z.number(),
  business_name: z.string(),
  kind: z.enum(txKinds),
  kind_display: z.string(),
  category: z.number().nullable(),
  category_name: z.string().nullable().optional(),
  amount: z.string(),
  signed_amount: z.string(),
  method: z.enum(payMethods),
  method_display: z.string(),
  status: z.enum(txStatuses),
  status_display: z.string(),
  occurred_on: z.string(),
  site_object: z.number().nullable(),
  counterparty: z.string(),
  note: z.string(),
  is_barter: z.boolean(),
  source: z.string(),
  is_disbursement: z.boolean().optional(),
  recipient_manager: z.number().nullable().optional(),
  recipient_manager_name: z.string().nullable().optional(),
  requires_owner: z.boolean().optional(),
  created_by: z.number().nullable().optional(),
  created_by_name: z.string().nullable().optional(),
  checked_by: z.number().nullable().optional(),
  checked_by_name: z.string().nullable().optional(),
  checked_at: z.string().nullable().optional(),
  confirmed_by: z.number().nullable(),
  confirmed_by_name: z.string().nullable().optional(),
  confirmed_at: z.string().nullable(),
  created_at: z.string(),
});

export type Transaction = z.infer<typeof transactionSchema>;

export interface TransactionCreate {
  business: number;
  kind: (typeof txKinds)[number];
  category?: number | null;
  amount: string;
  method: (typeof payMethods)[number];
  occurred_on: string;
  counterparty?: string;
  note?: string;
  is_barter?: boolean;
  is_disbursement?: boolean;
  recipient_manager?: number | null;
}

export interface TransactionFilters {
  business?: number;
  kind?: string;
  status?: string;
  method?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface ProfitRow {
  business_id: number;
  business_name: string;
  income: string;
  expense: string;
  profit: string;
}

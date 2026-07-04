import { z } from "zod";

export const cashKinds = ["income", "expense"] as const;
export const cashMethods = ["cash", "transfer"] as const;

export const cashRegisterSchema = z.object({
  id: z.number(),
  business: z.number(),
  business_name: z.string().optional(),
  name: z.string(),
  code: z.string(),
  turnover_limit: z.string(),
  responsible: z.number().nullable().optional(),
  is_active: z.boolean(),
  balance: z.string(),
  created_at: z.string().optional(),
});

export type CashRegister = z.infer<typeof cashRegisterSchema>;

export const cashOperationSchema = z.object({
  id: z.number(),
  register: z.number(),
  register_name: z.string(),
  kind: z.enum(cashKinds),
  kind_display: z.string(),
  amount: z.string(),
  signed_amount: z.string(),
  method: z.enum(cashMethods),
  method_display: z.string(),
  occurred_on: z.string(),
  counterparty: z.string(),
  note: z.string(),
  created_by: z.number().nullable().optional(),
  created_by_name: z.string().nullable().optional(),
  documents_count: z.number().optional(),
  finance_transaction: z.number().nullable().optional(),
  created_at: z.string().optional(),
});

export type CashOperation = z.infer<typeof cashOperationSchema>;

export interface CashOperationCreate {
  register: number;
  kind: (typeof cashKinds)[number];
  amount: string;
  method: (typeof cashMethods)[number];
  occurred_on: string;
  counterparty?: string;
  note?: string;
}

export interface CashOperationFilters {
  register?: number;
  kind?: string;
  method?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
}

import { z } from "zod";

export const businessKinds = [
  "developer",
  "design",
  "concrete_plant",
  "crushing_plant",
  "supply",
  "finance",
] as const;

export const businessSchema = z.object({
  id: z.number(),
  code: z.string(),
  name: z.string(),
  kind: z.string(),
  kind_display: z.string().optional(),
  expense_limit: z.string(),
  is_active: z.boolean(),
});

export type Business = z.infer<typeof businessSchema>;

export const expenseCategorySchema = z.object({
  id: z.number(),
  code: z.string(),
  name: z.string(),
  is_active: z.boolean(),
});

export type ExpenseCategory = z.infer<typeof expenseCategorySchema>;

import type { PeriodParams } from "@/shared/api";

export const settlementKinds = ["netting", "repayment"] as const;
export type SettlementKind = (typeof settlementKinds)[number];

export interface Transfer {
  id: number;
  from_business: number;
  from_business_name?: string;
  to_business: number;
  to_business_name?: string;
  amount: string;
  description: string;
  occurred_on: string;
  is_barter: boolean;
  status: string;
  status_display: string;
}

export interface TransferCreate {
  from_business: number;
  to_business: number;
  amount: string;
  occurred_on: string;
  description?: string;
  is_barter?: boolean;
}

export interface Debt {
  id: number;
  debtor: number;
  debtor_name?: string;
  creditor: number;
  creditor_name?: string;
  amount: string;
  outstanding: string;
  status: string;
  status_display: string;
  is_barter: boolean;
}

export interface Settlement {
  id: number;
  debt: number;
  kind: SettlementKind;
  amount: string;
  occurred_on: string;
  note: string;
}

export interface SettlePayload {
  kind: SettlementKind;
  amount: string;
  occurred_on: string;
  counter_debt?: number | null;
  note?: string;
}

/** Row shape returned by GET /debts/registry (БАР-02 transparent register). */
export interface DebtRegistryRow {
  debt_id: number;
  debtor_id: number;
  debtor_name: string;
  creditor_id: number;
  creditor_name: string;
  outstanding: string;
  amount: string;
  is_barter: boolean;
  occurred_on: string;
  status: string;
}

export interface TransferFilters extends PeriodParams {
  from_business?: number;
  to_business?: number;
  status?: string;
  is_barter?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface DebtFilters extends PeriodParams {
  debtor?: number;
  creditor?: number;
  status?: string;
  is_barter?: boolean;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface DebtRegistryParams extends PeriodParams {
  include_settled?: boolean;
}

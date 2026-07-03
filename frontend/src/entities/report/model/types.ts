export interface BusinessProfitRow {
  business_id: number;
  business_name: string;
  income: string;
  expense: string;
  profit: string;
}

export interface DashboardData {
  income: string;
  expense: string;
  profit: string;
  cash_balance: string;
  open_debts: string;
  payroll_fund: string;
  by_business: BusinessProfitRow[];
}

export interface PnlReport {
  by_business: BusinessProfitRow[];
  consolidated: { income: string; expense: string; profit: string };
}

export interface CashRegisterRow {
  register_id: number;
  register_name: string;
  business_id: number;
  business_name: string;
  balance: string;
  turnover: string;
  limit: string;
}

export interface CashReport {
  registers: CashRegisterRow[];
  total_balance: string;
  total_turnover: string;
}

export interface DebtRow {
  debtor_id: number;
  debtor_name: string;
  creditor_id: number;
  creditor_name: string;
  outstanding: string;
  amount: string;
  status: string;
}

export interface SettlementsReport {
  registry: DebtRow[];
  total_outstanding: string;
}

export interface PayrollFundRow {
  business_id: number;
  business_name: string;
  fund: string;
}

export interface PayrollReport {
  fund: string;
  by_business: PayrollFundRow[];
  period: { year: number | null; month: number | null };
}

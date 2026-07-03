export const payrollStatuses = ["draft", "calculated", "approved", "paid"] as const;
export const salaryTypes = ["object", "admin"] as const;

export interface PayrollScheme {
  id: number;
  name: string;
  base_fixed: string;
  rules: Record<string, unknown>[];
  is_active: boolean;
}

export interface Employee {
  id: number;
  full_name: string;
  business: number;
  business_name?: string;
  position: string;
  salary_type: (typeof salaryTypes)[number];
  salary_type_display?: string;
  base_salary: string;
  is_salesperson: boolean;
  scheme: number | null;
  scheme_name?: string | null;
  is_active: boolean;
}

export interface PayrollRun {
  id: number;
  year: number;
  month: number;
  status: (typeof payrollStatuses)[number];
  status_display: string;
  total: string;
  items_count?: number;
}

export interface PayrollItem {
  id: number;
  run: number;
  employee: number;
  employee_name?: string;
  base_amount: string;
  bonus_amount: string;
  total_amount: string;
  details?: Record<string, unknown>;
  metrics?: Record<string, number>;
}

export interface RunPayrollPayload {
  year: number;
  month: number;
  metrics_by_employee?: Record<number, Record<string, number>>;
}

export interface EmployeeFilters {
  business?: number;
  salary_type?: string;
  is_salesperson?: boolean;
  is_active?: boolean;
  search?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface PayrollRunFilters {
  year?: number;
  month?: number;
  status?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

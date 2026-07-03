import { Route, Routes } from "react-router-dom";

import { AppLayout } from "@/app/layout/AppLayout";
import { ApprovalsPage } from "@/pages/approvals";
import { AuditPage } from "@/pages/audit";
import { CashPage } from "@/pages/cash";
import { DashboardPage } from "@/pages/dashboard";
import { FinancePage } from "@/pages/finance";
import { LoginPage } from "@/pages/login";
import { PayrollPage } from "@/pages/payroll";
import { ReportsPage } from "@/pages/reports";
import { SettlementsPage } from "@/pages/settlements";
import { UsersPage } from "@/pages/users";

import { ProtectedRoute } from "./ProtectedRoute";

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="finance" element={<FinancePage />} />
        <Route path="cash" element={<CashPage />} />
        <Route path="settlements" element={<SettlementsPage />} />
        <Route path="payroll" element={<PayrollPage />} />
        <Route path="approvals" element={<ApprovalsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="audit" element={<AuditPage />} />
        <Route path="users" element={<UsersPage />} />
      </Route>
    </Routes>
  );
}

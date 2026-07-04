import { lazy, Suspense, type ReactNode } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/app/layout/AppLayout";
import { useAuth } from "@/app/providers";
import { Loading } from "@/shared/ui";

import { ProtectedRoute } from "./ProtectedRoute";

// Code-split pages so the initial bundle stays small and heavy deps (charts on
// Dashboard/Reports) load only when their page is opened — faster first paint.
const DashboardPage = lazy(() =>
  import("@/pages/dashboard").then((m) => ({ default: m.DashboardPage })),
);
const FinancePage = lazy(() =>
  import("@/pages/finance").then((m) => ({ default: m.FinancePage })),
);
const CashPage = lazy(() => import("@/pages/cash").then((m) => ({ default: m.CashPage })));
const SettlementsPage = lazy(() =>
  import("@/pages/settlements").then((m) => ({ default: m.SettlementsPage })),
);
const PayrollPage = lazy(() =>
  import("@/pages/payroll").then((m) => ({ default: m.PayrollPage })),
);
const ApprovalsPage = lazy(() =>
  import("@/pages/approvals").then((m) => ({ default: m.ApprovalsPage })),
);
const ReportsPage = lazy(() =>
  import("@/pages/reports").then((m) => ({ default: m.ReportsPage })),
);
const AuditPage = lazy(() => import("@/pages/audit").then((m) => ({ default: m.AuditPage })));
const UsersPage = lazy(() => import("@/pages/users").then((m) => ({ default: m.UsersPage })));
const LoginPage = lazy(() => import("@/pages/login").then((m) => ({ default: m.LoginPage })));

/** Redirects users without finance-staff access (cashiers) to their cash page,
 * so they never land on a holding-wide screen that would 403. */
function FinanceStaffRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user && !user.is_finance_staff) return <Navigate to="/cash" replace />;
  return <>{children}</>;
}

/** Home: finance staff/owners see the holding dashboard; cashiers go to their cash. */
function HomeRoute() {
  const { user } = useAuth();
  if (user && !user.is_finance_staff) return <Navigate to="/cash" replace />;
  return <DashboardPage />;
}

const staff = (el: ReactNode) => <FinanceStaffRoute>{el}</FinanceStaffRoute>;

export function AppRouter() {
  return (
    <Suspense
      fallback={
        <div style={{ display: "grid", placeItems: "center", height: "100vh" }}>
          <Loading />
        </div>
      }
    >
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
          <Route index element={<HomeRoute />} />
          <Route path="finance" element={staff(<FinancePage />)} />
          <Route path="cash" element={<CashPage />} />
          <Route path="settlements" element={staff(<SettlementsPage />)} />
          <Route path="payroll" element={staff(<PayrollPage />)} />
          <Route path="approvals" element={staff(<ApprovalsPage />)} />
          <Route path="reports" element={staff(<ReportsPage />)} />
          <Route path="audit" element={staff(<AuditPage />)} />
          <Route path="users" element={<UsersPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}

import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/app/providers";
import { Loading } from "@/shared/ui";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: "grid", placeItems: "center", height: "100vh" }}>
        <Loading />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

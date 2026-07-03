import { Outlet } from "react-router-dom";

import { Sidebar } from "@/widgets/sidebar";
import { Topbar } from "@/widgets/topbar";

import "./layout.css";

export function AppLayout() {
  return (
    <div className="ak-shell">
      <Sidebar />
      <div className="ak-shell__main">
        <Topbar />
        <main className="ak-shell__content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

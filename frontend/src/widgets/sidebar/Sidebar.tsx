import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { cn } from "@/shared/lib";

import "./sidebar.css";

interface NavItem {
  to: string;
  labelKey: string;
  icon: string;
  ownerOrStaff?: boolean;
  adminOnly?: boolean;
}

const NAV: NavItem[] = [
  { to: "/", labelKey: "nav.dashboard", icon: "◧" },
  { to: "/finance", labelKey: "nav.finance", icon: "₴" },
  { to: "/cash", labelKey: "nav.cash", icon: "▤" },
  { to: "/settlements", labelKey: "nav.settlements", icon: "⇄" },
  { to: "/payroll", labelKey: "nav.payroll", icon: "☰" },
  { to: "/approvals", labelKey: "nav.approvals", icon: "✓" },
  { to: "/reports", labelKey: "nav.reports", icon: "▦" },
  { to: "/audit", labelKey: "nav.audit", icon: "❋" },
  { to: "/users", labelKey: "nav.users", icon: "◯", adminOnly: true },
];

export function Sidebar() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser || user?.role_code === "admin";

  const items = NAV.filter((n) => (n.adminOnly ? isAdmin : true));

  return (
    <aside className="ak-sidebar">
      <div className="ak-sidebar__brand">
        <span className="ak-sidebar__mark">ARKAND</span>
        <span className="ak-sidebar__sub">{t("app.holding")}</span>
      </div>
      <nav className="ak-sidebar__nav">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) => cn("ak-nav-item", isActive && "ak-nav-item--active")}
          >
            <span className="ak-nav-item__icon">{item.icon}</span>
            {t(item.labelKey)}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

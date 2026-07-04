import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { cn } from "@/shared/lib";

import "./sidebar.css";

interface NavItem {
  to: string;
  labelKey: string;
  icon: string;
  /** Requires finance back-office / owner access (hidden from cashiers). */
  financeStaff?: boolean;
  adminOnly?: boolean;
}

const NAV: NavItem[] = [
  { to: "/", labelKey: "nav.dashboard", icon: "◧", financeStaff: true },
  { to: "/finance", labelKey: "nav.finance", icon: "₴", financeStaff: true },
  { to: "/cash", labelKey: "nav.cash", icon: "▤" },
  { to: "/settlements", labelKey: "nav.settlements", icon: "⇄", financeStaff: true },
  { to: "/payroll", labelKey: "nav.payroll", icon: "☰", financeStaff: true },
  { to: "/approvals", labelKey: "nav.approvals", icon: "✓", financeStaff: true },
  { to: "/reports", labelKey: "nav.reports", icon: "▦", financeStaff: true },
  { to: "/audit", labelKey: "nav.audit", icon: "❋", financeStaff: true },
  { to: "/users", labelKey: "nav.users", icon: "◯", adminOnly: true },
];

export function Sidebar() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const isAdmin = user?.is_superuser || user?.role_code === "admin";
  const isFinanceStaff = user?.is_finance_staff ?? false;

  // Кассир видит только «Кассы»; финперсонал/владельцы — все разделы;
  // управление пользователями — только админ.
  const items = NAV.filter((n) => {
    if (n.adminOnly) return isAdmin;
    if (n.financeStaff) return isFinanceStaff;
    return true;
  });

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

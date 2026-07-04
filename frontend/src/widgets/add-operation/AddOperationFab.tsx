import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { AddTransactionModal, type OperationKind } from "@/features/finance";
import { CreateTransferModal } from "@/features/settlement";

import "./add-operation.css";

type MenuAction = OperationKind | "transfer";

const ACTIONS: { key: MenuAction; icon: string; labelKey: string; tone: string }[] = [
  { key: "income", icon: "➕", labelKey: "money.income", tone: "var(--money-in)" },
  { key: "expense", icon: "➖", labelKey: "money.expense", tone: "var(--money-out)" },
  { key: "transfer", icon: "🔄", labelKey: "money.transfer", tone: "var(--info)" },
  { key: "disbursement", icon: "💵", labelKey: "finance.disbursement", tone: "var(--warning)" },
];

/** Always-visible «Добавить операцию» — Доход / Расход / Перевод / Выдача. */
export function AddOperationFab() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [active, setActive] = useState<MenuAction | null>(null);

  // Finance operations are written by finance managers (accountant/chief/admin).
  if (!user?.can_manage_finance) return null;

  const pick = (key: MenuAction) => {
    setActive(key);
    setMenuOpen(false);
  };

  return (
    <>
      <div className="ak-fab">
        {menuOpen && (
          <div className="ak-fab__menu" role="menu">
            {ACTIONS.map((a) => (
              <button
                key={a.key}
                type="button"
                className="ak-fab__item"
                onClick={() => pick(a.key)}
              >
                <span className="ak-fab__ico" style={{ color: a.tone }}>
                  {a.icon}
                </span>
                {t(a.labelKey)}
              </button>
            ))}
          </div>
        )}
        <button
          type="button"
          className="ak-fab__toggle"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((o) => !o)}
        >
          <span className={`ak-fab__plus ${menuOpen ? "is-open" : ""}`}>+</span>
          <span className="ak-fab__label">{t("finance.add_operation")}</span>
        </button>
      </div>

      <AddTransactionModal
        open={active === "income" || active === "expense" || active === "disbursement"}
        kind={(active === "transfer" ? "income" : (active ?? "income")) as OperationKind}
        onClose={() => setActive(null)}
      />
      <CreateTransferModal open={active === "transfer"} onClose={() => setActive(null)} />
    </>
  );
}

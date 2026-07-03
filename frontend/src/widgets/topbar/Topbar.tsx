import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { LANGS, setLanguage, type LangCode } from "@/shared/i18n";
import { Button } from "@/shared/ui";

import "./topbar.css";

export function Topbar() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  // Full ARKAND lockup on the light header. Drop a raster at /public/logo.png
  // to override; falls back to a monogram if neither asset loads.
  const [logoOk, setLogoOk] = useState(true);

  return (
    <header className="ak-topbar">
      <div className="ak-topbar__brand">
        {logoOk ? (
          <img
            src="/logo.svg"
            alt="ARKAND"
            className="ak-topbar__logo"
            onError={() => setLogoOk(false)}
          />
        ) : (
          <span className="ak-topbar__monogram" aria-hidden="true">
            A
          </span>
        )}
        <span className="ak-topbar__divider" />
        <span className="ak-topbar__module">{t("nav.finance")}</span>
      </div>

      <div className="ak-topbar__spacer" />

      <div className="ak-topbar__right">
        <div className="ak-lang">
          {LANGS.map((l) => (
            <button
              key={l.code}
              className={i18n.language === l.code ? "ak-lang__btn ak-lang__btn--on" : "ak-lang__btn"}
              onClick={() => setLanguage(l.code as LangCode)}
            >
              {l.code.toUpperCase()}
            </button>
          ))}
        </div>
        <div className="ak-topbar__user">
          <div className="ak-topbar__name">{user?.full_name || user?.username}</div>
          <div className="ak-topbar__role">{user?.role_name ?? "—"}</div>
        </div>
        <Button variant="ghost" size="sm" onClick={logout}>
          {t("common.logout")}
        </Button>
      </div>
    </header>
  );
}

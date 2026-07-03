import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "@/app/providers";
import { LANGS, setLanguage, type LangCode } from "@/shared/i18n";
import { Button } from "@/shared/ui";

import "./topbar.css";

export function Topbar() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  // Prefer the official PNG (drop yours in /public/logo.png), fall back to the
  // bundled crimson SVG emblem, then to a text monogram.
  const [logoStage, setLogoStage] = useState<0 | 1 | 2>(0);
  const logoSrc = logoStage === 0 ? "/logo.png" : "/logo.svg";

  return (
    <header className="ak-topbar">
      <div className="ak-topbar__brand">
        {logoStage < 2 ? (
          <img
            src={logoSrc}
            alt="ARKAND"
            className="ak-topbar__logo"
            onError={() => setLogoStage((s) => (s + 1) as 0 | 1 | 2)}
          />
        ) : (
          <span className="ak-topbar__monogram" aria-hidden="true">
            A
          </span>
        )}
        <span className="ak-topbar__divider" />
        <div className="ak-topbar__title">
          <span className="ak-topbar__title-main">ARKAND</span>
          <span className="ak-topbar__title-sub">{t("nav.finance")}</span>
        </div>
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

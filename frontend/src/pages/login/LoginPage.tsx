import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/app/providers";
import type { ApiError } from "@/shared/api";
import { Button, Field, Input } from "@/shared/ui";

import "./login.css";

const DEMO_PASSWORD = "arkand2026";
// One account per distinct access level (no duplicates of the same role).
const DEMO_ACCOUNTS = [
  { roleKey: "auth.role_owner", username: "sohib" },
  { roleKey: "auth.role_chief", username: "chief" },
  { roleKey: "auth.role_accountant", username: "buh1" },
  { roleKey: "auth.role_cashier", username: "cashier_dev" },
  { roleKey: "auth.role_admin", username: "admin" },
] as const;

export function LoginPage() {
  const { t } = useTranslation();
  const { user, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [logoStage, setLogoStage] = useState<0 | 1 | 2>(0);
  const logoSrc = logoStage === 0 ? "/logo.png" : "/logo.svg";

  if (user) return <Navigate to="/" replace />;

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(username.trim(), password);
    } catch (err) {
      setError((err as ApiError).message || t("auth.error"));
    } finally {
      setLoading(false);
    }
  };

  const fillDemo = (login: string) => {
    setUsername(login);
    setPassword(DEMO_PASSWORD);
    setError(null);
  };

  return (
    <div className="ak-login">
      <form className="ak-login__card" onSubmit={submit}>
        <div className="ak-login__head">
          {logoStage < 2 ? (
            <img
              src={logoSrc}
              alt="ARKAND"
              className="ak-login__logo"
              onError={() => setLogoStage((s) => (s + 1) as 0 | 1 | 2)}
            />
          ) : (
            <span className="ak-login__brand">ARKAND</span>
          )}
          <div className="ak-login__sub">{t("app.holding")}</div>
        </div>

        <h2 className="ak-login__title">{t("auth.login")}</h2>

        <Field label={t("auth.username")}>
          <Input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoFocus
            autoComplete="username"
          />
        </Field>
        <Field label={t("auth.password")} error={error ?? undefined}>
          <Input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </Field>

        <Button type="submit" loading={loading} className="ak-login__submit">
          {t("auth.sign_in")}
        </Button>

        <div className="ak-login__demo">
          <div className="ak-login__demo-title">{t("auth.demo_title")}</div>
          <div className="ak-login__demo-hint">{t("auth.demo_hint")}</div>
          <div className="ak-login__demo-grid">
            {DEMO_ACCOUNTS.map((a) => (
              <button
                type="button"
                key={a.username}
                className="ak-login__demo-chip"
                onClick={() => fillDemo(a.username)}
              >
                <span className="ak-login__demo-role">{t(a.roleKey)}</span>
                <span className="ak-login__demo-login">{a.username}</span>
              </button>
            ))}
          </div>
          <div className="ak-login__demo-pass">
            {t("auth.demo_password")}: <code>{DEMO_PASSWORD}</code>
          </div>
        </div>
      </form>
    </div>
  );
}

import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate } from "react-router-dom";

import { useAuth } from "@/app/providers";
import type { ApiError } from "@/shared/api";
import { Button, Field, Input } from "@/shared/ui";

import "./login.css";

export function LoginPage() {
  const { t } = useTranslation();
  const { user, login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="ak-login">
      <form className="ak-login__card" onSubmit={submit}>
        <div className="ak-login__brand">ARKAND</div>
        <div className="ak-login__sub">{t("app.holding")}</div>
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
      </form>
    </div>
  );
}

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { api, tokenStore, toApiError } from "@/shared/api";

export interface CurrentUser {
  id: number;
  username: string;
  full_name: string;
  role_code: string | null;
  role_name: string | null;
  business: number | null;
  business_name: string | null;
  is_finance_staff: boolean;
  can_manage_finance: boolean;
  is_owner: boolean;
  is_superuser: boolean;
}

interface AuthCtx {
  user: CurrentUser | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadMe = useCallback(async () => {
    try {
      const { data } = await api.get<CurrentUser>("/auth/me");
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    // Try to restore a session from the persisted refresh token.
    (async () => {
      if (tokenStore.getRefresh()) {
        await loadMe();
      }
      setLoading(false);
    })();

    const onLogout = () => setUser(null);
    window.addEventListener("arkand:logout", onLogout);
    return () => window.removeEventListener("arkand:logout", onLogout);
  }, [loadMe]);

  const login = useCallback(
    async (username: string, password: string) => {
      try {
        const { data } = await api.post("/auth/token", { username, password });
        tokenStore.setAccess(data.access);
        tokenStore.setRefresh(data.refresh);
        setUser(data.user as CurrentUser);
      } catch (e) {
        throw toApiError(e);
      }
    },
    [],
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  return (
    <Ctx.Provider value={{ user, loading, login, logout }}>{children}</Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

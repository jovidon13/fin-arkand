import { createContext, type ReactNode, useCallback, useContext, useState } from "react";

import { cn } from "@/shared/lib";

type ToastTone = "default" | "success" | "error";
interface Toast {
  id: number;
  message: string;
  tone: ToastTone;
}

interface ToastCtx {
  push: (message: string, tone?: ToastTone) => void;
}

const Ctx = createContext<ToastCtx | null>(null);

let seq = 0;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((message: string, tone: ToastTone = "default") => {
    const id = ++seq;
    setToasts((t) => [...t, { id, message, tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4000);
  }, []);

  return (
    <Ctx.Provider value={{ push }}>
      {children}
      <div className="ak-toast-host">
        {toasts.map((t) => (
          <div key={t.id} className={cn("ak-toast", t.tone !== "default" && `ak-toast--${t.tone}`)}>
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  );
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "@/shared/lib";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "success";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: "md" | "sm";
  loading?: boolean;
  children: ReactNode;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn("ak-btn", `ak-btn--${variant}`, size === "sm" && "ak-btn--sm", className)}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className="ak-spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />}
      {children}
    </button>
  );
}

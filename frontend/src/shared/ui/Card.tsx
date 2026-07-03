import type { ReactNode } from "react";

import { cn } from "@/shared/lib";

export function Card({
  children,
  header,
  className,
  bodyClassName,
}: {
  children: ReactNode;
  header?: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <div className={cn("ak-card", className)}>
      {header && <div className="ak-card__header">{header}</div>}
      <div className={cn("ak-card__body", bodyClassName)}>{children}</div>
    </div>
  );
}

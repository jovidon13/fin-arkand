import type { ReactNode } from "react";
import { useEffect } from "react";

export function Modal({
  open,
  title,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="ak-modal__overlay" onClick={onClose}>
      <div className="ak-modal" onClick={(e) => e.stopPropagation()}>
        <div className="ak-modal__header">
          <span>{title}</span>
          <button className="ak-btn ak-btn--ghost ak-btn--sm" onClick={onClose} aria-label="Закрыть">
            ✕
          </button>
        </div>
        <div className="ak-modal__body">{children}</div>
        {footer && <div className="ak-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}

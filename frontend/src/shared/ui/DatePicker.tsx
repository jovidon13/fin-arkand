import { useEffect, useMemo, useRef, useState } from "react";

import { cn, formatDate, MONTHS_RU } from "@/shared/lib";

type ChangeLike = { target: { value: string } };

interface DatePickerProps {
  value?: string; // ISO YYYY-MM-DD
  onChange?: (e: ChangeLike) => void;
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  name?: string;
  className?: string;
}

const WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

/** Local YYYY-MM-DD (avoids the UTC shift of Date.toISOString in +TZ). */
function isoLocal(y: number, m: number, d: number): string {
  return `${y}-${String(m + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
}

/** Parse "YYYY-MM-DD" into local Y/M/D parts (no timezone math). */
function parseIso(value?: string): { y: number; m: number; d: number } | null {
  if (!value) return null;
  const [y, m, d] = value.split("-").map(Number);
  if (!y || !m || !d) return null;
  return { y, m: m - 1, d };
}

/**
 * CustomDatePicker — вишнёвый календарь без нативного OS-контрола.
 * Русские дни недели (Пн…Вс), навигация по месяцам, выбранный день — заливка
 * бренда кружком, «Сегодня»/«Очистить» в подвале.
 */
export function DatePicker({
  value,
  onChange,
  placeholder = "дд.мм.гггг",
  disabled = false,
  id,
  name,
  className,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const selected = useMemo(() => parseIso(value), [value]);
  const now = new Date();
  const [view, setView] = useState(() => ({
    y: selected?.y ?? now.getFullYear(),
    m: selected?.m ?? now.getMonth(),
  }));

  // Re-centre on the selected month whenever the panel is opened.
  useEffect(() => {
    if (open && selected) setView({ y: selected.y, m: selected.m });
  }, [open, selected]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    const onEsc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const cells = useMemo(() => buildMonth(view.y, view.m), [view]);
  const todayIso = isoLocal(now.getFullYear(), now.getMonth(), now.getDate());

  const emit = (iso: string) => {
    onChange?.({ target: { value: iso } });
    setOpen(false);
  };

  const shift = (delta: number) => {
    const d = new Date(view.y, view.m + delta, 1);
    setView({ y: d.getFullYear(), m: d.getMonth() });
  };

  return (
    <div ref={rootRef} className={cn("ak-dp", open && "ak-dp--open", className)}>
      <button
        type="button"
        id={id}
        name={name}
        disabled={disabled}
        className="ak-dp__trigger"
        onClick={() => !disabled && setOpen((o) => !o)}
      >
        <CalendarIcon />
        <span className={cn("ak-dp__value", !value && "ak-dp__value--placeholder")}>
          {value ? formatDate(value) : placeholder}
        </span>
      </button>

      {open && (
        <div className="ak-dp__panel">
          <div className="ak-dp__nav">
            <button type="button" className="ak-dp__navbtn" onClick={() => shift(-1)} aria-label="Предыдущий месяц">
              ‹
            </button>
            <span className="ak-dp__title">
              {MONTHS_RU[view.m]} {view.y}
            </span>
            <button type="button" className="ak-dp__navbtn" onClick={() => shift(1)} aria-label="Следующий месяц">
              ›
            </button>
          </div>

          <div className="ak-dp__grid">
            {WEEKDAYS_RU.map((w) => (
              <div key={w} className="ak-dp__wd">
                {w}
              </div>
            ))}
            {cells.map((c) => {
              const iso = isoLocal(c.y, c.m, c.d);
              return (
                <button
                  type="button"
                  key={iso + (c.muted ? "-x" : "")}
                  className={cn(
                    "ak-dp__day",
                    c.muted && "ak-dp__day--muted",
                    iso === todayIso && "ak-dp__day--today",
                    value === iso && "ak-dp__day--selected",
                  )}
                  onClick={() => emit(iso)}
                >
                  {c.d}
                </button>
              );
            })}
          </div>

          <div className="ak-dp__footer">
            <button type="button" className="ak-dp__link" onClick={() => emit(todayIso)}>
              Сегодня
            </button>
            <button type="button" className="ak-dp__link" onClick={() => emit("")}>
              Очистить
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

interface Cell {
  y: number;
  m: number;
  d: number;
  muted: boolean;
}

/** 42-cell (6-week) grid, Monday-first, with leading/trailing muted days. */
function buildMonth(y: number, m: number): Cell[] {
  const first = new Date(y, m, 1);
  const offset = (first.getDay() + 6) % 7; // 0 = Monday
  const start = new Date(y, m, 1 - offset);
  const cells: Cell[] = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    cells.push({ y: d.getFullYear(), m: d.getMonth(), d: d.getDate(), muted: d.getMonth() !== m });
  }
  return cells;
}

function CalendarIcon() {
  return (
    <svg
      className="ak-dp__icon"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" />
      <path d="M16 2v4M8 2v4M3 10h18" />
    </svg>
  );
}

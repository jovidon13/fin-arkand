import { type CSSProperties, useEffect, useMemo, useRef, useState } from "react";

import { cn } from "@/shared/lib";

export interface SelectOption {
  value: string | number;
  label: string;
}

/** Synthetic change payload — mirrors a native `<select>` so call sites that
 *  read `e.target.value` keep working unchanged. */
type ChangeLike = { target: { value: string } };

interface SelectProps {
  options: SelectOption[];
  value?: string | number;
  onChange?: (e: ChangeLike) => void;
  placeholder?: string;
  disabled?: boolean;
  id?: string;
  name?: string;
  className?: string;
  style?: CSSProperties;
}

/**
 * CustomSelect — вишнёвый дропдаун без нативных OS-стилей.
 * Скруглённый список, выбранный пункт залит брендом, hover — мягкая красная
 * подложка, длинный текст обрезается в одну строку (ellipsis).
 */
export function Select({
  options,
  value,
  onChange,
  placeholder = "—",
  disabled = false,
  id,
  name,
  className,
  style,
}: SelectProps) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);

  const selectedIndex = useMemo(
    () => options.findIndex((o) => String(o.value) === String(value ?? "")),
    [options, value],
  );
  const selected = selectedIndex >= 0 ? options[selectedIndex] : undefined;

  // Close on outside click / Escape.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  const openMenu = () => {
    if (disabled) return;
    setActive(selectedIndex);
    setOpen(true);
  };

  const choose = (opt: SelectOption) => {
    onChange?.({ target: { value: String(opt.value) } });
    setOpen(false);
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (disabled) return;
    if (!open && (e.key === "Enter" || e.key === " " || e.key === "ArrowDown")) {
      e.preventDefault();
      openMenu();
      return;
    }
    if (!open) return;
    if (e.key === "Escape") {
      setOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(options.length - 1, i + 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter" && active >= 0) {
      e.preventDefault();
      choose(options[active]);
    }
  };

  return (
    <div
      ref={rootRef}
      className={cn("ak-cselect", open && "ak-cselect--open", className)}
      style={style}
    >
      <button
        type="button"
        id={id}
        name={name}
        disabled={disabled}
        className="ak-cselect__trigger"
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => (open ? setOpen(false) : openMenu())}
        onKeyDown={onKeyDown}
      >
        <span
          className={cn("ak-cselect__value", !selected && "ak-cselect__value--placeholder")}
        >
          {selected ? selected.label : placeholder}
        </span>
        <ChevronIcon />
      </button>

      {open && (
        <ul className="ak-cselect__menu" role="listbox">
          {options.length === 0 && <li className="ak-cselect__empty">Нет вариантов</li>}
          {options.map((o, i) => (
            <li
              key={o.value}
              role="option"
              aria-selected={i === selectedIndex}
              className={cn(
                "ak-cselect__option",
                i === selectedIndex && "ak-cselect__option--selected",
                i === active && "ak-cselect__option--active",
              )}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => choose(o)}
            >
              {o.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function ChevronIcon() {
  return (
    <svg
      className="ak-cselect__chevron"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

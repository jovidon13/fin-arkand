import type {
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import { cn } from "@/shared/lib";

export function Field({
  label,
  error,
  children,
}: {
  label?: string;
  error?: string;
  children: ReactNode;
}) {
  return (
    <div className="ak-field">
      {label && <label className="ak-field__label">{label}</label>}
      {children}
      {error && <span className="ak-field__error">{error}</span>}
    </div>
  );
}

export function Input({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn("ak-input", className)} {...rest} />;
}

export function Textarea({ className, ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("ak-textarea", className)} {...rest} />;
}

interface Option {
  value: string | number;
  label: string;
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: Option[];
  placeholder?: string;
}

export function Select({ options, placeholder, className, ...rest }: SelectProps) {
  return (
    <select className={cn("ak-select", className)} {...rest}>
      {placeholder && <option value="">{placeholder}</option>}
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

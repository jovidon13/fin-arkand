import type { InputHTMLAttributes, ReactNode, TextareaHTMLAttributes } from "react";

import { cn } from "@/shared/lib";

import { DatePicker } from "./DatePicker";

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

/** Two-column form grid (`.form-row`, 1fr 1fr, 1rem gap) — collapses on mobile. */
export function FormRow({ children }: { children: ReactNode }) {
  return <div className="form-row">{children}</div>;
}

export function Input({ className, type, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  // Native <input type="date"> shows OS-styled controls — delegate to the
  // custom calendar picker while preserving the value/onChange call signature.
  if (type === "date") {
    return (
      <DatePicker
        className={className}
        value={rest.value as string | undefined}
        onChange={rest.onChange as unknown as (e: { target: { value: string } }) => void}
        id={rest.id}
        name={rest.name}
        disabled={rest.disabled}
        placeholder={rest.placeholder as string | undefined}
      />
    );
  }
  return <input className={cn("ak-input", className)} type={type} {...rest} />;
}

export function Textarea({ className, ...rest }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("ak-textarea", className)} {...rest} />;
}

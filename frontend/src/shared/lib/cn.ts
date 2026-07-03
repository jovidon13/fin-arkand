import clsx, { type ClassValue } from "clsx";

/** Conditional className helper. */
export function cn(...args: ClassValue[]): string {
  return clsx(...args);
}

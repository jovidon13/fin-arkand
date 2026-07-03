/** Shared API types & the unified error contract { code, message, details }. */

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export type Id = number;

/** Period query params used across reports/lists. */
export interface PeriodParams {
  date_from?: string;
  date_to?: string;
}

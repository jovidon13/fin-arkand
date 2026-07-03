import type { ReactNode } from "react";

import { cn } from "@/shared/lib";

export interface Column<T> {
  key: string;
  header: ReactNode;
  render: (row: T) => ReactNode;
  numeric?: boolean;
  width?: number | string;
}

interface TableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  empty?: ReactNode;
  onRowClick?: (row: T) => void;
}

export function Table<T>({ columns, rows, rowKey, empty, onRowClick }: TableProps<T>) {
  return (
    <div className="ak-table-wrap">
      <table className="ak-table">
        <thead>
          <tr>
            {columns.map((c) => (
              <th
                key={c.key}
                className={cn(c.numeric && "ak-table__num")}
                style={{ width: c.width }}
              >
                {c.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 && (
            <tr>
              <td colSpan={columns.length}>
                <div className="ak-empty">{empty ?? "Нет данных"}</div>
              </td>
            </tr>
          )}
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              style={onRowClick ? { cursor: "pointer" } : undefined}
            >
              {columns.map((c) => (
                <td key={c.key} className={cn(c.numeric && "ak-table__num")}>
                  {c.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

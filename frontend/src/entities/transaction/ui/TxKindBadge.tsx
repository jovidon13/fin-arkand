import { Badge } from "@/shared/ui";

export function TxKindBadge({ kind, label }: { kind: string; label?: string }) {
  return <Badge tone={kind === "income" ? "success" : "error"}>{label ?? kind}</Badge>;
}

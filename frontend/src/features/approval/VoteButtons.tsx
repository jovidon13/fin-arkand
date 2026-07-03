import { useTranslation } from "react-i18next";

import { useCastVote, type VoteValueKind } from "@/entities/approval";
import { toApiError } from "@/shared/api";
import { Button, useToast } from "@/shared/ui";

/**
 * Approve / Reject actions for one pending request (ХОЛ-22/23). Needs a "Добро"
 * from all three owners; a single "Нет" blocks the request.
 */
export function VoteButtons({ requestId }: { requestId: number }) {
  const { t } = useTranslation();
  const toast = useToast();
  const vote = useCastVote();

  const cast = async (value: VoteValueKind) => {
    try {
      await vote.mutateAsync({ id: requestId, value });
      toast.push(t("approvals.voted"), "success");
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  return (
    <div style={{ display: "flex", gap: 6 }}>
      <Button
        size="sm"
        variant="success"
        loading={vote.isPending}
        onClick={() => cast("approve")}
      >
        {t("common.approve")}
      </Button>
      <Button
        size="sm"
        variant="ghost"
        loading={vote.isPending}
        onClick={() => cast("reject")}
      >
        {t("common.reject")}
      </Button>
    </div>
  );
}

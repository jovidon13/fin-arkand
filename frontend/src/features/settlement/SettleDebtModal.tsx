import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import {
  useDebts,
  useSettleDebt,
  type SettlementKind,
  type SettlePayload,
} from "@/entities/settlement";
import { toApiError } from "@/shared/api";
import { formatMoney, toISODate } from "@/shared/lib";
import { Button, Field, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

export function SettleDebtModal({
  open,
  debtId,
  outstanding,
  onClose,
}: {
  open: boolean;
  debtId: number | null;
  outstanding: string;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const settle = useSettleDebt();
  const debts = useDebts({ ordering: "-occurred_on" });

  const [form, setForm] = useState<SettlePayload>({
    kind: "repayment",
    amount: outstanding,
    occurred_on: toISODate(new Date()),
    counter_debt: null,
    note: "",
  });
  const set = (patch: Partial<SettlePayload>) => setForm((f) => ({ ...f, ...patch }));

  useEffect(() => {
    if (open) {
      setForm({
        kind: "repayment",
        amount: outstanding,
        occurred_on: toISODate(new Date()),
        counter_debt: null,
        note: "",
      });
    }
  }, [open, debtId, outstanding]);

  const counterOptions = (debts.data?.results ?? [])
    .filter((d) => d.id !== debtId && d.status !== "settled")
    .map((d) => ({
      value: d.id,
      label: `${d.debtor_name ?? d.debtor} → ${d.creditor_name ?? d.creditor} · ${formatMoney(
        d.outstanding,
      )}`,
    }));

  const submit = async () => {
    if (debtId === null || !form.amount) {
      toast.push(t("settlements.msg_fill"), "error");
      return;
    }
    const payload: SettlePayload = {
      kind: form.kind,
      amount: form.amount,
      occurred_on: form.occurred_on,
      note: form.note,
      counter_debt: form.kind === "netting" ? form.counter_debt : null,
    };
    try {
      await settle.mutateAsync({ id: debtId, payload });
      toast.push(t("settlements.msg_debt_settled"), "success");
      onClose();
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  return (
    <Modal
      open={open}
      title={t("settlements.close_debt")}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={submit} loading={settle.isPending}>
            {t("common.confirm")}
          </Button>
        </>
      }
    >
      <Field label={t("settlements.kind")}>
        <Select
          value={form.kind}
          onChange={(e) => set({ kind: e.target.value as SettlementKind })}
          options={[
            { value: "repayment", label: t("settlements.repayment") },
            { value: "netting", label: t("settlements.netting") },
          ]}
        />
      </Field>
      <Field label={t("common.amount")}>
        <Input
          type="number"
          min="0"
          step="0.01"
          value={form.amount}
          onChange={(e) => set({ amount: e.target.value })}
        />
      </Field>
      <Field label={t("common.date")}>
        <Input
          type="date"
          value={form.occurred_on}
          onChange={(e) => set({ occurred_on: e.target.value })}
        />
      </Field>
      {form.kind === "netting" && (
        <Field label={t("settlements.counter_debt")}>
          <Select
            value={form.counter_debt ?? ""}
            placeholder="—"
            onChange={(e) =>
              set({ counter_debt: e.target.value ? Number(e.target.value) : null })
            }
            options={counterOptions}
          />
        </Field>
      )}
      <Field label={t("common.note")}>
        <Textarea
          value={form.note ?? ""}
          onChange={(e) => set({ note: e.target.value })}
        />
      </Field>
    </Modal>
  );
}

import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  useCashRegisters,
  useCreateCashOperation,
  type CashOperationCreate,
} from "@/entities/cash";
import { toApiError } from "@/shared/api";
import { toISODate } from "@/shared/lib";
import { Button, Field, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

export function AddCashOperationModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const registers = useCashRegisters();
  const create = useCreateCashOperation();

  const [form, setForm] = useState<CashOperationCreate>({
    register: 0,
    kind: "income",
    amount: "",
    method: "cash",
    occurred_on: toISODate(new Date()),
    counterparty: "",
    note: "",
  });

  const set = (patch: Partial<CashOperationCreate>) =>
    setForm((f) => ({ ...f, ...patch }));

  const submit = async () => {
    if (!form.register || !form.amount) {
      toast.push(t("cash.fill_register_amount"), "error");
      return;
    }
    try {
      await create.mutateAsync(form);
      toast.push(t("cash.operation_added"), "success");
      onClose();
      setForm((f) => ({ ...f, amount: "", counterparty: "", note: "" }));
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  return (
    <Modal
      open={open}
      title={t("cash.add_operation")}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={submit} loading={create.isPending}>
            {t("common.create")}
          </Button>
        </>
      }
    >
      <Field label={t("cash.register")}>
        <Select
          value={form.register || ""}
          placeholder="—"
          onChange={(e) => set({ register: Number(e.target.value) })}
          options={(registers.data ?? []).map((r) => ({ value: r.id, label: r.name }))}
        />
      </Field>
      <Field label={t("money.income") + " / " + t("money.expense")}>
        <Select
          value={form.kind}
          onChange={(e) => set({ kind: e.target.value as "income" | "expense" })}
          options={[
            { value: "income", label: t("money.income") },
            { value: "expense", label: t("money.expense") },
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
      <Field label={t("common.method")}>
        <Select
          value={form.method}
          onChange={(e) => set({ method: e.target.value as "cash" | "transfer" })}
          options={[
            { value: "cash", label: t("money.cash") },
            { value: "transfer", label: t("money.transfer") },
          ]}
        />
      </Field>
      <Field label={t("common.date")}>
        <Input
          type="date"
          value={form.occurred_on}
          onChange={(e) => set({ occurred_on: e.target.value })}
        />
      </Field>
      <Field label={t("finance.counterparty")}>
        <Input
          value={form.counterparty}
          onChange={(e) => set({ counterparty: e.target.value })}
        />
      </Field>
      <Field label={t("common.note")}>
        <Textarea value={form.note} onChange={(e) => set({ note: e.target.value })} />
      </Field>
    </Modal>
  );
}

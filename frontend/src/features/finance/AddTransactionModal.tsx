import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useBusinesses, useExpenseCategories } from "@/entities/business";
import { useCreateTransaction, type TransactionCreate } from "@/entities/transaction";
import { toApiError } from "@/shared/api";
import { toISODate } from "@/shared/lib";
import { Button, Field, FormRow, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

export function AddTransactionModal({
  open,
  kind,
  onClose,
}: {
  open: boolean;
  kind: "income" | "expense";
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const businesses = useBusinesses();
  const categories = useExpenseCategories();
  const create = useCreateTransaction();

  const [form, setForm] = useState<TransactionCreate>({
    business: 0,
    kind,
    amount: "",
    method: "cash",
    occurred_on: toISODate(new Date()),
    counterparty: "",
    note: "",
  });

  const set = (patch: Partial<TransactionCreate>) => setForm((f) => ({ ...f, ...patch }));

  const submit = async () => {
    if (!form.business || !form.amount) {
      toast.push("Заполните бизнес и сумму", "error");
      return;
    }
    try {
      await create.mutateAsync({ ...form, kind });
      toast.push(kind === "income" ? "Приход добавлен" : "Расход добавлен", "success");
      onClose();
      setForm((f) => ({ ...f, amount: "", counterparty: "", note: "" }));
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const title = kind === "income" ? t("finance.add_income") : t("finance.add_expense");

  return (
    <Modal
      open={open}
      title={title}
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
      <Field label={t("common.business")}>
        <Select
          value={form.business || ""}
          placeholder="—"
          onChange={(e) => set({ business: Number(e.target.value) })}
          options={(businesses.data ?? []).map((b) => ({ value: b.id, label: b.name }))}
        />
      </Field>
      {kind === "expense" && (
        <Field label={t("common.category")}>
          <Select
            value={form.category ?? ""}
            placeholder="—"
            onChange={(e) => set({ category: Number(e.target.value) })}
            options={(categories.data ?? []).map((c) => ({ value: c.id, label: c.name }))}
          />
        </Field>
      )}
      <FormRow>
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
      </FormRow>
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

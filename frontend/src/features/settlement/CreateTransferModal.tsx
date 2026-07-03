import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useBusinesses } from "@/entities/business";
import { useCreateTransfer, type TransferCreate } from "@/entities/settlement";
import { toApiError } from "@/shared/api";
import { toISODate } from "@/shared/lib";
import { Button, Field, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

const empty = (): TransferCreate => ({
  from_business: 0,
  to_business: 0,
  amount: "",
  occurred_on: toISODate(new Date()),
  description: "",
  is_barter: false,
});

export function CreateTransferModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const businesses = useBusinesses();
  const create = useCreateTransfer();

  const [form, setForm] = useState<TransferCreate>(empty);
  const set = (patch: Partial<TransferCreate>) => setForm((f) => ({ ...f, ...patch }));

  const submit = async () => {
    if (!form.from_business || !form.to_business || !form.amount) {
      toast.push(t("settlements.msg_fill"), "error");
      return;
    }
    try {
      await create.mutateAsync(form);
      toast.push(t("settlements.msg_transfer_created"), "success");
      onClose();
      setForm(empty());
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const options = (businesses.data ?? []).map((b) => ({ value: b.id, label: b.name }));

  return (
    <Modal
      open={open}
      title={t("settlements.add_transfer")}
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
      <Field label={t("settlements.from_business")}>
        <Select
          value={form.from_business || ""}
          placeholder="—"
          onChange={(e) => set({ from_business: Number(e.target.value) })}
          options={options}
        />
      </Field>
      <Field label={t("settlements.to_business")}>
        <Select
          value={form.to_business || ""}
          placeholder="—"
          onChange={(e) => set({ to_business: Number(e.target.value) })}
          options={options}
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
      <Field label={t("settlements.description")}>
        <Textarea
          value={form.description ?? ""}
          onChange={(e) => set({ description: e.target.value })}
        />
      </Field>
      <Field label={t("settlements.barter")}>
        <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <input
            type="checkbox"
            checked={form.is_barter ?? false}
            onChange={(e) => set({ is_barter: e.target.checked })}
          />
          {t("common.yes")}
        </label>
      </Field>
    </Modal>
  );
}

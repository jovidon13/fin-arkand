import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useBusinesses, useExpenseCategories } from "@/entities/business";
import {
  useCreateApprovalRequest,
  type CreateRequestPayload,
} from "@/entities/approval";
import { toApiError } from "@/shared/api";
import { toISODate } from "@/shared/lib";
import { Button, Field, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

interface FormState {
  business: number;
  amount: string;
  purpose: string;
  occurred_on: string;
  category: number | null;
  description: string;
}

export function CreateApprovalRequestModal({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const businesses = useBusinesses();
  const categories = useExpenseCategories();
  const create = useCreateApprovalRequest();

  const [form, setForm] = useState<FormState>({
    business: 0,
    amount: "",
    purpose: "",
    occurred_on: toISODate(new Date()),
    category: null,
    description: "",
  });

  const set = (patch: Partial<FormState>) => setForm((f) => ({ ...f, ...patch }));

  const submit = async () => {
    if (!form.business || !form.amount || !form.purpose.trim()) {
      toast.push(t("approvals.fill_required"), "error");
      return;
    }
    const payload: CreateRequestPayload = {
      business: form.business,
      amount: form.amount,
      purpose: form.purpose.trim(),
      occurred_on: form.occurred_on,
      category: form.category ?? undefined,
      description: form.description || undefined,
    };
    try {
      await create.mutateAsync(payload);
      toast.push(t("approvals.created"), "success");
      onClose();
      setForm((f) => ({
        ...f,
        amount: "",
        purpose: "",
        category: null,
        description: "",
      }));
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  return (
    <Modal
      open={open}
      title={t("approvals.new_request")}
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
      <Field label={t("approvals.purpose")}>
        <Input value={form.purpose} onChange={(e) => set({ purpose: e.target.value })} />
      </Field>
      <Field label={t("common.category")}>
        <Select
          value={form.category ?? ""}
          placeholder="—"
          onChange={(e) => set({ category: e.target.value ? Number(e.target.value) : null })}
          options={(categories.data ?? []).map((c) => ({ value: c.id, label: c.name }))}
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
      <Field label={t("approvals.description")}>
        <Textarea
          value={form.description}
          onChange={(e) => set({ description: e.target.value })}
        />
      </Field>
    </Modal>
  );
}

import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useBusinesses, useExpenseCategories } from "@/entities/business";
import { useUploadDocument, type DocType } from "@/entities/document";
import { useCreateTransaction, type TransactionCreate } from "@/entities/transaction";
import { useOwners } from "@/entities/user";
import { toApiError } from "@/shared/api";
import { toISODate } from "@/shared/lib";
import { Button, Field, FormRow, Input, Modal, Select, Textarea, useToast } from "@/shared/ui";

export type OperationKind = "income" | "expense" | "disbursement";

interface PendingDoc {
  doc_type: DocType;
  file: File;
}

const DOC_TYPES: DocType[] = ["receipt", "invoice", "contract", "waybill", "other"];

export function AddTransactionModal({
  open,
  kind,
  onClose,
}: {
  open: boolean;
  kind: OperationKind;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const businesses = useBusinesses();
  const categories = useExpenseCategories();
  const owners = useOwners();
  const create = useCreateTransaction();
  const upload = useUploadDocument();

  const isDisbursement = kind === "disbursement";
  const apiKind = kind === "income" ? "income" : "expense";

  const [form, setForm] = useState<TransactionCreate>({
    business: 0,
    kind: apiKind,
    amount: "",
    method: "cash",
    occurred_on: toISODate(new Date()),
    counterparty: "",
    note: "",
  });
  const [recipient, setRecipient] = useState<number | "">("");
  const [docType, setDocType] = useState<DocType>("receipt");
  const [docs, setDocs] = useState<PendingDoc[]>([]);

  const set = (patch: Partial<TransactionCreate>) => setForm((f) => ({ ...f, ...patch }));

  const ownerList = owners.data ?? [];

  const resetAfter = () => {
    setForm((f) => ({ ...f, amount: "", counterparty: "", note: "" }));
    setRecipient("");
    setDocs([]);
  };

  const submit = async () => {
    if (!form.business || !form.amount) {
      toast.push(t("finance.msg_fill"), "error");
      return;
    }
    if (isDisbursement && !recipient) {
      toast.push(t("finance.msg_pick_recipient"), "error");
      return;
    }
    try {
      const tx = await create.mutateAsync({
        ...form,
        kind: apiKind,
        is_disbursement: isDisbursement,
        recipient_manager: isDisbursement ? Number(recipient) : undefined,
      });
      // Upload attached documents (фото документов) against the new operation.
      for (const d of docs) {
        await upload.mutateAsync({
          target: "transaction",
          object_id: tx.id,
          doc_type: d.doc_type,
          file: d.file,
        });
      }
      toast.push(
        isDisbursement
          ? t("finance.msg_disbursement_added")
          : kind === "income"
            ? t("finance.msg_income_added")
            : t("finance.msg_expense_added"),
        "success",
      );
      onClose();
      resetAfter();
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const addFiles = (files: FileList | null) => {
    if (!files) return;
    const picked = Array.from(files).map((file) => ({ doc_type: docType, file }));
    setDocs((d) => [...d, ...picked]);
  };

  const title = isDisbursement
    ? t("finance.add_disbursement")
    : kind === "income"
      ? t("finance.add_income")
      : t("finance.add_expense");

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
          <Button onClick={submit} loading={create.isPending || upload.isPending}>
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

      {isDisbursement && (
        <Field label={t("finance.recipient_manager")}>
          <Select
            value={recipient || ""}
            placeholder="—"
            onChange={(e) => setRecipient(e.target.value ? Number(e.target.value) : "")}
            options={ownerList.map((u) => ({ value: u.id, label: u.full_name || u.username }))}
          />
        </Field>
      )}

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

      {/* Фото документов: чек / счёт / договор / накладная */}
      <Field label={t("finance.documents")}>
        <FormRow>
          <Select
            value={docType}
            onChange={(e) => setDocType(e.target.value as DocType)}
            options={DOC_TYPES.map((d) => ({ value: d, label: t(`docs.${d}`) }))}
          />
          <Input
            type="file"
            accept="image/*,.pdf"
            multiple
            onChange={(e) => {
              addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </FormRow>
        {docs.length > 0 && (
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 13, color: "var(--n-700)" }}>
            {docs.map((d, i) => (
              <li key={i} style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                <span>
                  {t(`docs.${d.doc_type}`)}: {d.file.name}
                </span>
                <button
                  type="button"
                  onClick={() => setDocs((list) => list.filter((_, j) => j !== i))}
                  style={{ border: "none", background: "none", color: "var(--error)", cursor: "pointer" }}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </Field>
    </Modal>
  );
}

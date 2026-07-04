import { useState } from "react";
import { useTranslation } from "react-i18next";

import {
  docTypes,
  useOperationDocuments,
  useUploadDocument,
  type DocTarget,
  type DocType,
} from "@/entities/document";
import { toApiError } from "@/shared/api";
import { formatDate } from "@/shared/lib";
import { Button, Field, FormRow, Input, Loading, Modal, Select, useToast } from "@/shared/ui";

const isImage = (url: string | null, name: string) =>
  /\.(png|jpe?g|gif|webp|bmp|heic)$/i.test(url ?? "") || /\.(png|jpe?g|gif|webp|bmp|heic)$/i.test(name);

/** Просмотр и загрузка фото документов (чек/счёт/договор/накладная) любой операции. */
export function OperationDocumentsModal({
  open,
  target,
  objectId,
  onClose,
  canUpload = true,
}: {
  open: boolean;
  target: DocTarget;
  objectId: number | null;
  onClose: () => void;
  canUpload?: boolean;
}) {
  const { t } = useTranslation();
  const toast = useToast();
  const docs = useOperationDocuments(target, objectId);
  const upload = useUploadDocument();
  const [docType, setDocType] = useState<DocType>("receipt");

  const addFiles = async (files: FileList | null) => {
    if (!files || objectId == null) return;
    try {
      for (const file of Array.from(files)) {
        await upload.mutateAsync({ target, object_id: objectId, doc_type: docType, file });
      }
      toast.push(t("docs.uploaded"), "success");
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  const list = docs.data ?? [];

  return (
    <Modal
      open={open}
      title={t("docs.title")}
      onClose={onClose}
      footer={
        <Button variant="secondary" onClick={onClose}>
          {t("common.close")}
        </Button>
      }
    >
      {canUpload && (
        <Field label={t("finance.documents")}>
          <FormRow>
            <Select
              value={docType}
              onChange={(e) => setDocType(e.target.value as DocType)}
              options={docTypes.map((d) => ({ value: d, label: t(`docs.${d}`) }))}
            />
            <Input
              type="file"
              accept="image/*,.pdf"
              multiple
              disabled={upload.isPending || objectId == null}
              onChange={(e) => {
                void addFiles(e.target.files);
                e.target.value = "";
              }}
            />
          </FormRow>
        </Field>
      )}

      {docs.isLoading ? (
        <Loading />
      ) : list.length === 0 ? (
        <div style={{ color: "var(--n-500)", padding: "12px 0" }}>{t("docs.empty")}</div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
          {list.map((d) => (
            <a
              key={d.id}
              href={d.file_url ?? "#"}
              target="_blank"
              rel="noreferrer"
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 10,
                border: "1px solid var(--n-200)",
                borderRadius: 10,
                textDecoration: "none",
                color: "inherit",
              }}
            >
              {d.file_url && isImage(d.file_url, d.original_name) ? (
                <img
                  src={d.file_url}
                  alt={d.doc_type_display}
                  style={{ width: 48, height: 48, objectFit: "cover", borderRadius: 8 }}
                />
              ) : (
                <span style={{ fontSize: 28, width: 48, textAlign: "center" }}>📄</span>
              )}
              <span style={{ display: "flex", flexDirection: "column", gap: 2, minWidth: 0 }}>
                <strong style={{ fontSize: 14 }}>{d.doc_type_display}</strong>
                <span
                  style={{
                    fontSize: 12,
                    color: "var(--n-600)",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {d.original_name || d.file}
                </span>
                <span style={{ fontSize: 11, color: "var(--n-500)" }}>
                  {d.uploaded_by_name ?? "—"} · {formatDate(d.created_at)}
                </span>
              </span>
            </a>
          ))}
        </div>
      )}
    </Modal>
  );
}

export const docTypes = ["receipt", "invoice", "contract", "waybill", "other"] as const;
export type DocType = (typeof docTypes)[number];

/** Operation kinds a document may be attached to (matches backend ALLOWED_TARGETS). */
export type DocTarget = "transaction" | "cashoperation" | "transfer" | "externaldebt";

export interface OperationDocument {
  id: number;
  doc_type: DocType;
  doc_type_display: string;
  file: string;
  file_url: string | null;
  original_name: string;
  note: string;
  operation_type: string;
  object_id: number;
  uploaded_by: number | null;
  uploaded_by_name: string | null;
  created_at: string;
}

export interface UploadDocumentInput {
  target: DocTarget;
  object_id: number;
  doc_type: DocType;
  file: File;
  note?: string;
}

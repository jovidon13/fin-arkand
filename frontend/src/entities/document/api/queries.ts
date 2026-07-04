import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/shared/api";

import type {
  DocTarget,
  OperationDocument,
  UploadDocumentInput,
} from "../model/types";

const KEY = "documents";

export function useOperationDocuments(target: DocTarget, objectId: number | null) {
  return useQuery({
    queryKey: [KEY, target, objectId],
    enabled: objectId != null,
    queryFn: async () => {
      const { data } = await api.get<OperationDocument[]>("/documents", {
        params: { target, object_id: objectId },
      });
      return data;
    },
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (input: UploadDocumentInput) => {
      const fd = new FormData();
      fd.append("target", input.target);
      fd.append("object_id", String(input.object_id));
      fd.append("doc_type", input.doc_type);
      fd.append("file", input.file);
      if (input.note) fd.append("note", input.note);
      const { data } = await api.post<OperationDocument>("/documents", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return data;
    },
    onSuccess: (_d, input) => {
      void qc.invalidateQueries({ queryKey: [KEY, input.target, input.object_id] });
    },
  });
}

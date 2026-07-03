import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useRunPayroll } from "@/entities/payroll";
import { toApiError } from "@/shared/api";
import { MONTHS_RU } from "@/shared/lib";
import { Button, Field, Input, Modal, Select, useToast } from "@/shared/ui";

export function RunPayrollModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = useTranslation();
  const toast = useToast();
  const run = useRunPayroll();

  const now = new Date();
  const [year, setYear] = useState<number>(now.getFullYear());
  const [month, setMonth] = useState<number>(now.getMonth() + 1);

  const submit = async () => {
    try {
      await run.mutateAsync({ year, month });
      toast.push(t("payroll.run_success"), "success");
      onClose();
    } catch (e) {
      toast.push(toApiError(e).message, "error");
    }
  };

  return (
    <Modal
      open={open}
      title={t("payroll.run")}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button onClick={submit} loading={run.isPending}>
            {t("payroll.run")}
          </Button>
        </>
      }
    >
      <Field label={t("payroll.year")}>
        <Input
          type="number"
          min="2000"
          max="2100"
          step="1"
          value={year}
          onChange={(e) => setYear(Number(e.target.value))}
        />
      </Field>
      <Field label={t("payroll.period_month")}>
        <Select
          value={month}
          onChange={(e) => setMonth(Number(e.target.value))}
          options={MONTHS_RU.map((name, i) => ({ value: i + 1, label: name }))}
        />
      </Field>
      <p style={{ margin: "4px 2px 0", fontSize: 13, color: "var(--n-600)" }}>
        {t("payroll.metrics_note")}
      </p>
    </Modal>
  );
}

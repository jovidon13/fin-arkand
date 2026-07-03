import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import ru from "./ru.json";
import tj from "./tj.json";

export const LANGS = [
  { code: "ru", label: "Русский" },
  { code: "tj", label: "Тоҷикӣ" },
] as const;

export type LangCode = (typeof LANGS)[number]["code"];

const STORAGE_KEY = "arkand.lang";

i18n.use(initReactI18next).init({
  resources: {
    ru: { translation: ru },
    tj: { translation: tj },
  },
  lng: (localStorage.getItem(STORAGE_KEY) as LangCode) ?? "ru",
  fallbackLng: "ru",
  interpolation: { escapeValue: false },
});

export function setLanguage(code: LangCode) {
  localStorage.setItem(STORAGE_KEY, code);
  void i18n.changeLanguage(code);
}

export default i18n;

import "@/shared/config/global.css";
import "@/shared/i18n";

import { AppProviders } from "@/app/providers";

import { AppRouter } from "./router/AppRouter";

export function App() {
  return (
    <AppProviders>
      <AppRouter />
    </AppProviders>
  );
}

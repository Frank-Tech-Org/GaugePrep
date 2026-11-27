import type { Metadata, Viewport } from "next";
import type { ReactNode } from "react";
import { Header } from "../components/Header";
import { Providers } from "../components/Providers";
import { Msg } from "../i18n/provider";
import { BOOT_SCRIPT } from "../theme/boot-script";
import "../styles/tokens.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "GaugePrep",
  description: "TCF Canada exam prep",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  colorScheme: "light dark",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: BOOT_SCRIPT }} />
      </head>
      <body>
        <Providers>
          <a className="skip-link" href="#main">
            <Msg id="shell.skipToContent" />
          </a>
          <Header />
          <main id="main" tabIndex={-1}>
            {children}
          </main>
        </Providers>
      </body>
    </html>
  );
}

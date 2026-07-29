import type { Metadata } from "next";
import { IBM_Plex_Mono, Inter } from "next/font/google";
import Sidebar from "@/components/Sidebar";
import "./globals.css";

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
});

const sans = Inter({ subsets: ["latin"], variable: "--font-sans" });

export const metadata: Metadata = {
  title: "web-scraper",
  description: "Scrape jobs, pipeline status, and stored pages.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body
        className={`${mono.variable} ${sans.variable} font-sans antialiased`}
        style={{ background: "var(--bg)", color: "var(--text-primary)" }}
      >
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}

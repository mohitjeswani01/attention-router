import type { Metadata } from "next";
import { Inter, Lora, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";
import TabNav from "./TabNav";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const lora = Lora({
  subsets: ["latin"],
  variable: "--font-serif",
  style: ["normal", "italic"],
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Attention Router — Intelligence Layer",
  description:
    "Ranked urgency queue, auto-approve engine, and risk-scored PR briefing for your agent fleet.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${lora.variable} ${jetbrains.variable}`}
    >
      <body className="bg-[#0a0a0b] text-white/90 font-sans antialiased min-h-screen flex flex-col">
        {/* ── Header ──────────────────────────────────────────── */}
        <header className="shrink-0 border-b border-white/[0.06] bg-[#0a0a0b]/80 backdrop-blur-xl sticky top-0 z-50">
          <div className="max-w-[1600px] mx-auto px-6 h-14 flex items-center justify-between">
            {/* Logo / Title */}
            <Link href="/queue" className="flex items-center gap-3 group">
              {/* Gradient dot */}
              <div className="w-2 h-2 rounded-full bg-gradient-to-br from-[#ec4899] to-[#06b6d4] group-hover:shadow-[0_0_12px_rgba(236,72,153,0.4)] transition-shadow" />
              <span className="text-sm font-medium tracking-tight text-white/80 group-hover:text-white/95 transition-colors">
                Attention Router
              </span>
            </Link>

            {/* Tab Navigation */}
            <TabNav />

            {/* Right side — status dot */}
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-[11px] text-white/30 font-mono">live</span>
            </div>
          </div>
        </header>

        {/* ── Main ───────────────────────────────────────────── */}
        <main className="flex-1 flex flex-col">{children}</main>
      </body>
    </html>
  );
}

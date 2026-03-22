import type { Metadata } from "next";
import "./globals.css";
import { TopNav } from "@/components/shared/TopNav";

export const metadata: Metadata = {
  title: "AI Payments Control Tower",
  description: "Cross-border payments operations intelligence platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#060B18] text-slate-100 antialiased">
        <TopNav />
        <main className="pt-16 min-h-screen">{children}</main>
      </body>
    </html>
  );
}

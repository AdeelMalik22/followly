import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Followly — Your AI teammate for every conversation",
    template: "%s | Followly",
  },
  description: "Followly helps growing businesses capture leads, answer customers, and book appointments with an AI teammate.",
  applicationName: "Followly",
  keywords: ["AI CRM", "customer conversations", "lead follow-up", "appointment booking"],
};

interface LayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: LayoutProps) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-[#f7f9fc] text-[#17213b]">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

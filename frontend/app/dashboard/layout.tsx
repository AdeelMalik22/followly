"use client";

import React from "react";
import { useAuth } from "@/components/auth-provider";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-[#edf2f8]">
        <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-[#e7ecf4] border-t-[#3678f6]" />
        <span className="text-sm text-[#7e8aa1]">Loading your business dashboard...</span>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen bg-[#edf2f8] text-[#17213b] overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-[#edf2f8] p-8 lg:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}

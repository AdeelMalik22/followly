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
      <div className="min-h-screen bg-[#070b14] flex flex-col items-center justify-center">
        <div className="w-10 h-10 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin mb-4" />
        <span className="text-sm text-[#7b8aa8]">Loading your business dashboard...</span>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen bg-[#070b14] text-[#e8edf7] overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto bg-[#070b14] p-8">
          {children}
        </main>
      </div>
    </div>
  );
}

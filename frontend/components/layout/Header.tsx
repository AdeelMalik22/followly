"use client";

import React from "react";
import { useAuth } from "@/components/auth-provider";
import { Bell, Search, ChevronDown } from "lucide-react";

export default function Header() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <header className="h-[72px] border-b border-[#e8edf5] bg-white px-8 flex items-center justify-between sticky top-0 z-10 flex-shrink-0">
      <div className="flex items-center gap-6">
        <div className="hidden md:flex items-center gap-2 rounded-xl border border-[#e5eaf2] bg-[#fafbfe] px-3 py-2 w-80">
          <Search className="w-4 h-4 text-[#97a3b8]" /><span className="text-xs text-[#9aa5b8]">Search leads, conversations, appointments...</span>
        </div>
        <span className="hidden lg:flex text-xs text-emerald-600 bg-emerald-50 border border-emerald-100 px-2.5 py-1.5 rounded-full items-center gap-1.5 font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" /> AI assistant live
        </span>
      </div>

      <div className="flex items-center gap-4">
        <Bell className="w-5 h-5 text-[#66738d]" />
        <div className="text-right hidden sm:block">
          <span className="block text-xs font-bold text-[#17213b]">{user.name}</span>
          <span className="block text-[10px] text-[#8d99ad]">{user.role}</span>
        </div>
        <div className="w-9 h-9 rounded-full bg-[#f5c7b7] flex items-center justify-center font-extrabold text-sm text-[#6f3d37]">
          {user.name.charAt(0).toUpperCase()}
        </div>
        <ChevronDown className="w-4 h-4 text-[#66738d]" />
      </div>
    </header>
  );
}

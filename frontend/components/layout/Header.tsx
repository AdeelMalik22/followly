"use client";

import React from "react";
import { useAuth } from "@/components/auth-provider";
import { Bell, Search, ChevronDown, Menu } from "lucide-react";

export default function Header() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <header className="sticky top-0 z-20 flex h-[72px] flex-shrink-0 items-center justify-between border-b border-[#cbd6e5] bg-white px-4 shadow-[0_3px_14px_rgba(35,55,90,0.07)] sm:px-8">
      <div className="flex items-center gap-3 sm:gap-6">
        <button aria-label="Open navigation" onClick={() => window.dispatchEvent(new Event("followly:open-menu"))} className="rounded-xl p-2 text-[#66738d] hover:bg-[#f4f7fc] md:hidden"><Menu className="h-5 w-5" /></button>
        <div className="hidden md:flex items-center gap-2 rounded-xl border border-[#d5deeb] bg-[#f7f9fc] px-3 py-2 w-80">
          <Search className="w-4 h-4 text-[#66738d]" /><span className="text-xs text-[#71809a]">Search leads, conversations, appointments...</span>
        </div>
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

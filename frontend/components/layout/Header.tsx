"use client";

import React from "react";
import { useAuth } from "@/components/auth-provider";

export default function Header() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <header className="h-16 border-b border-white/[0.08] bg-[#070b14]/50 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-10 flex-shrink-0">
      <div className="flex items-center gap-4">
        <span className="font-bold text-base text-white">{user.business_name}</span>
        <span className="h-4 w-px bg-white/[0.12]" />
        <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-full flex items-center gap-1.5 font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          AI Assistant Online
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="text-right">
          <span className="block text-xs font-bold text-white">{user.name}</span>
          <span className="block text-[10px] text-[#7b8aa8]">{user.email}</span>
        </div>
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#5d7ef0] to-[#8b5cf6] flex items-center justify-center font-extrabold text-sm text-white shadow-md shadow-[#5d7ef0]/10">
          {user.name.charAt(0).toUpperCase()}
        </div>
      </div>
    </header>
  );
}

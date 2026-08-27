"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { clearAuthToken } from "@/lib/auth";
import {
  LayoutDashboard,
  MessageSquare,
  Calendar,
  Users,
  Database,
  RefreshCw,
  Cpu,
  UserPlus,
  Settings,
  LogOut,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Conversations", href: "/dashboard/conversations", icon: MessageSquare },
  { name: "Appointments", href: "/dashboard/appointments", icon: Calendar },
  { name: "Leads", href: "/dashboard/leads", icon: Users },
  { name: "Knowledge Base", href: "/dashboard/knowledge", icon: Database },
  { name: "Follow-up Rules", href: "/dashboard/follow-up", icon: RefreshCw },
  { name: "Channels", href: "/dashboard/channels", icon: Cpu },
  { name: "Team", href: "/dashboard/team", icon: UserPlus },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  const handleLogout = () => {
    clearAuthToken();
    window.location.href = "/login";
  };

  return (
    <aside className="w-64 bg-[#0a0f1d] border-r border-white/[0.08] flex flex-col h-screen sticky top-0 flex-shrink-0 z-10">
      {/* Brand logo */}
      <div className="p-6 border-b border-white/[0.08] flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#5d7ef0] to-[#8b5cf6] flex items-center justify-center font-extrabold text-sm shadow-[0_0_15px_rgba(93,126,240,0.35)]">
          F
        </div>
        <span className="text-lg font-bold tracking-tight text-white">Followly</span>
      </div>

      {/* Nav items */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl transition-all ${
                isActive
                  ? "bg-[#5d7ef0] text-white shadow-lg shadow-[#5d7ef0]/15"
                  : "text-[#7b8aa8] hover:text-white hover:bg-white/[0.03]"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Business info & Logout */}
      <div className="p-4 border-t border-white/[0.08] bg-[#0c1326]/40">
        {user && (
          <div className="mb-4 px-2">
            <span className="block text-xs font-bold text-[#7b8aa8] truncate">{user.business_name}</span>
            <span className="block text-[10px] text-[#5d7ef0] truncate mt-0.5">{user.name} ({user.role})</span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-red-400 hover:text-red-300 hover:bg-red-500/5 rounded-xl transition-all"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}

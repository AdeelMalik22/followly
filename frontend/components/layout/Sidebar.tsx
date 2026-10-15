"use client";

import React, { useEffect, useState } from "react";
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
  CreditCard,
  LogOut,
  Bot,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Conversations", href: "/dashboard/conversations", icon: MessageSquare },
  { name: "AI Agent", href: "/dashboard/agent", icon: Bot },
  { name: "Appointments", href: "/dashboard/appointments", icon: Calendar },
  { name: "Leads", href: "/dashboard/leads", icon: Users },
  { name: "Knowledge Base", href: "/dashboard/knowledge", icon: Database },
  { name: "Follow-up Rules", href: "/dashboard/follow-up", icon: RefreshCw },
  { name: "Channels", href: "/dashboard/channels", icon: Cpu },
  { name: "Team", href: "/dashboard/team", icon: UserPlus },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
  { name: "Usage & Billing", href: "/dashboard/billing", icon: CreditCard },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const open = () => setMobileOpen(true);
    window.addEventListener("followly:open-menu", open);
    return () => window.removeEventListener("followly:open-menu", open);
  }, []);

  const handleLogout = () => {
    clearAuthToken();
    window.location.href = "/login";
  };

  return (
    <>
      {mobileOpen && <button aria-label="Close navigation" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-30 bg-[#17213b]/20 backdrop-blur-sm md:hidden" />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-shrink-0 flex-col border-r border-[#e8edf5] bg-white transition-transform md:sticky md:top-0 md:z-10 md:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
      {/* Brand logo */}
      <div className="p-6 border-b border-[#eef1f6] flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-[#3678f6] flex items-center justify-center font-extrabold text-sm text-white shadow-lg shadow-blue-200">
          ↗
        </div>
        <div><span className="text-xl font-bold tracking-tight text-[#17213b]">Followly</span><span className="block text-[10px] text-[#95a0b5]">Your AI teammate</span></div>
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
                  ? "bg-[#eaf2ff] text-[#1764db] shadow-sm"
                  : "text-[#66738d] hover:text-[#17213b] hover:bg-[#f5f8fc]"
              }`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon className="w-4 h-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* Business info & Logout */}
      <div className="p-4 border-t border-[#eef1f6] bg-[#fbfcfe]">
        {user && (
          <div className="mb-4 px-2">
            <span className="block text-xs font-bold text-[#17213b] truncate">{user.business_name}</span>
            <span className="block text-[10px] text-[#5e88df] truncate mt-0.5">{user.name} · {user.role}</span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium text-[#8d99ad] hover:text-red-500 hover:bg-red-50 rounded-xl transition-all"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
    </>
  );
}

"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  Activity,
  Package,
} from "lucide-react";

const navItems = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "Conversations", href: "/dashboard/conversations", icon: MessageSquare },
  { name: "AI Agent", href: "/dashboard/agent", icon: Bot },
  { name: "Appointments", href: "/dashboard/appointments", icon: Calendar },
  { name: "Leads", href: "/dashboard/leads", icon: Users },
  { name: "Knowledge Base", href: "/dashboard/knowledge", icon: Database },
  { name: "Inventory", href: "/dashboard/inventory", icon: Package },
  { name: "Follow-up Rules", href: "/dashboard/follow-up", icon: RefreshCw },
  { name: "Channels", href: "/dashboard/channels", icon: Cpu },
  { name: "Team", href: "/dashboard/team", icon: UserPlus },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
  { name: "Usage & Billing", href: "/dashboard/billing", icon: CreditCard },
  { name: "Usage", href: "/dashboard/usage", icon: Activity },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const open = () => setMobileOpen(true);
    window.addEventListener("followly:open-menu", open);
    return () => window.removeEventListener("followly:open-menu", open);
  }, []);

  const handleLogout = () => {
    clearAuthToken();
    router.push("/login");
  };

  return (
    <>
      {mobileOpen && <button aria-label="Close navigation" onClick={() => setMobileOpen(false)} className="fixed inset-0 z-30 bg-[#17213b]/20 backdrop-blur-sm md:hidden" />}
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-shrink-0 flex-col border-r border-[#243653] bg-[#14233d] text-white transition-transform md:sticky md:top-0 md:z-10 md:translate-x-0 ${mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}`}>
      {/* Brand logo */}
      <div className="flex items-center gap-3 border-b border-[#263957] p-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#3d83ff] text-sm font-extrabold text-white shadow-lg shadow-blue-950/30">
          ↗
        </div>
        <div><span className="text-xl font-bold tracking-tight text-white">Followly</span><span className="block text-[10px] text-[#9fb0cb]">Your AI teammate</span></div>
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
                  ? "bg-[#3d83ff] text-white shadow-lg shadow-blue-950/20"
                  : "text-[#a9b8cf] hover:bg-[#203453] hover:text-white"
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
      <div className="border-t border-[#263957] bg-[#101d34] p-4">
        {user && (
          <div className="mb-4 px-2">
            <span className="block truncate text-xs font-bold text-white">{user.business_name}</span>
            <span className="mt-0.5 block truncate text-[10px] text-[#8eb7ff]">{user.name} · {user.role}</span>
          </div>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium text-[#a9b8cf] transition-all hover:bg-red-500/15 hover:text-red-300"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
    </>
  );
}

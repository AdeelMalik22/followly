"use client";

import { useEffect, useState } from "react";
import { Activity, ArrowUpRight, Gauge, MessageSquare, Users, Database } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { BillingStatus } from "@/types";
import { Card, CardHeader } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { LoadingState } from "@/components/ui/States";
import toast from "react-hot-toast";

const icons = [MessageSquare, Users, Database, Activity];

export default function UsagePage() {
  const [billing, setBilling] = useState<BillingStatus | null>(null);

  useEffect(() => {
    apiFetch<BillingStatus>("/api/v1/billing/status")
      .then(setBilling)
      .catch((error) => toast.error(error instanceof Error ? error.message : "Unable to load usage."));
  }, []);

  if (!billing) return <LoadingState label="Loading usage overview..." />;

  const entries = Object.keys(billing.limits);
  const percent = (name: string) => billing.limits[name] ? Math.min(100, Math.round(((billing.usage[name] || 0) / billing.limits[name]) * 100)) : 0;

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <div><p className="mb-2 text-sm font-semibold text-[#3678f6]">Workspace analytics</p><h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Usage &amp; plan limits</h1><p className="mt-1.5 text-sm text-[#7e8aa1]">Keep an eye on the resources powering your AI customer experience.</p></div>
        <a href="/dashboard/billing" className="inline-flex items-center gap-2 text-sm font-semibold text-[#3678f6] hover:text-[#1764db]">Manage subscription <ArrowUpRight className="h-4 w-4" /></a>
      </div>
      <Card className="overflow-hidden"><div className="flex flex-col justify-between gap-5 bg-gradient-to-r from-[#eff5ff] to-[#f7f3ff] p-6 md:flex-row md:items-center"><div className="flex items-center gap-4"><div className="rounded-2xl bg-white p-3 text-[#3678f6] shadow-sm"><Gauge className="h-6 w-6" /></div><div><p className="text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">Current plan</p><div className="mt-1 flex items-center gap-3"><h2 className="text-xl font-bold capitalize text-[#17213b]">{billing.plan.replaceAll("_", " ")}</h2><Badge tone={billing.status === "active" ? "green" : "yellow"}>{billing.status}</Badge></div></div></div><p className="text-sm text-[#53617a]">Usage resets with your billing period.</p></div><div className="grid gap-4 p-6 sm:grid-cols-2 lg:grid-cols-4">{entries.map((name, index) => { const Icon = icons[index % icons.length]; const used = billing.usage[name] || 0; const limit = billing.limits[name]; const value = percent(name); return <div key={name} className="rounded-2xl border border-[#eef1f6] bg-[#fbfcfe] p-4"><div className="flex items-center justify-between"><div className="rounded-xl bg-[#eaf2ff] p-2 text-[#3678f6]"><Icon className="h-4 w-4" /></div><span className="text-xs font-bold text-[#53617a]">{value}%</span></div><p className="mt-4 text-xs font-semibold capitalize text-[#53617a]">{name.replaceAll("_", " ")}</p><p className="mt-1 text-lg font-bold text-[#17213b]">{used.toLocaleString()} <span className="text-xs font-normal text-[#8b97ab]">/ {limit.toLocaleString()}</span></p><div className="mt-3 h-2 overflow-hidden rounded-full bg-[#e8edf5]"><div className={`h-full rounded-full ${value >= 90 ? "bg-amber-500" : "bg-[#3678f6]"}`} style={{ width: `${value}%` }} /></div></div>; })}</div></Card>
      <Card><CardHeader title="Usage guidance" description="Your limits are enforced at the service boundary to keep the workspace predictable." /><div className="grid gap-4 p-6 md:grid-cols-3"><div className="rounded-2xl bg-[#f7f9fc] p-4"><p className="text-sm font-semibold text-[#17213b]">Approaching a limit?</p><p className="mt-2 text-xs leading-5 text-[#7e8aa1]">Upgrade before a resource reaches its cap to keep conversations and automations running.</p></div><div className="rounded-2xl bg-[#f7f9fc] p-4"><p className="text-sm font-semibold text-[#17213b]">Need a larger plan?</p><p className="mt-2 text-xs leading-5 text-[#7e8aa1]">Compare plan allowances and move to a plan that matches your customer volume.</p></div><div className="rounded-2xl bg-[#f7f9fc] p-4"><p className="text-sm font-semibold text-[#17213b]">Review billing</p><p className="mt-2 text-xs leading-5 text-[#7e8aa1]">Open subscription settings to view invoices, change plans, or cancel.</p></div></div></Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { BillingStatus, ConfigurationAudit } from "@/types";
import toast from "react-hot-toast";

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingStatus | null>(null);
  const [audits, setAudits] = useState<ConfigurationAudit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiFetch<BillingStatus>("/api/v1/billing/status"),
      apiFetch<ConfigurationAudit[]>("/api/v1/business/configuration/audit"),
    ]).then(([status, history]) => { setBilling(status); setAudits(history); })
      .catch((error) => toast.error(error.message || "Unable to load usage details."))
      .finally(() => setLoading(false));
  }, []);

  const startCheckout = async () => {
    try {
      const result = await apiFetch<{ checkout_url: string }>("/api/v1/billing/checkout", { method: "POST" });
      window.location.href = result.checkout_url;
    } catch (error: any) { toast.error(error.message || "Unable to start checkout."); }
  };

  if (loading || !billing) return <div className="py-20 text-center text-[#7b8aa8]">Loading usage and billing...</div>;
  const percent = (name: string) => billing.limits[name] ? Math.min(100, Math.round((billing.usage[name] || 0) / billing.limits[name] * 100)) : 0;

  return <div className="space-y-8">
    <div><h1 className="text-2xl font-extrabold text-white">Usage &amp; Billing</h1><p className="text-sm text-[#7b8aa8]">Monitor consumption, plan limits, and configuration history.</p></div>
    <section className="bg-white/[0.02] border border-white/[0.08] rounded-2xl p-6">
      <div className="flex justify-between items-start"><div><p className="text-xs uppercase text-[#7b8aa8]">Current plan</p><h2 className="text-2xl font-bold text-white mt-1">{billing.plan}</h2><p className="text-sm text-[#aab4cb] mt-1">Subscription: {billing.status}</p></div><button onClick={startCheckout} className="rounded-xl bg-[#5d7ef0] px-4 py-2 text-sm font-semibold text-white">Upgrade plan</button></div>
      <div className="grid gap-4 md:grid-cols-3 mt-6">{Object.keys(billing.limits).map((name) => <div key={name} className="rounded-xl bg-white/[0.04] p-4"><div className="flex justify-between text-xs text-[#aab4cb]"><span>{name.replace("_", " ")}</span><span>{billing.usage[name] || 0} / {billing.limits[name]}</span></div><div className="h-2 rounded-full bg-white/[0.08] mt-3"><div className="h-2 rounded-full bg-[#5d7ef0]" style={{ width: `${percent(name)}%` }} /></div></div>)}</div>
    </section>
    <section className="bg-white/[0.02] border border-white/[0.08] rounded-2xl p-6"><h2 className="text-sm font-bold text-white">Configuration audit history</h2><div className="mt-4 space-y-3">{audits.length === 0 ? <p className="text-sm text-[#7b8aa8]">No configuration changes recorded.</p> : audits.map((audit) => <div key={audit.id} className="flex justify-between border-b border-white/[0.06] pb-3 text-sm"><span className="text-[#aab4cb]">Configuration snapshot #{audit.id}</span><span className="text-[#7b8aa8]">{new Date(audit.created_at).toLocaleString()}</span></div>)}</div></section>
  </div>;
}

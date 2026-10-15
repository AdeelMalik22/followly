"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { ArrowLeft, ArrowRight, CheckCircle2 } from "lucide-react";
import { apiFetch } from "@/lib/api";
import toast from "react-hot-toast";

export default function RecoverPage() {
  const [email, setEmail] = useState(""); const [sent, setSent] = useState(false); const [loading, setLoading] = useState(false);
  const submit = async (event: FormEvent) => { event.preventDefault(); setLoading(true); try { await apiFetch("/api/v1/auth/password-recovery", { method: "POST", body: JSON.stringify({ email }) }); setSent(true); } catch (error) { toast.error(error instanceof Error ? error.message : "Unable to start recovery."); } finally { setLoading(false); } };
  return <main className="flex min-h-screen items-center justify-center bg-[#f7f9fc] p-4"><section className="w-full max-w-md rounded-3xl border border-[#e5eaf2] bg-white p-8 shadow-[0_20px_60px_rgba(35,55,90,0.08)]"><Link href="/login" className="mb-10 inline-flex items-center gap-2 text-xs font-semibold text-[#71809a]"><ArrowLeft className="h-4 w-4" />Back to sign in</Link><div className="mb-8"><div className="mb-5 flex h-10 w-10 items-center justify-center rounded-xl bg-[#3678f6] text-xl font-black text-white">↗</div><h1 className="text-2xl font-bold text-[#17213b]">Reset your password</h1><p className="mt-2 text-sm leading-6 text-[#8b97ab]">Enter your account email and we&apos;ll help you get back into your workspace.</p></div>{sent ? <div className="rounded-2xl bg-emerald-50 p-5 text-sm text-emerald-800"><CheckCircle2 className="mb-3 h-6 w-6 text-emerald-600" /><p className="font-bold">Recovery request received</p><p className="mt-1 text-xs leading-5">If an account exists for this email, recovery instructions have been created.</p></div> : <form onSubmit={submit} className="space-y-5"><label className="block"><span className="mb-2 block text-xs font-bold text-[#53617a]">Email address</span><input required type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@company.com" className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-4 py-3 text-sm outline-none focus:border-[#3678f6] focus:ring-4 focus:ring-blue-50" /></label><button disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#3678f6] py-3.5 text-sm font-bold text-white shadow-lg shadow-blue-200 disabled:opacity-50">{loading ? "Sending..." : "Send recovery instructions"}<ArrowRight className="h-4 w-4" /></button></form>}</section></main>;
}

"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <main className="flex min-h-screen items-center justify-center bg-[#f7f9fc] p-6"><section className="w-full max-w-md rounded-3xl border border-[#e5eaf2] bg-white p-8 text-center shadow-[0_20px_60px_rgba(35,55,90,0.08)]"><div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-amber-50 text-amber-600"><AlertTriangle className="h-6 w-6" /></div><h1 className="text-xl font-bold text-[#17213b]">Something went wrong</h1><p className="mt-2 text-sm leading-6 text-[#7e8aa1]">We couldn&apos;t load this page. Try again, and your workspace should be right where you left it.</p><button onClick={() => reset()} className="mt-6 inline-flex items-center gap-2 rounded-xl bg-[#3678f6] px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-blue-200 hover:bg-[#2568e4]"><RefreshCw className="h-4 w-4" />Try again</button></section></main>;
}

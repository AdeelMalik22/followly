import React from "react";
import { Loader2, Inbox } from "lucide-react";

export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return <div className="flex min-h-48 flex-col items-center justify-center gap-3 text-sm text-[#8793a8]"><Loader2 className="h-6 w-6 animate-spin text-[#3678f6]" />{label}</div>;
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return <div className="flex min-h-52 flex-col items-center justify-center px-6 text-center"><div className="mb-3 rounded-2xl bg-[#eef4ff] p-3 text-[#3678f6]"><Inbox className="h-5 w-5" /></div><h3 className="text-sm font-bold text-[#17213b]">{title}</h3><p className="mt-1 max-w-sm text-xs leading-5 text-[#8793a8]">{description}</p>{action && <div className="mt-4">{action}</div>}</div>;
}

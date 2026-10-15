import React from "react";

export function Card({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <section className={`rounded-2xl border border-[#d8e0ec] bg-white shadow-[0_8px_24px_rgba(35,55,90,0.07)] ${className}`}>{children}</section>;
}

export function CardHeader({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[#e1e7f0] px-6 py-5">
      <div><h2 className="text-[15px] font-bold text-[#17213b]">{title}</h2>{description && <p className="mt-1 text-xs text-[#66738d]">{description}</p>}</div>
      {action}
    </div>
  );
}

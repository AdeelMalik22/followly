import React from "react";

export function Card({ className = "", children }: { className?: string; children: React.ReactNode }) {
  return <section className={`rounded-2xl border border-[#e7ecf4] bg-white shadow-[0_5px_20px_rgba(35,55,90,0.04)] ${className}`}>{children}</section>;
}

export function CardHeader({ title, description, action }: { title: string; description?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[#eef1f6] px-6 py-5">
      <div><h2 className="text-[15px] font-bold text-[#17213b]">{title}</h2>{description && <p className="mt-1 text-xs text-[#8b97ab]">{description}</p>}</div>
      {action}
    </div>
  );
}

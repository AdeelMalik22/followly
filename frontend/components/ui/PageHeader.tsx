import React from "react";

export function PageHeader({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div><h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">{title}</h1><p className="mt-1.5 text-sm text-[#7e8aa1]">{description}</p></div>
      {action}
    </div>
  );
}

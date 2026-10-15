import React from "react";
import { Loader2 } from "lucide-react";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  loading?: boolean;
};

export function Button({ variant = "primary", loading = false, className = "", children, disabled, ...props }: ButtonProps) {
  const styles = {
    primary: "bg-[#3678f6] text-white shadow-sm shadow-blue-200 hover:bg-[#2568e4]",
    secondary: "border border-[#dfe6f1] bg-white text-[#34415d] hover:border-[#b9c9e3] hover:bg-[#f8faff]",
    ghost: "text-[#63708a] hover:bg-[#f3f6fb] hover:text-[#17213b]",
    danger: "border border-red-100 bg-red-50 text-red-600 hover:bg-red-100",
  }[variant];
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${styles} ${className}`}
      {...props}
    >
      {loading && <Loader2 className="h-4 w-4 animate-spin" />}
      {children}
    </button>
  );
}

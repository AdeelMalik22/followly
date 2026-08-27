"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, []);

  return (
    <div className="min-h-screen bg-[#070b14] flex flex-col items-center justify-center">
      <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin mb-4" />
      <span className="text-xs text-[#7b8aa8]">Redirecting to your dashboard...</span>
    </div>
  );
}

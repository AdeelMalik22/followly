"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setAuthToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import toast from "react-hot-toast";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter both email and password.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      setAuthToken(data.access_token, remember);
      toast.success("Successfully logged in!");
      
      // Let AuthProvider refresh status and handle redirect to dashboard or onboarding
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.message || "Invalid credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-[#070b14] overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(65,105,225,0.15)] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(93,126,240,0.1)] blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#5d7ef0] to-[#8b5cf6] flex items-center justify-center font-extrabold text-lg shadow-[0_0_20px_rgba(93,126,240,0.3)]">
            F
          </div>
          <span className="text-xl font-bold tracking-tight">Followly</span>
        </div>

        <h1 className="text-2xl font-extrabold text-center mb-1">Welcome back</h1>
        <p className="text-[#7b8aa8] text-sm text-center mb-8">Sign in to your account to continue</p>

        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
              Email Address
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">✉</span>
              <input
                type="email"
                placeholder="you@business.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-3 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
              Password
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔒</span>
              <input
                type={showPassword ? "text" : "password"}
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-3 pl-10 pr-12 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
              >
                {showPassword ? "🙈" : "👁"}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-sm text-[#7b8aa8] cursor-pointer select-none">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
                className="rounded border-white/[0.08] bg-white/[0.06] text-[#5d7ef0] focus:ring-[#5d7ef0]/20 cursor-pointer"
              />
              Remember me
            </label>
            <a href="#" className="text-sm font-semibold text-[#5d7ef0] hover:text-[#7c9cf8] transition-colors">
              Forgot password?
            </a>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#5d7ef0] to-[#7c5cf6] text-white font-semibold text-sm hover:opacity-90 active:scale-[0.98] shadow-lg shadow-[#5d7ef0]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <div className="flex items-center my-6">
          <div className="flex-1 h-px bg-white/[0.08]" />
          <span className="text-xs text-[#7b8aa8] px-3">Don't have an account?</span>
          <div className="flex-1 h-px bg-white/[0.08]" />
        </div>

        <p className="text-center text-sm text-[#7b8aa8]">
          <Link href="/signup" className="font-semibold text-[#5d7ef0] hover:text-[#7c9cf8] transition-colors">
            Create a free account →
          </Link>
        </p>
      </div>
    </div>
  );
}

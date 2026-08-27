"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { setAuthToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import toast from "react-hot-toast";

export default function SignupPage() {
  const [ownerName, setOwnerName] = useState("");
  const [email, setEmail] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("Dental Clinic");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const router = useRouter();

  // Password strength calculation
  const getPasswordScore = () => {
    let score = 0;
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };

  const score = getPasswordScore();
  const strengthColors = ["bg-transparent", "bg-red-400", "bg-amber-400", "bg-amber-400", "bg-emerald-400", "bg-emerald-400"];
  const strengthLabels = ["Too short", "Weak", "Fair", "Good", "Strong", "Excellent"];

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ownerName || !email || !businessName || !password || !confirmPassword) {
      toast.error("Please fill in all required fields.");
      return;
    }
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters.");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }
    if (!termsAccepted) {
      toast.error("You must accept the Terms of Service.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        owner_name: ownerName,
        email,
        business_name: businessName,
        industry,
        password,
        confirm_password: confirmPassword,
        terms_accepted: termsAccepted,
      };

      const data = await apiFetch<{ access_token: string }>("/api/v1/auth/signup", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setAuthToken(data.access_token);
      toast.success("Account created successfully!");
      router.push("/onboarding");
    } catch (err: any) {
      toast.error(err.message || "Failed to create account.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-[#070b14] overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(65,105,225,0.15)] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(93,126,240,0.1)] blur-[120px] pointer-events-none" />

      <div className="w-full max-w-xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#5d7ef0] to-[#8b5cf6] flex items-center justify-center font-extrabold text-lg shadow-[0_0_20px_rgba(93,126,240,0.3)]">
            F
          </div>
          <span className="text-xl font-bold tracking-tight">Followly</span>
        </div>

        <h1 className="text-2xl font-extrabold text-center mb-1">Create your account</h1>
        <p className="text-[#7b8aa8] text-sm text-center mb-8">Start automating your sales follow-ups in minutes</p>

        <form onSubmit={handleSignup} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                Your Name
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">👤</span>
                <input
                  type="text"
                  placeholder="John Smith"
                  value={ownerName}
                  onChange={(e) => setOwnerName(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                  required
                />
              </div>
            </div>

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
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                  required
                />
              </div>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
              Business Name
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🏢</span>
              <input
                type="text"
                placeholder="Bright Smiles Dental"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
              Industry
            </label>
            <div className="relative">
              <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🏷</span>
              <select
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all appearance-none cursor-pointer"
              >
                <option value="Dental Clinic" className="bg-[#131929]">Dental Clinic</option>
                <option value="Medical Clinic" className="bg-[#131929]">Medical Clinic</option>
                <option value="Salon & Spa" className="bg-[#131929]">Salon &amp; Spa</option>
                <option value="Law Firm" className="bg-[#131929]">Law Firm</option>
                <option value="Real Estate" className="bg-[#131929]">Real Estate</option>
                <option value="Fitness & Gym" className="bg-[#131929]">Fitness &amp; Gym</option>
                <option value="Other" className="bg-[#131929]">Other</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="Min 8 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-12 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
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
              {password && (
                <div className="mt-2">
                  <div className="h-1 w-full bg-white/[0.08] rounded-full overflow-hidden">
                    <div className={`h-full ${strengthColors[score]} transition-all duration-300`} style={{ width: `${(score / 5) * 100}%` }} />
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-[10px] text-[#7b8aa8]">Password strength</span>
                    <span className="text-[10px] font-semibold text-[#aab4cb]">{strengthLabels[score]}</span>
                  </div>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                Confirm Password
              </label>
              <div className="relative">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500">🔒</span>
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Repeat password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-12 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] focus:ring-2 focus:ring-[#5d7ef0]/20 transition-all"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors"
                >
                  {showConfirmPassword ? "🙈" : "👁"}
                </button>
              </div>
            </div>
          </div>

          <div className="flex items-start gap-2 pt-2">
            <input
              type="checkbox"
              id="terms"
              checked={termsAccepted}
              onChange={(e) => setTermsAccepted(e.target.checked)}
              className="mt-1 rounded border-white/[0.08] bg-white/[0.06] text-[#5d7ef0] focus:ring-[#5d7ef0]/20 cursor-pointer"
            />
            <label htmlFor="terms" className="text-xs text-[#7b8aa8] leading-normal cursor-pointer select-none">
              I agree to the{" "}
              <a href="#" className="font-semibold text-[#5d7ef0] hover:text-[#7c9cf8]">
                Terms of Service
              </a>{" "}
              and{" "}
              <a href="#" className="font-semibold text-[#5d7ef0] hover:text-[#7c9cf8]">
                Privacy Policy
              </a>
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-[#5d7ef0] to-[#7c5cf6] text-white font-semibold text-sm hover:opacity-90 active:scale-[0.98] shadow-lg shadow-[#5d7ef0]/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <div className="flex items-center my-5">
          <div className="flex-1 h-px bg-white/[0.08]" />
          <span className="text-xs text-[#7b8aa8] px-3">Already have an account?</span>
          <div className="flex-1 h-px bg-white/[0.08]" />
        </div>

        <p className="text-center text-sm text-[#7b8aa8]">
          <Link href="/login" className="font-semibold text-[#5d7ef0] hover:text-[#7c9cf8] transition-colors">
            ← Sign in instead
          </Link>
        </p>
      </div>
    </div>
  );
}

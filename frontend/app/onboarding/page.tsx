"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth-provider";
import { apiFetch } from "@/lib/api";
import toast from "react-hot-toast";

interface KBItemInput {
  category: string;
  question: string;
  answer: string;
}

export default function OnboardingPage() {
  const { user, refetchUser } = useAuth();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const [businessName, setBusinessName] = useState(user?.business_name || "");
  const [industry, setIndustry] = useState(user?.industry || "");
  const [ownerName, setOwnerName] = useState(user?.name || "");

  // Auth data loads asynchronously; keep the form in sync with it on the
  // first authenticated render instead of validating stale empty state.
  useEffect(() => {
    if (!user) return;
    setBusinessName(user.business_name || "");
    setIndustry(user.industry || "");
    setOwnerName(user.name || "");
  }, [user]);

  // KB inputs
  const [kbEntries, setKbEntries] = useState<KBItemInput[]>([
    { category: "services", question: "", answer: "" },
    { category: "pricing", question: "", answer: "" },
    { category: "faqs", question: "", answer: "" },
    { category: "policies", question: "", answer: "" },
  ]);

  const handleKBChange = (index: number, field: keyof KBItemInput, value: string) => {
    const updated = [...kbEntries];
    updated[index][field] = value;
    setKbEntries(updated);
  };

  const addKBEntry = () => {
    setKbEntries([...kbEntries, { category: "faqs", question: "", answer: "" }]);
  };

  const removeKBEntry = (index: number) => {
    if (kbEntries.length <= 4) {
      toast.error("Keep at least one entry for each category.");
      return;
    }
    setKbEntries(kbEntries.filter((_, i) => i !== index));
  };

  const handleNextStep = async () => {
    if (step === 1) {
      if (!businessName.trim() || !industry.trim() || !ownerName.trim()) {
        toast.error("Please complete your business profile.");
        return;
      }
      setLoading(true);
      try {
        await apiFetch("/api/v1/business/profile", {
          method: "PUT",
          body: JSON.stringify({ name: businessName, industry, owner_name: ownerName }),
        });
      } catch (err: any) {
        toast.error(err.message || "Unable to save your business profile.");
        return;
      } finally {
        setLoading(false);
      }
      setStep(2);
    }
  };

  const handleFinishOnboarding = async () => {
    // Require the four core categories so the agent has useful business context.
    const missingCategories = ["services", "pricing", "faqs", "policies"].filter(
      (category) => !kbEntries.some((entry) => entry.category === category && entry.answer.trim())
    );
    if (missingCategories.length) {
      toast.error(`Add at least one completed entry for: ${missingCategories.join(", ")}.`);
      return;
    }
    for (let i = 0; i < kbEntries.length; i++) {
      if (!kbEntries[i].question.trim() || !kbEntries[i].answer.trim()) {
        toast.error(`Please complete entry #${i + 1}`);
        return;
      }
    }

    setLoading(true);
    try {
      // Send posts
      for (const entry of kbEntries) {
        await apiFetch("/api/v1/knowledge", {
          method: "POST",
          body: JSON.stringify({
            category: entry.category,
            question: entry.question,
            answer: entry.answer,
            extra_data: {}
          })
        });
      }

      toast.success("Knowledge Base successfully configured!");
      
      setStep(3);
    } catch (err: any) {
      toast.error(err.message || "Failed to create knowledge base entries.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoToDashboard = async () => {
    setLoading(true);
    try {
      await apiFetch("/api/v1/business/onboarding/complete", { method: "POST" });
      await refetchUser();
      router.replace("/dashboard");
    } catch (err: any) {
      toast.error(err.message || "Unable to complete onboarding.");
    } finally { setLoading(false); }
  };

  if (!user) return null;

  return (
    <div className="relative min-h-screen flex items-center justify-center p-4 bg-[#070b14] overflow-hidden">
      {/* Background orbs */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(65,105,225,0.15)] blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] rounded-full bg-[rgba(93,126,240,0.1)] blur-[120px] pointer-events-none" />

      <div className="w-full max-w-2xl bg-white/[0.03] border border-white/[0.08] rounded-2xl p-8 backdrop-blur-md shadow-2xl">
        {/* Step Indicator */}
        <div className="flex items-center justify-between mb-8 pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#5d7ef0] to-[#8b5cf6] flex items-center justify-center font-extrabold text-sm shadow-[0_0_15px_rgba(93,126,240,0.3)]">
              F
            </div>
            <span className="font-bold text-sm text-[#7b8aa8]">Followly Onboarding</span>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3].map((s) => (
              <div
                key={s}
                className={`h-1.5 w-10 rounded-full transition-all ${
                  step >= s ? "bg-[#5d7ef0]" : "bg-white/[0.08]"
                }`}
              />
            ))}
          </div>
        </div>

        {/* Step 1: Confirm Business Profile */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold mb-2">Welcome to Followly!</h2>
              <p className="text-sm text-[#7b8aa8]">Let's confirm your business details before getting started.</p>
            </div>

            <div className="space-y-4 bg-white/[0.02] p-5 rounded-xl border border-white/[0.05]">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="block text-[11px] font-bold text-[#7b8aa8] uppercase">Account Owner</span>
                  <input value={ownerName} onChange={(e) => setOwnerName(e.target.value)} className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg py-2 px-3 text-sm text-white" />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-[#7b8aa8] uppercase">Email Address</span>
                  <span className="text-sm font-semibold">{user.email}</span>
                </div>
              </div>
              <hr className="border-white/[0.05]" />
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="block text-[11px] font-bold text-[#7b8aa8] uppercase">Business Name</span>
                  <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg py-2 px-3 text-sm text-white" />
                </div>
                <div>
                  <span className="block text-[11px] font-bold text-[#7b8aa8] uppercase">Industry</span>
                  <select value={industry} onChange={(e) => setIndustry(e.target.value)} className="w-full bg-[#131929] border border-white/[0.08] rounded-lg py-2 px-3 text-sm text-white">
                    <option>Dental Clinic</option><option>Medical Clinic</option><option>Salon &amp; Spa</option><option>Law Firm</option><option>Real Estate</option><option>Fitness &amp; Gym</option><option>Other</option>
                  </select>
                </div>
              </div>
            </div>

            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <p className="text-xs text-amber-300 leading-relaxed">
                <strong>Important:</strong> To ensure your AI assistant answers accurately and does not generate incorrect pricing, you must seed your Knowledge Base with at least 3 initial business details before going live.
              </p>
            </div>

            <button
              onClick={handleNextStep}
              className="w-full py-3 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
            >
              {loading ? "Saving..." : "Continue to Knowledge Base Setup →"}
            </button>
          </div>
        )}

        {/* Step 2: Configure first 3 KB entries */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold mb-2">Build Your AI's Brain</h2>
              <p className="text-sm text-[#7b8aa8]">Add the information your AI should use when answering customers. You can add more entries or manage them later from Knowledge Base.</p>
            </div>

            <div className="space-y-5 max-h-[400px] overflow-y-auto pr-1">
              {kbEntries.map((entry, index) => (
                <div key={index} className="space-y-3 bg-white/[0.02] p-5 rounded-xl border border-white/[0.05]">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-[#5d7ef0] uppercase tracking-wide">Entry #{index + 1}</span>
                    <button type="button" onClick={() => removeKBEntry(index)} className="text-xs text-red-400 hover:text-red-300">Remove</button>
                  </div>

                  <select value={entry.category} onChange={(e) => handleKBChange(index, "category", e.target.value)} className="w-full bg-[#131929] border border-white/[0.08] rounded-lg py-2 px-3 text-xs text-white">
                    <option value="services">Services</option><option value="pricing">Pricing</option><option value="faqs">FAQs</option><option value="policies">Policies</option>
                  </select>

                  <div>
                    <label className="block text-[10px] font-bold text-[#7b8aa8] uppercase mb-1">
                      Common Question / FAQ
                    </label>
                    <input
                      type="text"
                      value={entry.question}
                      onChange={(e) => handleKBChange(index, "question", e.target.value)}
                      className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg py-2 px-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0]"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-[#7b8aa8] uppercase mb-1">
                      AI Response / Truth
                    </label>
                    <textarea
                      value={entry.answer}
                      onChange={(e) => handleKBChange(index, "answer", e.target.value)}
                      rows={2}
                      className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg py-2 px-3 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] resize-none"
                      required
                    />
                  </div>
                </div>
              ))}
            </div>

            <button type="button" onClick={addKBEntry} className="w-full py-2.5 rounded-xl border border-dashed border-white/[0.15] text-xs font-semibold text-[#aab4cb] hover:text-white hover:border-[#5d7ef0]">+ Add another entry</button>

            <button
              onClick={handleFinishOnboarding}
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-[#5d7ef0] to-[#8b5cf6] text-white font-semibold text-sm hover:opacity-90 transition-all disabled:opacity-50"
            >
              {loading ? "Saving entries..." : "Activate AI Assistant & Continue"}
            </button>
          </div>
        )}

        {/* Step 3: AI is live */}
        {step === 3 && (
          <div className="space-y-6 text-center py-6">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 animate-bounce">
              ✓
            </div>
            <div>
              <h2 className="text-xl font-bold mb-2">Your AI Agent Is Ready to Activate</h2>
              <p className="text-sm text-[#7b8aa8] max-w-md mx-auto">
                Your business profile and knowledge base are configured. Connect your channels before sending real customer conversations.
              </p>
            </div>

            <button
              onClick={handleGoToDashboard}
              className="w-full py-3 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
            >
              {loading ? "Activating..." : "Finish Setup & Go to Dashboard →"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

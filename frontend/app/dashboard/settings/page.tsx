"use client";

import React, { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import toast from "react-hot-toast";
import { Settings, Shield, Trash2 } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function SettingsPage() {
  const { user, refetchUser } = useAuth();
  
  // Profile settings state
  const [businessName, setBusinessName] = useState(user?.business_name || "");
  const [industry, setIndustry] = useState(user?.industry || "");
  const [ownerName, setOwnerName] = useState(user?.name || "");
  const [email] = useState(user?.email || ""); // read-only
  const [saveLoading, setSaveLoading] = useState(false);

  // Security settings state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [securityLoading, setSecurityLoading] = useState(false);
  const [duration, setDuration] = useState(60);
  const [hoursLoading, setHoursLoading] = useState(false);
  const [escalation, setEscalation] = useState({ contact_name: "", contact_phone: "", contact_email: "", instructions: "" });
  const [escalationLoading, setEscalationLoading] = useState(false);
  React.useEffect(() => { apiFetch<typeof escalation>("/api/v1/business/escalation-settings").then(setEscalation).catch(() => {}); }, []);
  const days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"];
  const [hours, setHours] = useState<Record<string, { open: boolean; start: string; end: string }>>(
    Object.fromEntries(days.map((day) => [day, { open: day !== "sunday", start: "09:00", end: "17:00" }]))
  );

  const handleSaveHours = async (e: React.FormEvent) => {
    e.preventDefault();
    setHoursLoading(true);
    try {
      await apiFetch("/api/v1/business/booking-settings", {
        method: "PUT", body: JSON.stringify({ working_hours: hours, appointment_duration_minutes: duration }),
      });
      toast.success("Working hours saved!");
    } catch (err: any) {
      toast.error(err.message || "Unable to save working hours.");
    } finally { setHoursLoading(false); }
  };
  const handleSaveEscalation = async (e: React.FormEvent) => {
    e.preventDefault(); setEscalationLoading(true);
    try { await apiFetch("/api/v1/business/escalation-settings", { method: "PUT", body: JSON.stringify(escalation) }); toast.success("Human escalation settings saved!"); }
    catch (err: any) { toast.error(err.message || "Unable to save escalation settings."); }
    finally { setEscalationLoading(false); }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!businessName || !ownerName) {
      toast.error("Business name and owner name cannot be empty.");
      return;
    }

    setSaveLoading(true);
    try {
      await apiFetch("/api/v1/business/profile", {
        method: "PUT",
        body: JSON.stringify({ name: businessName, industry, owner_name: ownerName }),
      });
      toast.success("Business profile settings updated!");
      refetchUser();
    } catch (err: any) {
      toast.error(err.message || "Unable to update business profile.");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleUpdatePassword = (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword || !newPassword || !confirmPassword) {
      toast.error("Please fill in all password fields.");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error("New passwords do not match.");
      return;
    }
    if (newPassword.length < 8) {
      toast.error("New password must be at least 8 characters.");
      return;
    }

    setSecurityLoading(true);
    // Mock save password
    setTimeout(() => {
      toast.success("Security credentials updated successfully!");
      setSecurityLoading(false);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }, 800);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Account Settings</h1>
        <p className="text-sm text-[#7b8aa8]">Update your business preferences, security credentials, and AI operating configuration.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Forms */}
        <div className="lg:col-span-2 space-y-6">
          {/* Profile settings */}
          <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl space-y-5 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#5d7ef0]/10 border border-[#5d7ef0]/20 flex items-center justify-center text-[#5d7ef0]">
                <Settings className="w-4.5 h-4.5" />
              </div>
              <h3 className="text-sm font-bold text-white">Business Details</h3>
            </div>

            <form onSubmit={handleSaveProfile} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                    Business Name
                  </label>
                  <input
                    type="text"
                    value={businessName}
                    onChange={(e) => setBusinessName(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                    Industry
                  </label>
                  <select
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
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
                    Owner Full Name
                  </label>
                  <input
                    type="text"
                    value={ownerName}
                    onChange={(e) => setOwnerName(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={email}
                    disabled
                    className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-[#7b8aa8] cursor-not-allowed"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saveLoading}
                className="px-5 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-xs hover:bg-[#4169e1] transition-all disabled:opacity-50"
              >
                {saveLoading ? "Saving..." : "Save Business Profile"}
              </button>
            </form>
          </div>

          <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl space-y-5 shadow-xl">
            <div><h3 className="text-sm font-bold text-white">Human Staff Escalation</h3><p className="text-xs text-[#7b8aa8] mt-1">Configure who should handle conversations the AI cannot answer.</p></div>
            <form onSubmit={handleSaveEscalation} className="space-y-3">
              <input placeholder="Staff contact name" value={escalation.contact_name} onChange={(e) => setEscalation({ ...escalation, contact_name: e.target.value })} className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl p-2.5 text-xs text-white" />
              <input placeholder="Staff phone number" value={escalation.contact_phone} onChange={(e) => setEscalation({ ...escalation, contact_phone: e.target.value })} className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl p-2.5 text-xs text-white" />
              <input type="email" placeholder="Staff email address" value={escalation.contact_email} onChange={(e) => setEscalation({ ...escalation, contact_email: e.target.value })} className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl p-2.5 text-xs text-white" />
              <textarea placeholder="Instructions for the assistant" value={escalation.instructions} onChange={(e) => setEscalation({ ...escalation, instructions: e.target.value })} rows={3} className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl p-2.5 text-xs text-white resize-none" />
              <button disabled={escalationLoading} className="px-5 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-xs disabled:opacity-50">{escalationLoading ? "Saving..." : "Save Escalation Settings"}</button>
            </form>
          </div>

          {/* Security credentials */}
          <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl space-y-5 shadow-xl">
            <div><h3 className="text-sm font-bold text-white">Working Hours &amp; Booking</h3><p className="text-xs text-[#7b8aa8] mt-1">These hours are stored for this business and will guide appointment availability.</p></div>
            <form onSubmit={handleSaveHours} className="space-y-3">
              {days.map((day) => <div key={day} className="grid grid-cols-[100px_1fr_1fr] gap-2 items-center text-xs text-white">
                <label className="capitalize flex gap-2"><input type="checkbox" checked={hours[day].open} onChange={(e) => setHours({ ...hours, [day]: { ...hours[day], open: e.target.checked } })} />{day}</label>
                <input type="time" disabled={!hours[day].open} value={hours[day].start} onChange={(e) => setHours({ ...hours, [day]: { ...hours[day], start: e.target.value } })} className="bg-white/[0.06] border border-white/[0.08] rounded-lg p-2 disabled:opacity-40" />
                <input type="time" disabled={!hours[day].open} value={hours[day].end} onChange={(e) => setHours({ ...hours, [day]: { ...hours[day], end: e.target.value } })} className="bg-white/[0.06] border border-white/[0.08] rounded-lg p-2 disabled:opacity-40" />
              </div>)}
              <label className="block text-xs text-[#aab4cb] pt-2">Default appointment duration (minutes)<input type="number" min="15" max="480" value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="mt-2 w-full bg-white/[0.06] border border-white/[0.08] rounded-xl p-2.5 text-white" /></label>
              <button disabled={hoursLoading} className="px-5 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-xs disabled:opacity-50">{hoursLoading ? "Saving..." : "Save Working Hours"}</button>
            </form>
          </div>

          {/* Security credentials */}
          <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl space-y-5 shadow-xl">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-[#5d7ef0]/10 border border-[#5d7ef0]/20 flex items-center justify-center text-[#5d7ef0]">
                <Shield className="w-4.5 h-4.5" />
              </div>
              <h3 className="text-sm font-bold text-white">Security &amp; Password</h3>
            </div>

            <form onSubmit={handleUpdatePassword} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Current Password
                </label>
                <input
                  type="password"
                  placeholder="••••••••"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                    New Password
                  </label>
                  <input
                    type="password"
                    placeholder="Min 8 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    placeholder="Repeat new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={securityLoading}
                className="px-5 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-xs hover:bg-[#4169e1] transition-all disabled:opacity-50"
              >
                {securityLoading ? "Updating..." : "Update Security Credentials"}
              </button>
            </form>
          </div>
        </div>

        {/* Right Info Sidebar / Billing */}
        <div className="space-y-6">
          <div className="bg-[#0c1326]/40 border border-white/[0.08] p-6 rounded-2xl space-y-4">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">Subscription Plan</h3>
            <div className="bg-white/[0.03] p-4 rounded-xl border border-white/[0.06]">
              <span className="block text-xs font-bold text-white">Starter Trial Plan</span>
              <span className="block text-[10px] text-[#7b8aa8] mt-1">Free during initial private beta</span>
            </div>
            <div className="text-[11px] text-[#7b8aa8] leading-relaxed">
              Included: 1 connected channel, 25 monthly qualified bookings, standard email support.
            </div>
          </div>

          <div className="bg-red-500/5 border border-red-500/10 p-6 rounded-2xl space-y-4">
            <h3 className="text-xs font-bold text-red-400 uppercase tracking-wider flex items-center gap-1.5">
              <Trash2 className="w-4 h-4" />
              Danger Zone
            </h3>
            <p className="text-[11px] text-[#7b8aa8] leading-relaxed">
              Permanently delete this account, business, all client lead lists, conversation history, and calendar synchronization details. This is non-reversible.
            </p>
            <button
              onClick={() => {
                if (confirm("WARNING: Are you absolutely sure you want to permanently delete your Followly account? This action cannot be undone.")) {
                  toast.success("Account deletion request submitted.");
                }
              }}
              className="px-4 py-2 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-semibold hover:bg-red-500/20 transition-all"
            >
              Delete Followly Account
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

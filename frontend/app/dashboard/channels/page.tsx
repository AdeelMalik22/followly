"use client";

import React, { useState } from "react";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/api";
import { MessageSquare, Calendar, Code, Copy, Check, ShieldCheck, ArrowRight, CircleAlert } from "lucide-react";

export default function ChannelsPage() {
  const [copied, setCopied] = useState(false);
  const [whatsappConnected, setWhatsappConnected] = useState(false);
  const [calendarConnected, setCalendarConnected] = useState(false);
  const [phoneNumberId, setPhoneNumberId] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [whatsappLoading, setWhatsappLoading] = useState(false);
  const [showAdvancedWhatsapp, setShowAdvancedWhatsapp] = useState(false);
  const [calendarLoading, setCalendarLoading] = useState(false);
  const [calendarSetupError, setCalendarSetupError] = useState(() => (
    typeof window !== "undefined" && new URLSearchParams(window.location.search).get("calendar") === "error"
      ? "Google could not complete the connection. Please try again or contact your workspace administrator."
      : ""
  ));

  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("calendar") === "connected") {
      toast.success("Google Calendar connected successfully.");
    }
    apiFetch<{ connected: boolean }>("/api/v1/calendar/status")
      .then((data) => setCalendarConnected(data.connected))
      .catch((err) => toast.error(err.message || "Unable to load calendar status."));
    apiFetch<{ connected: boolean; phone_number_id?: string }>("/api/v1/whatsapp/status")
      .then((data) => {
        setWhatsappConnected(data.connected);
        setPhoneNumberId(data.phone_number_id || "");
      })
      .catch((err) => toast.error(err.message || "Unable to load WhatsApp status."));
  }, []);

  const saveWhatsApp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumberId.trim() || !accessToken.trim()) {
      toast.error("Enter both the Phone Number ID and access token.");
      return;
    }
    setWhatsappLoading(true);
    try {
      await apiFetch("/api/v1/whatsapp/credentials", {
        method: "PUT",
        body: JSON.stringify({ phone_number_id: phoneNumberId.trim(), access_token: accessToken.trim() }),
      });
      setWhatsappConnected(true);
      setAccessToken("");
      toast.success("WhatsApp connected successfully.");
    } catch (err) { toast.error(err instanceof Error ? err.message : "Unable to connect WhatsApp."); }
    finally { setWhatsappLoading(false); }
  };

  const disconnectWhatsApp = async () => {
    try {
      await apiFetch("/api/v1/whatsapp/credentials", { method: "DELETE" });
      setWhatsappConnected(false);
      setPhoneNumberId("");
      toast.success("WhatsApp disconnected.");
    } catch (err) { toast.error(err instanceof Error ? err.message : "Unable to disconnect WhatsApp."); }
  };

  const [widgetEmbedCode, setWidgetEmbedCode] = useState("");
  React.useEffect(() => {
    apiFetch<{ widget_key: string; embed_code: string }>("/api/v1/business/widget-config")
      .then((data) => setWidgetEmbedCode(data.embed_code))
      .catch((err) => toast.error(err.message || "Unable to load widget configuration."));
  }, []);
  const embedCode = widgetEmbedCode || "Loading your business widget configuration...";

  const handleCopy = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    toast.success("Embed code copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mx-auto max-w-[1500px] space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Channels &amp; Integrations</h1>
        <p className="text-sm text-[#7e8aa1]">Connect your favorite tools to streamline your customer workflow.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* WhatsApp Integration */}
        <div className="flex flex-col justify-between space-y-6 rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <div className="space-y-3">
            <div className="flex justify-between items-start">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-emerald-100 bg-emerald-50 text-emerald-600">
                <MessageSquare className="w-5 h-5" />
              </div>
              <span
                className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                  whatsappConnected
                    ? "border-emerald-100 bg-emerald-50 text-emerald-700"
                    : "border-[#e7ecf4] bg-[#f7f9fc] text-[#7e8aa1]"
                }`}
              >
                {whatsappConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div>
              <h3 className="mb-1 text-sm font-bold text-[#34415d]">WhatsApp Business API</h3>
              <p className="text-xs leading-relaxed text-[#7e8aa1]">
                Connect your business phone number to automate appointment booking and qualification follow-ups on WhatsApp.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {whatsappConnected && (
              <div className="space-y-1 rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] p-3">
                <span className="block text-[9px] font-bold uppercase text-[#8b97ab]">Webhook URL</span>
                <span className="block break-all text-[11px] font-semibold text-[#53617a]">
                  https://api.followly.ai/api/v1/whatsapp/webhook
                </span>
              </div>
            )}

            {!whatsappConnected ? <div className="space-y-3">
              <div className="rounded-xl border border-blue-100 bg-blue-50 p-3 text-xs leading-5 text-blue-800">
                Followly normally connects WhatsApp for you through Meta. If your workspace was provisioned with credentials, use the manual setup below.
              </div>
              <button type="button" onClick={() => setShowAdvancedWhatsapp(!showAdvancedWhatsapp)} className="text-xs font-semibold text-[#3678f6] hover:text-[#1764db]">
                {showAdvancedWhatsapp ? "Hide manual setup" : "Advanced manual setup"}
              </button>
              {showAdvancedWhatsapp && <form onSubmit={saveWhatsApp} className="space-y-3 rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] p-3">
                <p className="text-[10px] leading-4 text-[#7e8aa1]">These values come from Meta Business Manager and are intended for workspace administrators.</p>
                <input value={phoneNumberId} onChange={(e) => setPhoneNumberId(e.target.value)} placeholder="Meta Phone Number ID" className="w-full rounded-xl border border-[#dfe6f1] bg-white px-3 py-2.5 text-xs text-[#34415d]" />
                <input type="password" value={accessToken} onChange={(e) => setAccessToken(e.target.value)} placeholder="Meta access token" className="w-full rounded-xl border border-[#dfe6f1] bg-white px-3 py-2.5 text-xs text-[#34415d]" />
                <button disabled={whatsappLoading} className="w-full rounded-xl bg-[#3678f6] py-2.5 text-xs font-semibold text-white disabled:opacity-50">{whatsappLoading ? "Connecting..." : "Save WhatsApp connection"}</button>
              </form>}
            </div> : <button
              onClick={disconnectWhatsApp}
              className="w-full rounded-xl border border-red-100 bg-red-50 py-2.5 text-xs font-semibold text-red-600 hover:bg-red-100"
            >
              Disconnect WhatsApp
            </button>}
          </div>
        </div>

        {/* Google Calendar Integration */}
        <div className="flex flex-col justify-between space-y-6 rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <div className="space-y-3">
            <div className="flex justify-between items-start">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-blue-100 bg-blue-50 text-blue-600">
                <Calendar className="w-5 h-5" />
              </div>
              <span
                className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                  calendarConnected
                    ? "border-emerald-100 bg-emerald-50 text-emerald-700"
                    : "border-[#e7ecf4] bg-[#f7f9fc] text-[#7e8aa1]"
                }`}
              >
                {calendarConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div>
              <h3 className="mb-1 text-sm font-bold text-[#34415d]">Google Calendar</h3>
              <p className="text-xs leading-relaxed text-[#7e8aa1]">
                Connect your team calendar. The AI scheduler checks availability, avoids double bookings, and books directly into your calendar.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {!calendarConnected && (
              <div className="space-y-3 rounded-xl border border-blue-100 bg-blue-50 p-4">
                <div className="flex items-start gap-3">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />
                  <div>
                    <p className="text-xs font-bold text-blue-900">Followly handles the setup</p>
                    <p className="mt-1 text-[11px] leading-5 text-blue-800">
                      You will be taken to Google for a secure permission check. You do not need to create a Google Cloud project or copy any technical settings.
                    </p>
                  </div>
                </div>
                {calendarSetupError && (
                  <div className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-[11px] leading-5 text-amber-900">
                    <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" />
                    <span>{calendarSetupError}</span>
                  </div>
                )}
              </div>
            )}

            {calendarConnected && (
              <div className="space-y-1 rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] p-3">
                <span className="block text-[9px] font-bold uppercase text-[#8b97ab]">Connected Calendar</span>
                <span className="block text-[11px] font-semibold text-[#53617a]">
                  appointments@brightsmiles.com
                </span>
              </div>
            )}

            <button
              disabled={calendarLoading}
              onClick={async () => {
                setCalendarLoading(true);
                setCalendarSetupError("");
                try {
                  if (calendarConnected) {
                    await apiFetch("/api/v1/calendar/disconnect", { method: "DELETE" });
                    setCalendarConnected(false);
                    toast.success("Google Calendar disconnected.");
                  } else {
                    const data = await apiFetch<{ authorization_url: string }>("/api/v1/calendar/connect");
                    window.location.href = data.authorization_url;
                  }
                } catch (err) {
                  const message = err instanceof Error ? err.message : "Unable to update calendar connection.";
                  setCalendarSetupError(message.includes("not configured") || message.includes("403")
                    ? "Google Calendar is being prepared by Followly. Please contact support to finish enabling this connection."
                    : message);
                  toast.error("Unable to connect Google Calendar.");
                } finally {
                  setCalendarLoading(false);
                }
              }}
              className={`flex w-full items-center justify-center gap-2 rounded-xl py-2.5 text-xs font-semibold transition-all disabled:cursor-wait disabled:opacity-60 ${
                calendarConnected
                  ? "border border-red-100 bg-red-50 text-red-600 hover:bg-red-100"
                  : "bg-[#3678f6] text-white hover:bg-[#2568e4]"
              }`}
            >
                  {calendarLoading ? "Opening Google..." : calendarConnected ? "Disconnect Calendar" : <>Connect Google Calendar <ArrowRight className="h-3.5 w-3.5" /></>}
            </button>
          </div>
        </div>
      </div>

      {/* Website Chat Widget Embed */}
      <div className="space-y-5 rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-violet-100 bg-violet-50 text-violet-600">
            <Code className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#34415d]">Website Chat Widget</h3>
            <p className="text-xs text-[#7e8aa1]">Add a branded AI chat widget to your website.</p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl border border-[#e7ecf4] bg-[#17213b] p-4 pr-12 font-mono text-xs text-blue-100">
              {embedCode}
            </pre>
            <button
              onClick={handleCopy}
              className="absolute right-3 top-3 rounded-lg border border-white/10 bg-white/10 p-2 text-blue-100 hover:bg-white/20"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[10px] text-[#8b97ab]">
            <span>Place this code snippet before the closing </span>
            <code className="font-semibold text-[#3678f6]">&lt;/body&gt;</code>
            <span> tag on your website pages.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState } from "react";
import toast from "react-hot-toast";
import { MessageSquare, Calendar, Code, Copy, Check, ExternalLink } from "lucide-react";

export default function ChannelsPage() {
  const [copied, setCopied] = useState(false);
  const [whatsappConnected, setWhatsappConnected] = useState(false);
  const [calendarConnected, setCalendarConnected] = useState(false);

  const embedCode = `<script src="https://cdn.followly.ai/widget.js" data-business-id="1" defer></script>`;

  const handleCopy = () => {
    navigator.clipboard.writeText(embedCode);
    setCopied(true);
    toast.success("Embed code copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Integrations &amp; Channels</h1>
        <p className="text-sm text-[#7b8aa8]">Connect Followly to your customer messaging channels and booking calendars.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* WhatsApp Integration */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between items-start">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <MessageSquare className="w-5 h-5" />
              </div>
              <span
                className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                  whatsappConnected
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-white/[0.06] text-[#aab4cb] border-white/[0.08]"
                }`}
              >
                {whatsappConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-bold text-white mb-1">WhatsApp Business API</h3>
              <p className="text-xs text-[#7b8aa8] leading-relaxed">
                Connect your business phone number to automate appointment booking and qualification follow-ups on WhatsApp.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {whatsappConnected && (
              <div className="bg-white/[0.03] p-3 rounded-xl border border-white/[0.06] space-y-1">
                <span className="block text-[9px] font-bold text-[#7b8aa8] uppercase">Webhook URL</span>
                <span className="block text-[11px] font-semibold text-white break-all">
                  https://api.followly.ai/webhook/whatsapp/1
                </span>
              </div>
            )}

            <button
              onClick={() => {
                setWhatsappConnected(!whatsappConnected);
                toast.success(whatsappConnected ? "WhatsApp disconnected." : "WhatsApp successfully connected!");
              }}
              className={`w-full py-2.5 rounded-xl font-semibold text-xs transition-all ${
                whatsappConnected
                  ? "bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20"
                  : "bg-[#5d7ef0] text-white hover:bg-[#4169e1]"
              }`}
            >
              {whatsappConnected ? "Disconnect WhatsApp" : "Connect WhatsApp Account"}
            </button>
          </div>
        </div>

        {/* Google Calendar Integration */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl flex flex-col justify-between space-y-6">
          <div className="space-y-3">
            <div className="flex justify-between items-start">
              <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                <Calendar className="w-5 h-5" />
              </div>
              <span
                className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                  calendarConnected
                    ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                    : "bg-white/[0.06] text-[#aab4cb] border-white/[0.08]"
                }`}
              >
                {calendarConnected ? "Connected" : "Disconnected"}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-bold text-white mb-1">Google Calendar</h3>
              <p className="text-xs text-[#7b8aa8] leading-relaxed">
                Connect your team calendar. The AI scheduler checks availability, avoids double bookings, and books directly into your calendar.
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {calendarConnected && (
              <div className="bg-white/[0.03] p-3 rounded-xl border border-white/[0.06] space-y-1">
                <span className="block text-[9px] font-bold text-[#7b8aa8] uppercase">Connected Calendar</span>
                <span className="block text-[11px] font-semibold text-white">
                  appointments@brightsmiles.com
                </span>
              </div>
            )}

            <button
              onClick={() => {
                setCalendarConnected(!calendarConnected);
                toast.success(calendarConnected ? "Google Calendar disconnected." : "Google Calendar successfully connected!");
              }}
              className={`w-full py-2.5 rounded-xl font-semibold text-xs transition-all ${
                calendarConnected
                  ? "bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20"
                  : "bg-[#5d7ef0] text-white hover:bg-[#4169e1]"
              }`}
            >
              {calendarConnected ? "Disconnect Calendar" : "Link Google Calendar"}
            </button>
          </div>
        </div>
      </div>

      {/* Website Chat Widget Embed */}
      <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl space-y-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
            <Code className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Website Chat Widget</h3>
            <p className="text-xs text-[#7b8aa8]">Embed a sleek, glassmorphic AI chat widget bubble directly onto your website.</p>
          </div>
        </div>

        <div className="space-y-3">
          <div className="relative">
            <pre className="bg-[#070b14] border border-white/[0.08] p-4 rounded-xl text-xs text-[#aab4cb] font-mono overflow-x-auto whitespace-pre-wrap pr-12">
              {embedCode}
            </pre>
            <button
              onClick={handleCopy}
              className="absolute right-3 top-3 p-2 rounded-lg bg-white/[0.04] border border-white/[0.08] text-[#aab4cb] hover:text-white hover:bg-white/[0.1] transition-all"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>

          <div className="flex items-center gap-1.5 text-[10px] text-[#7b8aa8]">
            <span>Place this code snippet before the closing </span>
            <code className="text-[#5d7ef0] font-semibold">&lt;/body&gt;</code>
            <span> tag on your website pages.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

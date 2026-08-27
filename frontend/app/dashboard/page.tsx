"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { AnalyticsSummary } from "@/types";
import toast from "react-hot-toast";
import { Users, PhoneCall, CheckCircle, Calendar, DollarSign, ArrowUpRight } from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  Cell
} from "recharts";

export default function DashboardOverviewPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<AnalyticsSummary>("/api/v1/analytics/summary", {
        params: { days },
      });
      setSummary(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load analytics summary.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [days]);

  if (loading || !summary) {
    return (
      <div className="py-20 flex flex-col items-center justify-center">
        <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin mb-4" />
        <span className="text-xs text-[#7b8aa8]">Loading analytics summary...</span>
      </div>
    );
  }

  // Estimated Revenue Calculation
  // We assume an average contract value (ACV) of $150 per booked appointment.
  const estimatedRevenue = summary.funnel.booked * 150;

  // Funnel steps data
  const funnelData = [
    { name: "Total Leads", count: summary.funnel.total_leads, fill: "#7c5cf6" },
    { name: "Contacted", count: summary.funnel.contacted + summary.funnel.qualified + summary.funnel.booked, fill: "#5d7ef0" },
    { name: "Qualified", count: summary.funnel.qualified + summary.funnel.booked, fill: "#3b82f6" },
    { name: "Booked", count: summary.funnel.booked, fill: "#10b981" },
  ];

  return (
    <div className="space-y-8">
      {/* Top Banner */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Dashboard Overview</h1>
          <p className="text-sm text-[#7b8aa8]">Proof of value analytics and conversion metrics for your clinic.</p>
        </div>

        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-white/[0.05] border border-white/[0.08] rounded-xl py-2 px-3 text-xs font-semibold text-white focus:outline-none focus:border-[#5d7ef0] cursor-pointer"
        >
          <option value={7} className="bg-[#131929]">Last 7 days</option>
          <option value={30} className="bg-[#131929]">Last 30 days</option>
          <option value={90} className="bg-[#131929]">Last 90 days</option>
        </select>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Leads */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-9 h-9 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Total Leads</span>
            <span className="text-2xl font-extrabold text-white">{summary.funnel.total_leads}</span>
          </div>
        </div>

        {/* Contacted */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-9 h-9 rounded-xl bg-[#5d7ef0]/10 border border-[#5d7ef0]/20 flex items-center justify-center text-[#5d7ef0]">
              <PhoneCall className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Contacted</span>
            <span className="text-2xl font-extrabold text-white">
              {summary.funnel.contacted + summary.funnel.qualified + summary.funnel.booked}
            </span>
          </div>
        </div>

        {/* Qualified */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Qualified</span>
            <span className="text-2xl font-extrabold text-white">
              {summary.funnel.qualified + summary.funnel.booked}
            </span>
          </div>
        </div>

        {/* Booked */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-5 rounded-2xl flex flex-col justify-between">
          <div className="flex justify-between items-start mb-4">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Appointments</span>
            <span className="text-2xl font-extrabold text-emerald-400">{summary.funnel.booked}</span>
          </div>
        </div>

        {/* Estimated Revenue */}
        <div className="bg-gradient-to-br from-[#0c1326] to-[#0d223c] border border-white/[0.08] p-5 rounded-2xl flex flex-col justify-between relative overflow-hidden shadow-xl">
          <div className="absolute top-0 right-0 w-24 h-24 bg-[#5d7ef0]/5 blur-xl rounded-full" />
          <div className="flex justify-between items-start mb-4">
            <div className="w-9 h-9 rounded-xl bg-yellow-500/10 border border-yellow-500/20 flex items-center justify-center text-yellow-400">
              <DollarSign className="w-4 h-4" />
            </div>
            <span className="text-[10px] font-semibold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded flex items-center gap-0.5">
              Live
              <ArrowUpRight className="w-2.5 h-2.5" />
            </span>
          </div>
          <div>
            <span className="block text-[10px] font-bold text-[#aab4cb] uppercase tracking-wider">Est. Revenue</span>
            <span className="text-2xl font-extrabold text-white">${estimatedRevenue}</span>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leads Over Time Chart */}
        <div className="lg:col-span-2 bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl">
          <h3 className="text-sm font-bold text-white mb-6">Leads Growth</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={summary.leads_over_time} margin={{ left: -20, right: 10, top: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="leadGlow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#5d7ef0" stopOpacity={0.2} />
                    <stop offset="95%" stopColor="#5d7ef0" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(str) => {
                    try {
                      const d = new Date(str);
                      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
                    } catch {
                      return str;
                    }
                  }}
                  stroke="#7b8aa8"
                  fontSize={10}
                  tickLine={false}
                />
                <YAxis stroke="#7b8aa8" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#0c1326",
                    border: "1px solid rgba(255,255,255,0.09)",
                    borderRadius: "12px",
                    color: "#e8edf7",
                    fontSize: "11px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  name="New Leads"
                  stroke="#5d7ef0"
                  strokeWidth={2}
                  activeDot={{ r: 6 }}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Funnel Conversion Chart */}
        <div className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl">
          <h3 className="text-sm font-bold text-white mb-6">Conversion Funnel</h3>
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={funnelData} layout="vertical" margin={{ left: -10, right: 10, top: 10, bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" stroke="#7b8aa8" fontSize={10} tickLine={false} />
                <YAxis dataKey="name" type="category" stroke="#7b8aa8" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    background: "#0c1326",
                    border: "1px solid rgba(255,255,255,0.09)",
                    borderRadius: "12px",
                    color: "#e8edf7",
                    fontSize: "11px",
                  }}
                />
                <Bar dataKey="count" name="Leads count" radius={[0, 8, 8, 0]}>
                  {funnelData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { Lead, LeadStatus } from "@/types";
import toast from "react-hot-toast";
import { Search, Plus, User, MessageSquare, Phone } from "lucide-react";
import Link from "next/link";

const statuses: LeadStatus[] = ["new", "contacted", "qualified", "booked", "cold", "recovered", "not_interested"];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Create lead form states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [source, setSource] = useState("manual");
  const [createLoading, setCreateLoading] = useState(false);

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Lead[]>("/api/v1/leads", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
          search: searchQuery || undefined,
        },
      });
      setLeads(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load leads.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [statusFilter, searchQuery]);

  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone && !email) {
      toast.error("Please enter either a phone number or email address.");
      return;
    }

    setCreateLoading(true);
    try {
      const created = await apiFetch<Lead>("/api/v1/leads", {
        method: "POST",
        body: JSON.stringify({ name, phone, email, source }),
      });
      setLeads([created, ...leads]);
      toast.success("Lead created successfully!");
      setIsModalOpen(false);
      setName("");
      setPhone("");
      setEmail("");
      setSource("manual");
    } catch (err: any) {
      toast.error(err.message || "Failed to create lead.");
    } finally {
      setCreateLoading(false);
    }
  };

  const handleUpdateStatus = async (leadId: number, status: LeadStatus) => {
    try {
      const updated = await apiFetch<Lead>(`/api/v1/leads/${leadId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setLeads(leads.map((l) => (l.id === leadId ? updated : l)));
      toast.success("Lead status updated.");
    } catch (err: any) {
      toast.error(err.message || "Failed to update lead status.");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Leads Management</h1>
          <p className="text-sm text-[#7b8aa8]">View, search, and manually update status for your client leads.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Lead
        </button>
      </div>

      {/* Filter and Search */}
      <div className="flex flex-col md:flex-row gap-4 justify-between items-stretch">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8aa8]" />
          <input
            type="text"
            placeholder="Search leads by name, phone, or email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-4 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0]"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-white/[0.05] border border-white/[0.08] rounded-xl py-2.5 px-4 text-xs font-semibold text-white focus:outline-none focus:border-[#5d7ef0] cursor-pointer"
        >
          <option value="all" className="bg-[#131929]">All Statuses</option>
          {statuses.map((s) => (
            <option key={s} value={s} className="bg-[#131929] capitalize">
              {s}
            </option>
          ))}
        </select>
      </div>

      {/* Leads Table */}
      {loading ? (
        <div className="py-20 flex justify-center">
          <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
        </div>
      ) : leads.length === 0 ? (
        <div className="text-center py-20 bg-white/[0.01] border border-white/[0.08] rounded-2xl">
          <User className="w-12 h-12 text-[#7b8aa8] mx-auto mb-4 opacity-50" />
          <h3 className="text-base font-bold text-white mb-1">No Leads Found</h3>
          <p className="text-xs text-[#7b8aa8] max-w-sm mx-auto mb-6">
            Import or create leads to start qualified follow-up sequences.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="px-4 py-2 rounded-xl bg-white/[0.06] border border-white/[0.08] text-white text-xs font-semibold hover:bg-white/[0.1] transition-all"
          >
            Create first lead
          </button>
        </div>
      ) : (
        <div className="bg-white/[0.01] border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.02]">
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Lead Info</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Status</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Source</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Last Contact</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Created</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-white/[0.01] transition-colors">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-[#7b8aa8]">
                          <User className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="block text-xs font-bold text-white">{lead.name || "Unknown name"}</span>
                          <span className="block text-[10px] text-[#7b8aa8]">
                            {lead.phone ? `📞 ${lead.phone}` : ""} {lead.email ? `✉ ${lead.email}` : ""}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <select
                        value={lead.status}
                        onChange={(e) => handleUpdateStatus(lead.id, e.target.value as LeadStatus)}
                        className="bg-[#0a0f1d] border border-white/[0.08] rounded-lg py-1 px-2.5 text-[10px] font-semibold text-white focus:outline-none focus:border-[#5d7ef0] cursor-pointer capitalize"
                      >
                        {statuses.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-4">
                      <span className="text-xs font-semibold text-white capitalize">{lead.source || "unknown"}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-xs text-[#7b8aa8]">
                        {lead.last_contact_at ? new Date(lead.last_contact_at).toLocaleDateString() : "Never"}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-xs text-[#7b8aa8]">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        href="/dashboard/conversations"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-white text-xs font-medium hover:bg-white/[0.1] hover:border-white/[0.15] transition-all"
                      >
                        <MessageSquare className="w-3 h-3" />
                        Chat Thread
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Lead Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-[#070b14]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0c1326] border border-white/[0.08] rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="text-lg font-bold text-white mb-4">Add Manual Lead</h2>

            <form onSubmit={handleCreateLead} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Lead Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Emily Watson"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="e.g. +14155552671"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="e.g. emily@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Lead Source
                </label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                >
                  <option value="manual" className="bg-[#131929]">Manual entry</option>
                  <option value="website" className="bg-[#131929]">Website widget</option>
                  <option value="whatsapp" className="bg-[#131929]">WhatsApp</option>
                  <option value="instagram" className="bg-[#131929]">Instagram</option>
                </select>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-xl border border-white/[0.08] text-xs font-semibold text-[#aab4cb] hover:bg-white/[0.03] transition-all"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                  className="px-4 py-2 rounded-xl bg-[#5d7ef0] text-white text-xs font-semibold hover:bg-[#4169e1] transition-all disabled:opacity-50"
                >
                  {createLoading ? "Creating..." : "Save Lead"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

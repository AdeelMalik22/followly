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
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Leads</h1>
          <p className="text-sm text-[#7e8aa1]">Manage and track all your leads in one place.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 rounded-xl bg-[#3678f6] px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-blue-200 hover:bg-[#2568e4]"
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
            className="w-full rounded-xl border border-[#dfe6f1] bg-white py-2.5 pl-10 pr-4 text-xs text-[#17213b] placeholder-[#a5afbf] outline-none focus:border-[#3678f6] focus:ring-4 focus:ring-blue-50"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-xl border border-[#dfe6f1] bg-white px-4 py-2.5 text-xs font-semibold text-[#53617a] outline-none focus:border-[#3678f6]"
        >
            <option value="all">All Statuses</option>
          {statuses.map((s) => (
              <option key={s} value={s} className="capitalize">
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
        <div className="rounded-2xl border border-[#e7ecf4] bg-white py-20 text-center shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <User className="mx-auto mb-4 h-12 w-12 text-[#9aa5b8] opacity-50" />
          <h3 className="mb-1 text-base font-bold text-[#17213b]">No leads found</h3>
          <p className="mx-auto mb-6 max-w-sm text-xs text-[#7e8aa1]">
            Import or create leads to start qualified follow-up sequences.
          </p>
          <button
            onClick={() => setIsModalOpen(true)}
            className="rounded-xl border border-[#dfe6f1] bg-white px-4 py-2 text-xs font-semibold text-[#3678f6] hover:bg-[#f4f7fc]"
          >
            Create first lead
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-[#e7ecf4] bg-white shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#eef1f6] bg-[#fbfcfe]">
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Lead Info</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Status</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Source</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Last Contact</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Created</th>
                  <th className="p-4 text-right text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eef1f6]">
                {leads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-[#fbfcfe]">
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#dfe6f1] bg-[#f4f7fc] text-[#7e8aa1]">
                          <User className="w-4 h-4" />
                        </div>
                        <div>
                          <span className="block text-xs font-bold text-[#34415d]">{lead.name || "Unknown name"}</span>
                          <span className="block text-[10px] text-[#8b97ab]">
                            {lead.phone ? `📞 ${lead.phone}` : ""} {lead.email ? `✉ ${lead.email}` : ""}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="p-4">
                      <select
                        value={lead.status}
                        onChange={(e) => handleUpdateStatus(lead.id, e.target.value as LeadStatus)}
                        className="rounded-lg border border-[#dfe6f1] bg-white px-2.5 py-1 text-[10px] font-semibold capitalize text-[#53617a] outline-none focus:border-[#3678f6]"
                      >
                        {statuses.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="p-4">
                      <span className="text-xs font-semibold capitalize text-[#53617a]">{lead.source || "unknown"}</span>
                    </td>
                    <td className="p-4">
                      <span className="text-xs text-[#8b97ab]">
                        {lead.last_contact_at ? new Date(lead.last_contact_at).toLocaleDateString() : "Never"}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-xs text-[#8b97ab]">
                        {new Date(lead.created_at).toLocaleDateString()}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <Link
                        href="/dashboard/conversations"
                        className="inline-flex items-center gap-1.5 rounded-lg border border-[#dfe6f1] bg-white px-3 py-1.5 text-xs font-medium text-[#53617a] hover:border-[#b9c9e3] hover:bg-[#f4f7fc]"
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
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#17213b]/30 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-[#e5eaf2] bg-white p-6 shadow-2xl">
            <h2 className="mb-4 text-lg font-bold text-[#17213b]">Add manual lead</h2>

            <form onSubmit={handleCreateLead} className="space-y-4">
              <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#53617a]">
                  Lead Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Emily Watson"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#3678f6]"
                />
              </div>

              <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#53617a]">
                  Phone Number
                </label>
                <input
                  type="tel"
                  placeholder="e.g. +14155552671"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#3678f6]"
                />
              </div>

              <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#53617a]">
                  Email Address
                </label>
                <input
                  type="email"
                  placeholder="e.g. emily@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#3678f6]"
                />
              </div>

              <div>
                  <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#53617a]">
                  Lead Source
                </label>
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#3678f6]"
                >
                  <option value="manual">Manual entry</option>
                  <option value="website">Website widget</option>
                  <option value="whatsapp">WhatsApp</option>
                  <option value="instagram">Instagram</option>
                </select>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                    className="rounded-xl border border-[#dfe6f1] px-4 py-2 text-xs font-semibold text-[#71809a] hover:bg-[#f4f7fc]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createLoading}
                    className="rounded-xl bg-[#3678f6] px-4 py-2 text-xs font-semibold text-white hover:bg-[#2568e4] disabled:opacity-50"
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

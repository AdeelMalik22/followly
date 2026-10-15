"use client";

import React, { useCallback, useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { Appointment } from "@/types";
import toast from "react-hot-toast";
import { Calendar, User, Clock } from "lucide-react";
import { format } from "date-fns";

const statusTabs = [
  { id: "all", name: "All Bookings" },
  { id: "scheduled", name: "Scheduled" },
  { id: "completed", name: "Completed" },
  { id: "no_show", name: "No-Show" },
  { id: "cancelled", name: "Cancelled" },
];

export default function AppointmentsPage() {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchAppointments = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Appointment[]>("/api/v1/appointments", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
        },
      });
      setAppointments(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load appointments.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    const timer = window.setTimeout(() => { void fetchAppointments(); }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchAppointments]);

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Appointments</h1>
        <p className="text-sm text-[#7e8aa1]">Manage, schedule, and track your customer meetings.</p>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto border-b border-[#e7ecf4] pb-px scrollbar-none">
        {statusTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 whitespace-nowrap transition-all ${
              statusFilter === tab.id
                ? "border-[#3678f6] text-[#1764db]"
                : "border-transparent text-[#8b97ab] hover:text-[#34415d]"
            }`}
          >
            {tab.name}
          </button>
        ))}
      </div>

      {/* Booking Table / Cards */}
      {loading ? (
        <div className="py-20 flex justify-center">
          <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
        </div>
      ) : appointments.length === 0 ? (
        <div className="rounded-2xl border border-[#e7ecf4] bg-white py-20 text-center shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <Calendar className="mx-auto mb-4 h-12 w-12 text-[#9aa5b8] opacity-50" />
          <h3 className="mb-1 text-base font-bold text-[#17213b]">No appointments found</h3>
          <p className="mx-auto max-w-sm text-xs text-[#7e8aa1]">
            When the AI scheduling agent qualifies a lead, upcoming bookings will appear here.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-[#e7ecf4] bg-white shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#eef1f6] bg-[#fbfcfe]">
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Lead / Client</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Service</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Date &amp; Time</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Status</th>
                  <th className="p-4 text-[10px] font-bold uppercase tracking-wider text-[#8b97ab]">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#eef1f6]">
                {appointments.map((appt) => {
                  let formattedDate = "";
                  let formattedTime = "";
                  try {
                    const start = new Date(appt.start_time);
                    const end = new Date(appt.end_time);
                    formattedDate = format(start, "PPP");
                    formattedTime = `${format(start, "p")} - ${format(end, "p")}`;
                  } catch {
                    formattedDate = appt.start_time;
                  }

                  return (
                    <tr key={appt.id} className="hover:bg-[#fbfcfe]">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-[#dfe6f1] bg-[#f4f7fc] text-[#7e8aa1]">
                            <User className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="block text-xs font-bold text-[#34415d]">
                              {appt.lead?.name || "Unknown"}
                            </span>
                            <span className="block text-[10px] text-[#8b97ab]">
                              {appt.lead?.phone || appt.lead?.email || "No contact"}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-xs font-semibold capitalize text-[#53617a]">
                          {appt.service || "General Consultation"}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-[#5d7ef0]" />
                          <div>
                            <span className="block text-xs font-semibold text-[#34415d]">{formattedDate}</span>
                            <span className="block text-[10px] text-[#8b97ab]">{formattedTime}</span>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`text-[9px] font-bold px-2.5 py-1 rounded-full border uppercase tracking-wider ${
                            appt.status === "scheduled"
                              ? "border-blue-100 bg-blue-50 text-blue-700"
                              : appt.status === "completed"
                              ? "border-emerald-100 bg-emerald-50 text-emerald-700"
                              : appt.status === "cancelled"
                              ? "border-red-100 bg-red-50 text-red-700"
                              : "border-[#e7ecf4] bg-[#f7f9fc] text-[#7e8aa1]"
                          }`}
                        >
                          {appt.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="text-[10px] text-[#8b97ab]">
                          {new Date(appt.created_at).toLocaleDateString()}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

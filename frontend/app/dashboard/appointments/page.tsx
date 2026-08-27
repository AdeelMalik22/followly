"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { Appointment } from "@/types";
import toast from "react-hot-toast";
import { Calendar, User, Clock, CheckCircle } from "lucide-react";
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

  const fetchAppointments = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<Appointment[]>("/api/v1/appointments", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
        },
      });
      setAppointments(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load appointments.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [statusFilter]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-extrabold text-white">Appointments</h1>
        <p className="text-sm text-[#7b8aa8]">Day-to-day operational view of bookings and appointments scheduled by the AI.</p>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 border-b border-white/[0.08] pb-px overflow-x-auto scrollbar-none">
        {statusTabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusFilter(tab.id)}
            className={`px-4 py-2.5 text-xs font-bold uppercase tracking-wider border-b-2 whitespace-nowrap transition-all ${
              statusFilter === tab.id
                ? "border-[#5d7ef0] text-white"
                : "border-transparent text-[#7b8aa8] hover:text-white"
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
        <div className="text-center py-20 bg-white/[0.01] border border-white/[0.08] rounded-2xl">
          <Calendar className="w-12 h-12 text-[#7b8aa8] mx-auto mb-4 opacity-50" />
          <h3 className="text-base font-bold text-white mb-1">No Appointments Found</h3>
          <p className="text-xs text-[#7b8aa8] max-w-sm mx-auto">
            When the AI scheduling agent qualifies a lead, upcoming bookings will appear here.
          </p>
        </div>
      ) : (
        <div className="bg-white/[0.01] border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.02]">
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Lead / Client</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Service</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Date &amp; Time</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Status</th>
                  <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
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
                    <tr key={appt.id} className="hover:bg-white/[0.01] transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-[#7b8aa8]">
                            <User className="w-4 h-4" />
                          </div>
                          <div>
                            <span className="block text-xs font-bold text-white">
                              {appt.lead?.name || "Unknown"}
                            </span>
                            <span className="block text-[10px] text-[#7b8aa8]">
                              {appt.lead?.phone || appt.lead?.email || "No contact"}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="text-xs font-semibold text-white capitalize">
                          {appt.service || "General Consultation"}
                        </span>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <Clock className="w-3.5 h-3.5 text-[#5d7ef0]" />
                          <div>
                            <span className="block text-xs font-semibold text-white">{formattedDate}</span>
                            <span className="block text-[10px] text-[#7b8aa8]">{formattedTime}</span>
                          </div>
                        </div>
                      </td>
                      <td className="p-4">
                        <span
                          className={`text-[9px] font-bold px-2.5 py-1 rounded-full border uppercase tracking-wider ${
                            appt.status === "scheduled"
                              ? "bg-blue-500/10 text-blue-400 border-blue-500/20"
                              : appt.status === "completed"
                              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                              : appt.status === "cancelled"
                              ? "bg-red-500/10 text-red-400 border-red-500/20"
                              : "bg-white/[0.06] text-[#aab4cb] border-white/[0.08]"
                          }`}
                        >
                          {appt.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="text-[10px] text-[#7b8aa8]">
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

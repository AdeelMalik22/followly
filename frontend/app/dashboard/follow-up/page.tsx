"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { FollowUpRule } from "@/types";
import toast from "react-hot-toast";
import { Plus, Edit2, Trash2, RefreshCw, AlertCircle } from "lucide-react";

export default function FollowUpRulesPage() {
  const [rules, setRules] = useState<FollowUpRule[]>([]);
  const [loading, setLoading] = useState(true);

  // Form Modal States
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [triggerCondition, setTriggerCondition] = useState("lead_created");
  const [delayHours, setDelayHours] = useState(24);
  const [messageTemplate, setMessageTemplate] = useState("");
  const [active, setActive] = useState(true);
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchRules = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<FollowUpRule[]>("/api/v1/follow-up-rules");
      setRules(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load follow-up rules.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  const openAddModal = () => {
    setEditingId(null);
    setTriggerCondition("lead_created");
    setDelayHours(24);
    setMessageTemplate("");
    setActive(true);
    setIsModalOpen(true);
  };

  const openEditModal = (rule: FollowUpRule) => {
    setEditingId(rule.id);
    setTriggerCondition(rule.trigger_condition);
    setDelayHours(rule.delay_hours);
    setMessageTemplate(rule.message_template);
    setActive(rule.active === 1);
    setIsModalOpen(true);
  };

  const handleToggleActive = async (rule: FollowUpRule) => {
    const nextActive = rule.active === 1 ? 0 : 1;
    try {
      const updated = await apiFetch<FollowUpRule>(`/api/v1/follow-up-rules/${rule.id}`, {
        method: "PUT",
        body: JSON.stringify({ active: nextActive === 1 }),
      });
      setRules(rules.map((r) => (r.id === rule.id ? updated : r)));
      toast.success(nextActive === 1 ? "Rule activated." : "Rule paused.");
    } catch (err: any) {
      toast.error(err.message || "Failed to toggle rule state.");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageTemplate.trim()) {
      toast.error("Message template cannot be empty.");
      return;
    }

    setSubmitLoading(true);
    try {
      if (editingId !== null) {
        const updated = await apiFetch<FollowUpRule>(`/api/v1/follow-up-rules/${editingId}`, {
          method: "PUT",
          body: JSON.stringify({
            trigger_condition: triggerCondition,
            delay_hours: Number(delayHours),
            message_template: messageTemplate,
            active,
          }),
        });
        setRules(rules.map((r) => (r.id === editingId ? updated : r)));
        toast.success("Follow-up rule updated!");
      } else {
        const created = await apiFetch<FollowUpRule>("/api/v1/follow-up-rules", {
          method: "POST",
          body: JSON.stringify({
            trigger_condition: triggerCondition,
            delay_hours: Number(delayHours),
            message_template: messageTemplate,
            active,
          }),
        });
        setRules([...rules, created]);
        toast.success("Follow-up rule created!");
      }
      setIsModalOpen(false);
    } catch (err: any) {
      toast.error(err.message || "Failed to save rule.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this follow-up rule?")) return;

    try {
      await apiFetch(`/api/v1/follow-up-rules/${id}`, { method: "DELETE" });
      setRules(rules.filter((r) => r.id !== id));
      toast.success("Rule deleted successfully.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete rule.");
    }
  };

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Follow-up Automation</h1>
          <p className="text-sm text-[#7e8aa1]">Create automated follow-ups to nurture leads and never miss a conversation.</p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 rounded-xl bg-[#3678f6] px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-blue-200 hover:bg-[#2568e4]"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {loading ? (
        <div className="py-20 flex justify-center">
          <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
        </div>
      ) : rules.length === 0 ? (
        <div className="rounded-2xl border border-[#e7ecf4] bg-white py-20 text-center shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <RefreshCw className="mx-auto mb-4 h-12 w-12 text-[#9aa5b8] opacity-50" />
          <h3 className="mb-1 text-base font-bold text-[#17213b]">No follow-up rules</h3>
          <p className="mx-auto mb-6 max-w-sm text-xs text-[#7e8aa1]">
            Add a follow-up cadence rule to automatically message new or cold clients after a specified delay.
          </p>
          <button
            onClick={openAddModal}
            className="rounded-xl border border-[#dfe6f1] bg-white px-4 py-2 text-xs font-semibold text-[#3678f6] hover:bg-[#f4f7fc]"
          >
            Create first rule
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="flex flex-col items-start justify-between gap-4 rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-[0_5px_20px_rgba(35,55,90,0.04)] transition hover:border-[#b9c9e3] md:flex-row md:items-center"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2">
                  <span className="rounded border border-blue-100 bg-blue-50 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-blue-700">
                    {rule.trigger_condition.replace("_", " ")}
                  </span>
                  <span className="text-xs text-[#8b97ab]">
                    Send after <strong className="text-[#53617a]">{rule.delay_hours} hours</strong>
                  </span>
                </div>
                <p className="text-xs italic leading-relaxed text-[#53617a]">
                  &ldquo;{rule.message_template}&rdquo;
                </p>
              </div>

              <div className="flex items-center gap-4 self-end md:self-center">
                <label className="relative inline-flex items-center cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={rule.active === 1}
                    onChange={() => handleToggleActive(rule)}
                    className="sr-only peer"
                  />
                  <div className="h-5 w-9 rounded-full bg-[#dfe6f1] after:absolute after:left-[2px] after:top-0.5 after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all peer-checked:bg-[#3678f6] peer-checked:after:translate-x-full" />
                  <span className="ml-2 text-xs font-bold uppercase text-[#8b97ab]">
                    {rule.active === 1 ? "Active" : "Paused"}
                  </span>
                </label>

                <div className="flex gap-2">
                  <button
                    onClick={() => openEditModal(rule)}
                    className="rounded-lg border border-[#e7ecf4] bg-white p-1.5 text-[#8b97ab] hover:bg-[#f1f6ff] hover:text-[#3678f6]"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="rounded-lg border border-[#e7ecf4] bg-white p-1.5 text-[#8b97ab] hover:bg-red-50 hover:text-red-500"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#17213b]/20 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="mb-4 text-lg font-bold text-[#17213b]">
              {editingId !== null ? "Edit Follow-up Rule" : "Create Follow-up Rule"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                  Trigger Condition
                </label>
                <select
                  value={triggerCondition}
                  onChange={(e) => setTriggerCondition(e.target.value)}
                  className="w-full rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                >
                  <option value="lead_created">New lead created</option>
                  <option value="lead_cold">Lead becomes cold (inactive for 48h)</option>
                  <option value="no_show">Appointment no-show</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                  Delay (Hours)
                </label>
                <input
                  type="number"
                  min={1}
                  max={720}
                  value={delayHours}
                  onChange={(e) => setDelayHours(Number(e.target.value))}
                  className="w-full rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                  required
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                    Message Template
                  </label>
                  <span className="flex items-center gap-1 text-[10px] text-[#8b97ab]">
                    <AlertCircle className="w-3 h-3" />
                    Use {"{lead_name}"} or {"{business_name}"}
                  </span>
                </div>
                <textarea
                  placeholder="e.g. Hi {lead_name}, we noticed you haven't booked your cleaning yet! Do you have any questions about scheduling?"
                  value={messageTemplate}
                  onChange={(e) => setMessageTemplate(e.target.value)}
                  rows={4}
                  className="w-full resize-none rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] placeholder-[#a0aabd] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                  required
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="active"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                  className="cursor-pointer rounded border-[#dfe6f1] text-[#3678f6] focus:ring-[#3678f6]/20"
                />
                <label htmlFor="active" className="cursor-pointer select-none text-xs leading-normal text-[#71809a]">
                  Enable rule immediately
                </label>
              </div>

              <div className="flex gap-3 justify-end pt-2">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-xl border border-[#e7ecf4] px-4 py-2 text-xs font-semibold text-[#71809a] transition-all hover:bg-[#f7f9fc]"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitLoading}
                  className="px-4 py-2 rounded-xl bg-[#5d7ef0] text-white text-xs font-semibold hover:bg-[#4169e1] transition-all disabled:opacity-50"
                >
                  {submitLoading ? "Saving..." : "Save Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Follow-up Rules</h1>
          <p className="text-sm text-[#7b8aa8]">Configure cadences and text message templates the AI agent uses to re-engage cold leads.</p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
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
        <div className="text-center py-20 bg-white/[0.01] border border-white/[0.08] rounded-2xl">
          <RefreshCw className="w-12 h-12 text-[#7b8aa8] mx-auto mb-4 opacity-50" />
          <h3 className="text-base font-bold text-white mb-1">No Follow-up Rules</h3>
          <p className="text-xs text-[#7b8aa8] max-w-sm mx-auto mb-6">
            Add a follow-up cadence rule to automatically message new or cold clients after a specified delay.
          </p>
          <button
            onClick={openAddModal}
            className="px-4 py-2 rounded-xl bg-white/[0.06] border border-white/[0.08] text-white text-xs font-semibold hover:bg-white/[0.1] transition-all"
          >
            Create first rule
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {rules.map((rule) => (
            <div
              key={rule.id}
              className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition-all hover:bg-white/[0.03] hover:border-white/[0.12]"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-[#5d7ef0] bg-[#5d7ef0]/10 border border-[#5d7ef0]/20 px-2 py-0.5 rounded uppercase tracking-wider">
                    {rule.trigger_condition.replace("_", " ")}
                  </span>
                  <span className="text-xs text-[#7b8aa8]">
                    Send after <strong className="text-white">{rule.delay_hours} hours</strong>
                  </span>
                </div>
                <p className="text-xs text-[#e8edf7] italic leading-relaxed">
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
                  <div className="w-9 h-5 bg-white/[0.1] rounded-full peer peer-focus:ring-0 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-[#5d7ef0]" />
                  <span className="ml-2 text-xs font-bold text-[#7b8aa8] uppercase">
                    {rule.active === 1 ? "Active" : "Paused"}
                  </span>
                </label>

                <div className="flex gap-2">
                  <button
                    onClick={() => openEditModal(rule)}
                    className="p-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-[#aab4cb] hover:text-[#5d7ef0] hover:bg-white/[0.1] transition-all"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="p-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-[#aab4cb] hover:text-red-400 hover:bg-white/[0.1] transition-all"
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
        <div className="fixed inset-0 bg-[#070b14]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#0c1326] border border-white/[0.08] rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="text-lg font-bold text-white mb-4">
              {editingId !== null ? "Edit Follow-up Rule" : "Create Follow-up Rule"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Trigger Condition
                </label>
                <select
                  value={triggerCondition}
                  onChange={(e) => setTriggerCondition(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                >
                  <option value="lead_created" className="bg-[#131929]">New lead created</option>
                  <option value="lead_cold" className="bg-[#131929]">Lead becomes cold (inactive for 48h)</option>
                  <option value="no_show" className="bg-[#131929]">Appointment no-show</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Delay (Hours)
                </label>
                <input
                  type="number"
                  min={1}
                  max={720}
                  value={delayHours}
                  onChange={(e) => setDelayHours(Number(e.target.value))}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                  required
                />
              </div>

              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="block text-xs font-semibold text-[#aab4cb] uppercase tracking-wider">
                    Message Template
                  </label>
                  <span className="text-[10px] text-[#7b8aa8] flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Use {"{lead_name}"} or {"{business_name}"}
                  </span>
                </div>
                <textarea
                  placeholder="e.g. Hi {lead_name}, we noticed you haven't booked your cleaning yet! Do you have any questions about scheduling?"
                  value={messageTemplate}
                  onChange={(e) => setMessageTemplate(e.target.value)}
                  rows={4}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] resize-none"
                  required
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="active"
                  checked={active}
                  onChange={(e) => setActive(e.target.checked)}
                  className="rounded border-white/[0.08] bg-white/[0.06] text-[#5d7ef0] focus:ring-[#5d7ef0]/20 cursor-pointer"
                />
                <label htmlFor="active" className="text-xs text-[#7b8aa8] leading-normal cursor-pointer select-none">
                  Enable rule immediately
                </label>
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

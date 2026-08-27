"use client";

import React, { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";
import { KnowledgeEntry } from "@/types";
import toast from "react-hot-toast";
import { Plus, Edit2, Trash2, BookOpen } from "lucide-react";

const categories = [
  { id: "services", name: "Services", desc: "Treatments and cleanings you offer" },
  { id: "pricing", name: "Pricing", desc: "Direct prices for treatments" },
  { id: "policies", name: "Policies", desc: "Clinic policies and appointment terms" },
  { id: "faqs", name: "FAQs", desc: "General frequently asked questions" },
];

export default function KnowledgeBasePage() {
  const [entries, setEntries] = useState<KnowledgeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeCategory, setActiveCategory] = useState("services");

  // Form states
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [category, setCategory] = useState("services");
  const [submitLoading, setSubmitLoading] = useState(false);

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const data = await apiFetch<KnowledgeEntry[]>("/api/v1/knowledge");
      setEntries(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load knowledge base.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries();
  }, []);

  const openAddModal = () => {
    setEditingId(null);
    setQuestion("");
    setAnswer("");
    setCategory(activeCategory);
    setIsModalOpen(true);
  };

  const openEditModal = (entry: KnowledgeEntry) => {
    setEditingId(entry.id);
    setQuestion(entry.question || "");
    setAnswer(entry.answer);
    setCategory(entry.category);
    setIsModalOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !question.trim()) {
      toast.error("Please fill in both question and answer.");
      return;
    }

    setSubmitLoading(true);
    try {
      if (editingId !== null) {
        // Update
        const updated = await apiFetch<KnowledgeEntry>(`/api/v1/knowledge/${editingId}`, {
          method: "PUT",
          body: JSON.stringify({ category, question, answer, extra_data: {} }),
        });
        setEntries(entries.map((e) => (e.id === editingId ? updated : e)));
        toast.success("Knowledge base entry updated!");
      } else {
        // Create
        const created = await apiFetch<KnowledgeEntry>("/api/v1/knowledge", {
          method: "POST",
          body: JSON.stringify({ category, question, answer, extra_data: {} }),
        });
        setEntries([created, ...entries]);
        toast.success("Knowledge base entry created!");
      }
      setIsModalOpen(false);
    } catch (err: any) {
      toast.error(err.message || "Failed to save entry.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this knowledge entry?")) return;

    try {
      await apiFetch(`/api/v1/knowledge/${id}`, { method: "DELETE" });
      setEntries(entries.filter((e) => e.id !== id));
      toast.success("Entry deleted successfully.");
    } catch (err: any) {
      toast.error(err.message || "Failed to delete entry.");
    }
  };

  const filteredEntries = entries.filter((e) => e.category === activeCategory);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Knowledge Base</h1>
          <p className="text-sm text-[#7b8aa8]">Manage the answers, policies, and FAQs the AI agent uses to consult clients.</p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Entry
        </button>
      </div>

      {/* Tabs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {categories.map((cat) => {
          const count = entries.filter((e) => e.category === cat.id).length;
          return (
            <button
              key={cat.id}
              onClick={() => setActiveCategory(cat.id)}
              className={`p-4 rounded-xl border text-left transition-all relative overflow-hidden ${
                activeCategory === cat.id
                  ? "bg-white/[0.04] border-[#5d7ef0] shadow-lg shadow-[#5d7ef0]/5"
                  : "bg-white/[0.01] border-white/[0.08] hover:border-white/[0.15] hover:bg-white/[0.02]"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold text-[#7b8aa8] uppercase tracking-wider">{cat.name}</span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-white/[0.06] text-[#aab4cb]">
                  {count}
                </span>
              </div>
              <p className="text-[10px] text-[#7b8aa8] leading-normal">{cat.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Content List */}
      {loading ? (
        <div className="py-20 flex justify-center">
          <div className="w-8 h-8 border-4 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
        </div>
      ) : filteredEntries.length === 0 ? (
        <div className="text-center py-20 bg-white/[0.01] border border-white/[0.08] rounded-2xl">
          <BookOpen className="w-12 h-12 text-[#7b8aa8] mx-auto mb-4 opacity-50" />
          <h3 className="text-base font-bold text-white mb-1">No Entries in {categories.find((c) => c.id === activeCategory)?.name}</h3>
          <p className="text-xs text-[#7b8aa8] max-w-sm mx-auto mb-6">
            Configure answers for this category to ensure your AI agent replies accurately.
          </p>
          <button
            onClick={openAddModal}
            className="px-4 py-2 rounded-xl bg-white/[0.06] border border-white/[0.08] text-white text-xs font-semibold hover:bg-white/[0.1] transition-all"
          >
            Create first entry
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEntries.map((entry) => (
            <div
              key={entry.id}
              className="bg-white/[0.02] border border-white/[0.08] p-6 rounded-2xl relative group transition-all hover:bg-white/[0.03] hover:border-white/[0.12]"
            >
              <div className="flex justify-between items-start gap-4 mb-3">
                <h3 className="font-bold text-sm text-white leading-relaxed">{entry.question}</h3>
                <div className="flex gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEditModal(entry)}
                    className="p-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-[#aab4cb] hover:text-[#5d7ef0] hover:bg-white/[0.1]"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="p-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-[#aab4cb] hover:text-red-400 hover:bg-white/[0.1]"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <p className="text-xs text-[#7b8aa8] leading-relaxed whitespace-pre-wrap">{entry.answer}</p>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-[#070b14]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-[#0c1326] border border-white/[0.08] rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="text-lg font-bold text-white mb-4">
              {editingId !== null ? "Edit Knowledge Entry" : "Add Knowledge Entry"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                >
                  <option value="services" className="bg-[#131929]">Services</option>
                  <option value="pricing" className="bg-[#131929]">Pricing</option>
                  <option value="policies" className="bg-[#131929]">Policies</option>
                  <option value="faqs" className="bg-[#131929]">FAQs</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Question / Lead Inquiry
                </label>
                <input
                  type="text"
                  placeholder="e.g., What is the price of teeth cleaning?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Answer / Truth
                </label>
                <textarea
                  placeholder="e.g., Regular cleaning is $120. Deep cleaning is $250. Cleanings take 45 minutes."
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={4}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] resize-none"
                  required
                />
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
                  {submitLoading ? "Saving..." : "Save Entry"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

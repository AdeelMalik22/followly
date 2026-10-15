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
    <div className="mx-auto max-w-[1500px] space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-[-0.02em] text-[#17213b]">Knowledge Base</h1>
          <p className="text-sm text-[#7e8aa1]">Add your FAQs, product information, and business details for accurate AI answers.</p>
        </div>
        <button
          onClick={openAddModal}
          className="flex items-center gap-2 rounded-xl bg-[#3678f6] px-4 py-2.5 text-sm font-semibold text-white shadow-sm shadow-blue-200 hover:bg-[#2568e4]"
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
                  ? "border-[#9fc0ff] bg-[#f1f6ff] shadow-sm"
                  : "border-[#e7ecf4] bg-white hover:border-[#b9c9e3] hover:bg-[#fbfcfe]"
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#53617a]">{cat.name}</span>
                <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold text-[#7e8aa1]">
                  {count}
                </span>
              </div>
              <p className="text-[10px] leading-normal text-[#8b97ab]">{cat.desc}</p>
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
        <div className="rounded-2xl border border-[#e7ecf4] bg-white py-20 text-center shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
          <BookOpen className="mx-auto mb-4 h-12 w-12 text-[#9aa5b8] opacity-50" />
          <h3 className="mb-1 text-base font-bold text-[#17213b]">No entries in {categories.find((c) => c.id === activeCategory)?.name}</h3>
          <p className="mx-auto mb-6 max-w-sm text-xs text-[#7e8aa1]">
            Configure answers for this category to ensure your AI agent replies accurately.
          </p>
          <button
            onClick={openAddModal}
            className="rounded-xl border border-[#dfe6f1] bg-white px-4 py-2 text-xs font-semibold text-[#3678f6] hover:bg-[#f4f7fc]"
          >
            Create first entry
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredEntries.map((entry) => (
            <div
              key={entry.id}
              className="group relative rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-[0_5px_20px_rgba(35,55,90,0.04)] transition hover:border-[#b9c9e3]"
            >
              <div className="flex justify-between items-start gap-4 mb-3">
                <h3 className="text-sm font-bold leading-relaxed text-[#34415d]">{entry.question}</h3>
                <div className="flex gap-2 opacity-60 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => openEditModal(entry)}
                    className="rounded-lg border border-[#e7ecf4] bg-white p-1.5 text-[#8b97ab] hover:bg-[#f1f6ff] hover:text-[#3678f6]"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="rounded-lg border border-[#e7ecf4] bg-white p-1.5 text-[#8b97ab] hover:bg-red-50 hover:text-red-500"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <p className="whitespace-pre-wrap text-xs leading-relaxed text-[#7e8aa1]">{entry.answer}</p>
            </div>
          ))}
        </div>
      )}

      {/* Add / Edit Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#17213b]/20 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-[#e7ecf4] bg-white p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="mb-4 text-lg font-bold text-[#17213b]">
              {editingId !== null ? "Edit Knowledge Entry" : "Add Knowledge Entry"}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                  Category
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                >
                  <option value="services">Services</option>
                  <option value="pricing">Pricing</option>
                  <option value="policies">Policies</option>
                  <option value="faqs">FAQs</option>
                </select>
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                  Question / Lead Inquiry
                </label>
                <input
                  type="text"
                  placeholder="e.g., What is the price of teeth cleaning?"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="w-full rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] placeholder-[#a0aabd] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                  required
                />
              </div>

              <div>
                <label className="mb-2 block text-xs font-semibold uppercase tracking-wider text-[#7e8aa1]">
                  Answer / Truth
                </label>
                <textarea
                  placeholder="e.g., Regular cleaning is $120. Deep cleaning is $250. Cleanings take 45 minutes."
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={4}
                  className="w-full resize-none rounded-xl border border-[#e7ecf4] bg-[#fbfcfe] px-3 py-2.5 text-sm text-[#17213b] placeholder-[#a0aabd] outline-none focus:border-[#8eb3ff] focus:ring-4 focus:ring-[#eaf2ff]"
                  required
                />
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

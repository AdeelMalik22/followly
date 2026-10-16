"use client";

import { useCallback, useEffect, useState } from "react";
import { Package, Plus, Search, ArrowDownToLine, ArrowUpFromLine, AlertTriangle } from "lucide-react";
import toast from "react-hot-toast";
import { apiFetch } from "@/lib/api";

type Item = {
  id: number; name: string; sku: string; category: string | null; unit: string;
  quantity: number; reorder_level: number; supplier: string | null; low_stock: boolean;
};

const emptyForm = { name: "", sku: "", category: "", unit: "unit", quantity: "0", reorder_level: "0", supplier: "" };

export default function InventoryPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [search, setSearch] = useState("");
  const [lowStock, setLowStock] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try { setItems(await apiFetch<Item[]>("/api/v1/inventory", { params: { search: search || undefined, low_stock: lowStock } })); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Unable to load inventory."); }
    finally { setLoading(false); }
  }, [search, lowStock]);
  useEffect(() => { const timer = window.setTimeout(() => { void load(); }, 0); return () => window.clearTimeout(timer); }, [load]);

  const createItem = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      await apiFetch("/api/v1/inventory", { method: "POST", body: JSON.stringify({ ...form, quantity: Number(form.quantity), reorder_level: Number(form.reorder_level), category: form.category || null, supplier: form.supplier || null }) });
      setForm(emptyForm); setShowForm(false); toast.success("Inventory item added."); void load();
    } catch (error) { toast.error(error instanceof Error ? error.message : "Unable to add item."); }
  };

  const adjust = async (item: Item, movement_type: "receive" | "consume") => {
    const quantity = window.prompt(`${movement_type === "receive" ? "Quantity received" : "Quantity used"} for ${item.name}`, "1");
    if (!quantity || Number(quantity) <= 0) return;
    try { await apiFetch(`/api/v1/inventory/${item.id}/adjust`, { method: "POST", body: JSON.stringify({ quantity: Number(quantity), movement_type }) }); toast.success("Stock updated."); void load(); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Unable to update stock."); }
  };

  return <div className="inventory-workspace mx-auto max-w-[1500px] space-y-7">
    <div className="inventory-hero flex flex-wrap items-center justify-between gap-6 rounded-3xl p-7 sm:p-9">
      <div><p className="text-xs font-bold uppercase tracking-[0.2em] text-blue-200">Workspace / Operations</p><h1 className="mt-3 text-4xl font-semibold tracking-tight text-white">Every item. Under control.</h1><p className="mt-3 max-w-lg text-sm leading-6 text-blue-100">Your inventory, organized. Keep supplies moving and see what needs attention before you run out.</p></div>
      <button onClick={() => setShowForm(!showForm)} className="inline-flex items-center gap-2 rounded-xl bg-[#3678f6] px-4 py-3 text-sm font-bold text-white shadow-lg shadow-blue-200 hover:bg-[#2568e4]"><Plus className="h-4 w-4" /> Add item</button>
    </div>
    <div className="grid gap-4 sm:grid-cols-3">
      {[
        { label: "Items in view", value: items.length, detail: "Matching your current filters", icon: Package, color: "bg-blue-100 text-blue-700" },
        { label: "Need attention", value: items.filter((item) => item.low_stock).length, detail: "At or below reorder level", icon: AlertTriangle, color: "bg-amber-100 text-amber-800" },
        { label: "Suppliers in view", value: new Set(items.map((item) => item.supplier).filter(Boolean)).size, detail: "Across the items shown below", icon: ArrowDownToLine, color: "bg-teal-100 text-teal-800" },
      ].map(({ label, value, detail, icon: Icon, color }) => <div key={label} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"><div className="flex items-center justify-between"><p className="text-sm font-semibold text-slate-600">{label}</p><span className={`rounded-xl p-2.5 ${color}`}><Icon className="h-5 w-5" /></span></div><p className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{loading ? "—" : value}</p><p className="mt-1 text-xs text-slate-600">{detail}</p></div>)}
    </div>
    {showForm && <form onSubmit={createItem} className="grid gap-3 rounded-2xl border border-[#d8e0ec] bg-white p-5 shadow-[0_8px_24px_rgba(35,55,90,0.07)] md:grid-cols-4">
      {([["name", "Item name"], ["sku", "SKU"], ["category", "Category"], ["unit", "Unit"], ["quantity", "Starting quantity"], ["reorder_level", "Low-stock level"], ["supplier", "Supplier"]] as const).map(([key, label]) => <label key={key} className="text-xs font-bold text-[#53617a]"><span className="mb-1 block">{label}</span><input required={key === "name" || key === "sku"} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} className="w-full rounded-xl border border-[#cbd6e5] px-3 py-2.5 text-sm outline-none focus:border-[#3678f6]" /></label>)}
      <div className="flex items-end"><button className="w-full rounded-xl bg-[#17213b] px-4 py-2.5 text-sm font-bold text-white">Save item</button></div>
    </form>}
    <div className="flex flex-wrap gap-3"><label className="flex min-w-[260px] flex-1 items-center gap-2 rounded-xl border border-[#cbd6e5] bg-white px-3 py-2.5"><Search className="h-4 w-4 text-[#66738d]" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or SKU" className="w-full text-sm outline-none" /></label><button onClick={() => setLowStock(!lowStock)} className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-bold ${lowStock ? "border-amber-300 bg-amber-50 text-amber-800" : "border-[#cbd6e5] bg-white text-[#53617a]"}`}><AlertTriangle className="h-4 w-4" /> Low stock only</button></div>
    <section className="overflow-hidden rounded-2xl border border-[#d8e0ec] bg-white shadow-[0_8px_24px_rgba(35,55,90,0.07)]"><div className="grid grid-cols-[1.5fr_1fr_1fr_1fr_auto] gap-4 border-b border-[#e1e7f0] bg-[#f7f9fc] px-5 py-3 text-[11px] font-bold uppercase tracking-wide text-[#66738d]"><span>Item</span><span>Category</span><span>Stock</span><span>Supplier</span><span>Actions</span></div>{loading ? <p className="p-8 text-center text-sm text-[#66738d]">Loading inventory...</p> : items.length === 0 ? <div className="p-12 text-center"><Package className="mx-auto h-10 w-10 text-[#7b879b]" /><p className="mt-3 text-sm font-bold text-[#34415d]">No inventory items yet</p><p className="mt-1 text-xs text-[#66738d]">Add your first supply or product to start tracking stock.</p></div> : items.map((item) => <div key={item.id} className="grid grid-cols-[1.5fr_1fr_1fr_1fr_auto] items-center gap-4 border-b border-[#edf1f6] px-5 py-4 last:border-0"><div><p className="text-sm font-bold text-[#17213b]">{item.name}</p><p className="mt-0.5 text-xs text-[#66738d]">SKU: {item.sku}</p></div><span className="text-xs text-[#53617a]">{item.category || "—"}</span><span className={`text-sm font-bold ${item.low_stock ? "text-amber-700" : "text-[#17213b]"}`}>{item.quantity} <span className="text-xs font-normal text-[#66738d]">{item.unit}</span>{item.low_stock && <span className="ml-1 text-[10px]">Low</span>}</span><span className="text-xs text-[#53617a]">{item.supplier || "—"}</span><div className="flex gap-1"><button title="Receive stock" onClick={() => adjust(item, "receive")} className="rounded-lg p-2 text-emerald-700 hover:bg-emerald-50"><ArrowDownToLine className="h-4 w-4" /></button><button title="Consume stock" onClick={() => adjust(item, "consume")} className="rounded-lg p-2 text-orange-700 hover:bg-orange-50"><ArrowUpFromLine className="h-4 w-4" /></button></div></div>)}</section>
  </div>;
}

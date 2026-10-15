"use client";

import React, { useCallback, useState, useEffect, useRef } from "react";
import { apiFetch } from "@/lib/api";
import { ConversationListItem, Message } from "@/types";
import toast from "react-hot-toast";
import { Search, Send, User, Cpu, MessageSquare } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

const statusTabs = [
  { id: "all", name: "All Threads" },
  { id: "active", name: "AI Active" },
  { id: "human_takeover", name: "Takeover" },
  { id: "cold", name: "Cold" },
  { id: "closed", name: "Closed" },
];

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<ConversationListItem[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");

  const [messageInput, setMessageInput] = useState("");
  const [sendLoading, setSendLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Selected conversation object
  const selectedConv = conversations.find((c) => c.id === selectedId);

  const fetchConversations = useCallback(async (silent = false) => {
    if (!silent) setLoadingList(true);
    try {
      const data = await apiFetch<ConversationListItem[]>("/api/v1/conversations", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
          search: searchQuery || undefined,
        },
      });
      setConversations(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load conversations.");
    } finally {
      if (!silent) setLoadingList(false);
    }
  }, [searchQuery, statusFilter]);

  const fetchMessages = useCallback(async (convId: number, silent = false) => {
    if (!silent) setLoadingMessages(true);
    try {
      const data = await apiFetch<Message[]>(`/api/v1/conversations/${convId}/messages`);
      setMessages(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load messages.");
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => { void fetchConversations(); }, 0);
    return () => window.clearTimeout(timer);
  }, [fetchConversations]);

  // Periodic polling for new messages & updates
  useEffect(() => {
    pollIntervalRef.current = setInterval(() => {
      fetchConversations(true);
      if (selectedId) {
        fetchMessages(selectedId, true);
      }
    }, 4000);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [fetchConversations, fetchMessages, selectedId]);

  useEffect(() => {
    if (selectedId) {
      const timer = window.setTimeout(() => { void fetchMessages(selectedId); }, 0);
      return () => window.clearTimeout(timer);
    } else {
      const timer = window.setTimeout(() => setMessages([]), 0);
      return () => window.clearTimeout(timer);
    }
  }, [fetchMessages, selectedId]);

  // Scroll to bottom when messages list updates
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleTakeover = async (status: "human_takeover" | "active") => {
    if (!selectedId) return;
    try {
      const updated = await apiFetch<ConversationListItem>(`/api/v1/conversations/${selectedId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      setConversations(conversations.map((c) => (c.id === selectedId ? { ...c, status: updated.status } : c)));
      toast.success(status === "human_takeover" ? "Takeover active. AI paused." : "AI resumes control.");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to update status.");
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !selectedId || sendLoading) return;

    setSendLoading(true);
    try {
      const newMsg = await apiFetch<Message>(`/api/v1/conversations/${selectedId}/messages`, {
        method: "POST",
        body: JSON.stringify({ content: messageInput }),
      });
      setMessages((prev) => [...prev, newMsg]);
      setMessageInput("");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to send message.");
    } finally {
      setSendLoading(false);
    }
  };

  return (
    <div className="crm-light h-[calc(100vh-8.5rem)] flex rounded-2xl border border-[#e7ecf4] bg-white overflow-hidden shadow-[0_5px_20px_rgba(35,55,90,0.04)]">
      {/* 1. Left List panel */}
      <div className="w-80 border-r border-[#e7ecf4] flex flex-col h-full bg-white">
        <div className="space-y-3 border-b border-[#eef1f6] p-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8aa8]" />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] py-2 pl-9 pr-4 text-xs text-[#17213b] placeholder-[#a5afbf] outline-none focus:border-[#3678f6]"
            />
          </div>

          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {statusTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-all ${
                  statusFilter === tab.id
                    ? "bg-[#eaf2ff] text-[#1764db]"
                    : "bg-[#f7f9fc] text-[#7e8aa1] hover:text-[#17213b] hover:bg-[#eef4ff]"
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-[#eef1f6]">
          {loadingList ? (
            <div className="py-20 flex justify-center">
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-[#e7ecf4] border-t-[#3678f6]" />
            </div>
          ) : conversations.length === 0 ? (
            <p className="text-xs text-[#7b8aa8] text-center py-10">No conversations found.</p>
          ) : (
            conversations.map((conv) => {
              const isSelected = conv.id === selectedId;
              const formattedTime = conv.last_message_at
                ? formatDistanceToNow(new Date(conv.last_message_at), { addSuffix: false }) + " ago"
                : "";
              return (
                <button
                  key={conv.id}
                  onClick={() => setSelectedId(conv.id)}
                  className={`w-full text-left p-4 transition-all hover:bg-[#fbfcfe] flex flex-col gap-2 ${
                    isSelected ? "bg-[#f1f6ff]" : "hover:bg-[#fbfcfe]"
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="truncate text-xs font-bold text-[#34415d]">
                      {conv.lead?.name || conv.lead?.phone || "Unknown Lead"}
                    </span>
                    <span className="text-[9px] text-[#7b8aa8] whitespace-nowrap">{formattedTime}</span>
                  </div>

                    <p className="line-clamp-1 truncate text-[11px] text-[#8b97ab]">
                    {conv.last_message?.content || "No messages yet"}
                  </p>

                  <div className="flex justify-between items-center">
                    <span className="rounded bg-[#f1f4f9] px-2 py-0.5 text-[9px] uppercase text-[#7e8aa1]">
                      {conv.channel}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                        conv.status === "human_takeover"
                          ? "border border-amber-100 bg-amber-50 text-amber-700"
                          : conv.status === "active"
                          ? "border border-emerald-100 bg-emerald-50 text-emerald-700"
                          : "bg-[#f1f4f9] text-[#7e8aa1]"
                      }`}
                    >
                      {conv.status === "human_takeover" ? "takeover" : conv.status === "active" ? "AI active" : conv.status}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* 2. Middle & Right Chat panels */}
      {selectedConv ? (
        <div className="flex-1 flex min-w-0">
          {/* Middle Conversation Thread */}
          <div className="flex-1 flex flex-col h-full min-w-0 bg-white">
            {/* Header info */}
            <div className="flex h-14 flex-shrink-0 items-center justify-between border-b border-[#eef1f6] px-6">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-[#34415d]">
                  {selectedConv.lead?.name || selectedConv.lead?.phone || "Lead Details"}
                </span>
                <span className="h-3 w-px bg-[#dfe6f1]" />
                <span className="text-[10px] font-medium uppercase tracking-wider text-[#8b97ab]">{selectedConv.channel}</span>
              </div>

              <div className="flex gap-2">
                {selectedConv.status === "human_takeover" ? (
                  <button
                    onClick={() => handleTakeover("active")}
                    className="flex items-center gap-1.5 rounded-lg border border-emerald-100 bg-emerald-50 px-3 py-1 text-[10px] font-bold text-emerald-700"
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    Resume AI
                  </button>
                ) : (
                  <button
                    onClick={() => handleTakeover("human_takeover")}
                    className="flex items-center gap-1.5 rounded-lg border border-amber-100 bg-amber-50 px-3 py-1 text-[10px] font-bold text-amber-700"
                  >
                    <User className="w-3.5 h-3.5" />
                    Pause AI &amp; Takeover
                  </button>
                )}
              </div>
            </div>

            {/* Message Thread */}
            <div className="flex-1 space-y-4 overflow-y-auto bg-[#fbfcfe] p-6">
              {loadingMessages ? (
                <div className="py-20 flex justify-center">
                  <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#e7ecf4] border-t-[#3678f6]" />
                </div>
              ) : messages.length === 0 ? (
                <p className="text-xs text-[#7b8aa8] text-center">No messages yet.</p>
              ) : (
                messages.map((msg) => {
                  const isUser = msg.role === "user";
                  return (
                    <div key={msg.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed whitespace-pre-wrap ${
                          isUser
                            ? "bg-[#5d7ef0] text-white rounded-tr-none shadow-md shadow-[#5d7ef0]/10"
                            : "rounded-tl-none border border-[#e7ecf4] bg-white text-[#53617a] shadow-sm"
                        }`}
                      >
                        {msg.content}
                      </div>
                    </div>
                  );
                })
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Compose Message Box */}
            <form onSubmit={handleSendMessage} className="flex-shrink-0 border-t border-[#eef1f6] bg-white p-4">
              <div className="relative flex gap-3">
                <textarea
                  value={messageInput}
                  onChange={(e) => setMessageInput(e.target.value)}
                  placeholder={
                    selectedConv.status === "human_takeover"
                      ? "Write a response to the lead..."
                      : "AI is active. Pause AI / Take over control to send a message."
                  }
                  disabled={selectedConv.status !== "human_takeover"}
                  rows={2}
                  className="flex-1 resize-none rounded-xl border border-[#dfe6f1] bg-[#fbfcfe] px-4 py-3 text-xs text-[#17213b] placeholder-[#a5afbf] outline-none focus:border-[#3678f6] disabled:cursor-not-allowed disabled:opacity-50"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSendMessage(e);
                    }
                  }}
                />
                <button
                  type="submit"
                  disabled={selectedConv.status !== "human_takeover" || !messageInput.trim() || sendLoading}
                  className="self-end p-3.5 rounded-xl bg-[#5d7ef0] text-white hover:bg-[#4169e1] transition-all disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>

          {/* Right Lead Details Strip */}
          <div className="w-64 flex-shrink-0 space-y-6 border-l border-[#eef1f6] bg-[#fbfcfe] p-6">
            <div>
              <h3 className="mb-4 text-xs font-bold uppercase tracking-wider text-[#53617a]">Lead Information</h3>
              <div className="space-y-4">
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Name</span>
                  <span className="text-xs font-semibold text-[#34415d]">{selectedConv.lead?.name || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Phone Number</span>
                  <span className="text-xs font-semibold text-[#34415d]">{selectedConv.lead?.phone || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Email Address</span>
                  <span className="text-xs font-semibold text-[#34415d]">{selectedConv.lead?.email || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Lead Status</span>
                  <span className="text-xs font-semibold capitalize text-[#34415d]">{selectedConv.lead?.status || "New"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Attribution Source</span>
                  <span className="text-xs font-semibold capitalize text-[#34415d]">{selectedConv.lead?.source || "unknown"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col items-center justify-center bg-[#fbfcfe] p-8">
          <MessageSquare className="w-12 h-12 text-[#7b8aa8] opacity-35 mb-3" />
          <h3 className="mb-1 text-sm font-bold text-[#34415d]">Select a Conversation</h3>
          <p className="text-xs text-[#7b8aa8]">Choose a conversation from the sidebar list to view the full thread and take manual control.</p>
        </div>
      )}
    </div>
  );
}

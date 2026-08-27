"use client";

import React, { useState, useEffect, useRef } from "react";
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

  const fetchConversations = async (silent = false) => {
    if (!silent) setLoadingList(true);
    try {
      const data = await apiFetch<ConversationListItem[]>("/api/v1/conversations", {
        params: {
          status: statusFilter === "all" ? undefined : statusFilter,
          search: searchQuery || undefined,
        },
      });
      setConversations(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load conversations.");
    } finally {
      if (!silent) setLoadingList(false);
    }
  };

  const fetchMessages = async (convId: number, silent = false) => {
    if (!silent) setLoadingMessages(true);
    try {
      const data = await apiFetch<Message[]>(`/api/v1/conversations/${convId}/messages`);
      setMessages(data);
    } catch (err: any) {
      toast.error(err.message || "Failed to load messages.");
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  };

  useEffect(() => {
    fetchConversations();
  }, [statusFilter, searchQuery]);

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
  }, [selectedId, statusFilter, searchQuery]);

  useEffect(() => {
    if (selectedId) {
      fetchMessages(selectedId);
    } else {
      setMessages([]);
    }
  }, [selectedId]);

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
    } catch (err: any) {
      toast.error(err.message || "Failed to update status.");
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
    } catch (err: any) {
      toast.error(err.message || "Failed to send message.");
    } finally {
      setSendLoading(false);
    }
  };

  return (
    <div className="h-[calc(100vh-8.5rem)] flex bg-[#0c1326]/30 border border-white/[0.08] rounded-2xl overflow-hidden">
      {/* 1. Left List panel */}
      <div className="w-80 border-r border-white/[0.08] flex flex-col h-full bg-[#0a0f1d]/50">
        <div className="p-4 border-b border-white/[0.08] space-y-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-[#7b8aa8]" />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white/[0.05] border border-white/[0.08] rounded-xl py-2 pl-9 pr-4 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0]"
            />
          </div>

          <div className="flex gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {statusTabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider whitespace-nowrap transition-all ${
                  statusFilter === tab.id
                    ? "bg-[#5d7ef0] text-white"
                    : "bg-white/[0.04] text-[#7b8aa8] hover:text-white hover:bg-white/[0.08]"
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-white/[0.04]">
          {loadingList ? (
            <div className="py-20 flex justify-center">
              <div className="w-6 h-6 border-2 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
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
                  className={`w-full text-left p-4 transition-all hover:bg-white/[0.02] flex flex-col gap-2 ${
                    isSelected ? "bg-white/[0.04]" : ""
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="font-bold text-xs text-white truncate">
                      {conv.lead?.name || conv.lead?.phone || "Unknown Lead"}
                    </span>
                    <span className="text-[9px] text-[#7b8aa8] whitespace-nowrap">{formattedTime}</span>
                  </div>

                  <p className="text-[11px] text-[#7b8aa8] truncate line-clamp-1">
                    {conv.last_message?.content || "No messages yet"}
                  </p>

                  <div className="flex justify-between items-center">
                    <span className="text-[9px] text-[#7b8aa8] bg-white/[0.06] px-2 py-0.5 rounded uppercase">
                      {conv.channel}
                    </span>
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full ${
                        conv.status === "human_takeover"
                          ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                          : conv.status === "active"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-white/[0.06] text-[#aab4cb]"
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
          <div className="flex-1 flex flex-col h-full min-w-0 bg-[#070b14]/10">
            {/* Header info */}
            <div className="h-14 border-b border-white/[0.08] px-6 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <span className="font-bold text-xs text-white">
                  {selectedConv.lead?.name || selectedConv.lead?.phone || "Lead Details"}
                </span>
                <span className="h-3 w-px bg-white/[0.12]" />
                <span className="text-[10px] text-[#7b8aa8] font-medium uppercase tracking-wider">{selectedConv.channel}</span>
              </div>

              <div className="flex gap-2">
                {selectedConv.status === "human_takeover" ? (
                  <button
                    onClick={() => handleTakeover("active")}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 hover:bg-emerald-500/20 text-[10px] font-bold transition-all"
                  >
                    <Cpu className="w-3.5 h-3.5" />
                    Resume AI
                  </button>
                ) : (
                  <button
                    onClick={() => handleTakeover("human_takeover")}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400 hover:bg-amber-500/20 text-[10px] font-bold transition-all"
                  >
                    <User className="w-3.5 h-3.5" />
                    Pause AI &amp; Takeover
                  </button>
                )}
              </div>
            </div>

            {/* Message Thread */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {loadingMessages ? (
                <div className="py-20 flex justify-center">
                  <div className="w-8 h-8 border-2 border-t-[#5d7ef0] border-white/[0.08] rounded-full animate-spin" />
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
                            : "bg-white/[0.04] border border-white/[0.08] text-[#e8edf7] rounded-tl-none"
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
            <form onSubmit={handleSendMessage} className="p-4 border-t border-white/[0.08] bg-[#0c1326]/20 flex-shrink-0">
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
                  className="flex-1 bg-white/[0.05] border border-white/[0.08] rounded-xl py-3 px-4 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#5d7ef0] resize-none disabled:opacity-50 disabled:cursor-not-allowed"
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
          <div className="w-64 border-l border-white/[0.08] bg-[#0a0f1d]/50 p-6 space-y-6 flex-shrink-0">
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-4">Lead Information</h3>
              <div className="space-y-4">
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Name</span>
                  <span className="text-xs font-semibold text-white">{selectedConv.lead?.name || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Phone Number</span>
                  <span className="text-xs font-semibold text-white">{selectedConv.lead?.phone || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Email Address</span>
                  <span className="text-xs font-semibold text-white">{selectedConv.lead?.email || "Not provided"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Lead Status</span>
                  <span className="text-xs font-semibold text-white capitalize">{selectedConv.lead?.status || "New"}</span>
                </div>
                <div>
                  <span className="block text-[10px] text-[#7b8aa8] uppercase font-bold">Attribution Source</span>
                  <span className="text-xs font-semibold text-white capitalize">{selectedConv.lead?.source || "unknown"}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center p-8 bg-[#070b14]/10">
          <MessageSquare className="w-12 h-12 text-[#7b8aa8] opacity-35 mb-3" />
          <h3 className="text-sm font-bold text-white mb-1">Select a Conversation</h3>
          <p className="text-xs text-[#7b8aa8]">Choose a conversation from the sidebar list to view the full thread and take manual control.</p>
        </div>
      )}
    </div>
  );
}

"use client";

import React, { useState } from "react";
import toast from "react-hot-toast";
import { UserPlus, User, Trash2, Mail } from "lucide-react";
import { useAuth } from "@/components/auth-provider";

interface Member {
  id: number;
  name: string;
  email: string;
  role: string;
  status: string;
}

export default function TeamPage() {
  const { user } = useAuth();

  // Mock list of team members (since team model is simplified / backend doesn't store multi-user by default yet)
  const [members, setMembers] = useState<Member[]>([
    { id: 1, name: user?.name || "John Smith", email: user?.email || "john@brightsmiles.com", role: "Owner", status: "Active" },
    { id: 2, name: "Sarah Connor", email: "sarah@brightsmiles.com", role: "Staff / Dentist", status: "Active" },
    { id: 3, name: "David Miller", email: "david@brightsmiles.com", role: "Front Desk Administrator", status: "Pending Invite" },
  ]);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteName, setInviteName] = useState("");
  const [inviteRole, setInviteRole] = useState("Staff");
  const [inviteLoading, setInviteLoading] = useState(false);

  const handleInvite = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail || !inviteName) {
      toast.error("Please fill in name and email.");
      return;
    }

    setInviteLoading(true);
    setTimeout(() => {
      const newMember: Member = {
        id: Date.now(),
        name: inviteName,
        email: inviteEmail,
        role: inviteRole,
        status: "Pending Invite",
      };

      setMembers([...members, newMember]);
      toast.success(`Invitation sent to ${inviteEmail}`);
      setInviteLoading(false);
      setIsModalOpen(false);
      setInviteName("");
      setInviteEmail("");
      setInviteRole("Staff");
    }, 800);
  };

  const handleRemove = (id: number) => {
    if (id === 1) {
      toast.error("You cannot remove the account owner.");
      return;
    }
    if (!confirm("Are you sure you want to remove this team member?")) return;

    setMembers(members.filter((m) => m.id !== id));
    toast.success("Team member removed.");
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Team Management</h1>
          <p className="text-sm text-[#7b8aa8]">Invite staff, front-desk managers, or operators to review threads and handle manual takeover.</p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#5d7ef0] text-white font-semibold text-sm hover:bg-[#4169e1] transition-all"
        >
          <UserPlus className="w-4 h-4" />
          Invite Member
        </button>
      </div>

      {/* Team Member List */}
      <div className="bg-white/[0.01] border border-white/[0.08] rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/[0.08] bg-white/[0.02]">
                <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Member Name</th>
                <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Email Address</th>
                <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Role</th>
                <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider">Status</th>
                <th className="p-4 text-[10px] font-bold text-[#7b8aa8] uppercase tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {members.map((member) => (
                <tr key={member.id} className="hover:bg-white/[0.01] transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-white/[0.05] border border-white/[0.08] flex items-center justify-center text-[#7b8aa8]">
                        <User className="w-4 h-4" />
                      </div>
                      <span className="text-xs font-bold text-white">{member.name}</span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="text-xs text-[#7b8aa8]">{member.email}</span>
                  </td>
                  <td className="p-4">
                    <span className="text-xs font-semibold text-white">{member.role}</span>
                  </td>
                  <td className="p-4">
                    <span
                      className={`text-[9px] font-bold px-2 py-0.5 rounded-full border uppercase tracking-wider ${
                        member.status === "Active"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border-amber-500/20"
                      }`}
                    >
                      {member.status}
                    </span>
                  </td>
                  <td className="p-4 text-right">
                    {member.id !== 1 ? (
                      <button
                        onClick={() => handleRemove(member.id)}
                        className="p-1.5 rounded-lg bg-white/[0.05] border border-white/[0.08] text-[#aab4cb] hover:text-red-400 hover:bg-white/[0.1] transition-all"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    ) : (
                      <span className="text-[10px] text-[#7b8aa8] font-semibold italic pr-2">Primary Owner</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invite Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-[#070b14]/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-[#0c1326] border border-white/[0.08] rounded-2xl p-6 shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            <h2 className="text-lg font-bold text-white mb-4">Invite Team Member</h2>

            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Full Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Sarah Connor"
                  value={inviteName}
                  onChange={(e) => setInviteName(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                  <input
                    type="email"
                    placeholder="e.g. sarah@brightsmiles.com"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 pl-10 pr-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-[#aab4cb] mb-2 uppercase tracking-wider">
                  Role
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full bg-white/[0.06] border border-white/[0.08] rounded-xl py-2.5 px-3 text-sm text-white focus:outline-none focus:border-[#5d7ef0]"
                >
                  <option value="Staff" className="bg-[#131929]">Staff / Assistant</option>
                  <option value="Admin" className="bg-[#131929]">Administrator</option>
                  <option value="Dentist" className="bg-[#131929]">Dentist / Specialist</option>
                </select>
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
                  disabled={inviteLoading}
                  className="px-4 py-2 rounded-xl bg-[#5d7ef0] text-white text-xs font-semibold hover:bg-[#4169e1] transition-all disabled:opacity-50"
                >
                  {inviteLoading ? "Sending..." : "Send Invitation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

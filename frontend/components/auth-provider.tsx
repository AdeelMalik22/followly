"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getAuthToken } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { UserMe } from "@/types";

interface AuthContextType {
  user: UserMe | null;
  loading: boolean;
  refetchUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  refetchUser: async () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      if (pathname !== "/login" && pathname !== "/signup") {
        router.replace("/login");
      }
      return;
    }

    try {
      const userData = await apiFetch<UserMe>("/api/v1/auth/me");
      setUser(userData);
      
      // Onboarding Gate: If knowledge base count is less than 3, force user to complete onboarding
      if (userData.knowledge_base_count < 3 && pathname !== "/onboarding") {
        router.replace("/onboarding");
      } else if (userData.knowledge_base_count >= 3 && pathname === "/onboarding") {
        router.replace("/dashboard");
      } else if (pathname === "/login" || pathname === "/signup") {
        router.replace("/dashboard");
      }
    } catch (err) {
      console.error("Error fetching user profile", err);
      setUser(null);
      if (pathname !== "/login" && pathname !== "/signup") {
        router.replace("/login");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, [pathname]);

  return (
    <AuthContext.Provider value={{ user, loading, refetchUser: fetchUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

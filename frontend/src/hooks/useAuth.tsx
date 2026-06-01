"use client";
import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import Cookies from "js-cookie";
import { authAPI } from "@/lib/api";

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: "user" | "admin";
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAdmin: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = Cookies.get("access_token");
    if (token) {
      authAPI.me()
        .then(({ data }) => setUser(data))
        .catch(() => {
          Cookies.remove("access_token");
          Cookies.remove("refresh_token");
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email: string, password: string) => {
    const { data } = await authAPI.login({ email, password });
    Cookies.set("access_token", data.access_token, { secure: true, sameSite: "strict", expires: 1 / 48 });
    Cookies.set("refresh_token", data.refresh_token, { secure: true, sameSite: "strict", expires: 7 });
    const me = await authAPI.me();
    setUser(me.data);
  };

  const logout = async () => {
    try { await authAPI.logout(); } catch {}
    Cookies.remove("access_token");
    Cookies.remove("refresh_token");
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAdmin: user?.role === "admin" }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};

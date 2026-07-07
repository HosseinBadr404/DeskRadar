"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

type Role = "admin" | "user";

interface User {
  name: string;
  role: Role;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (username: string, role: Role) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true); 
  const router = useRouter();

  useEffect(() => {
    const savedUser = localStorage.getItem("deskradar_user");
    
    const timer = setTimeout(() => {
      if (savedUser) {
        setUser(JSON.parse(savedUser));
      }
      setIsLoading(false);
    }, 0);

    return () => clearTimeout(timer);
  }, []);

  const login = (username: string, role: Role) => {
    const mockUser: User = {
      name: username || "کاربر سیستم",
      role: role,
      email: `${role}@deskino.com`,
    };
    setUser(mockUser);
    localStorage.setItem("deskradar_user", JSON.stringify(mockUser));
    router.push("/");
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem("deskradar_user");
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth باید داخل AuthProvider استفاده شود");
  }
  return context;
}
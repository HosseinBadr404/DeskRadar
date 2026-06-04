"use client";

import React, { createContext, useContext, useState } from "react";

type Role = "admin" | "user";

interface AuthContextType {
  user: { name: string; role: Role } | null;
  toggleRole: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<{ name: string; role: Role } | null>({
    name: "احمد احمدی",
    role: "admin",
  });

  const toggleRole = () => {
    setUser((prev) => 
      prev ? { ...prev, role: prev.role === "admin" ? "user" : "admin" } : null
    );
  };

  return (
    <AuthContext.Provider value={{ user, toggleRole }}>
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
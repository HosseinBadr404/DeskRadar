"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const { user, login } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [role, setRole] = useState<"admin" | "user">("admin");

  useEffect(() => {
    if (user) {
      router.push("/");
    }
  }, [user, router]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) return;
    login(username, role);
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-[360px] bg-white p-7 rounded-2xl border border-slate-200/50 shadow-[0_8px_30px_rgb(0,0,0,0.02)] space-y-7">
        <div className="flex flex-col items-center space-y-1.5 text-center">
          <img src="/deskino-logo.svg" alt="دسکینو" className="w-40 h-11 object-contain" />
          <p className="text-[10px] font-medium text-slate-400 tracking-wide uppercase">میز کار هوشمند رادار</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5.5 text-xs">
          <div className="space-y-3">
            <label className="block font-bold text-slate-500 mr-1">نام کاربری</label>
            <input
              type="text"
              required
              placeholder="حسین احمدی"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border border-slate-200 rounded-xl bg-white text-slate-800 placeholder-slate-300 transition-all focus:outline-none focus:border-slate-400 focus:shadow-[0_0_0_3px_rgba(0,0,0,0.01)]"
            />
          </div>

          <div className="space-y-3">
            <label className="block font-bold text-slate-500 mr-1">سطح دسترسی سازمانی</label>
            <div className="bg-slate-100/70 p-0.5 rounded-xl flex border border-slate-200/30">
              <button
                type="button"
                onClick={() => setRole("admin")}
                className={`flex-1 py-1.5 rounded-lg text-center font-bold transition-all cursor-pointer text-[11px] ${
                  role === "admin"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                }`}
              >
                مدیر
              </button>
              <button
                type="button"
                onClick={() => setRole("user")}
                className={`flex-1 py-1.5 rounded-lg text-center font-bold transition-all cursor-pointer text-[11px] ${
                  role === "user"
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-400 hover:text-slate-600"
                }`}
              >
                 کاربر 
              </button>
            </div>
          </div>

          <button
            type="submit"
            className="w-full bg-slate-900 text-white font-bold py-2.5 rounded-xl hover:bg-slate-800 transition-colors shadow-sm mt-2 cursor-pointer text-[11px]"
          >
            ورود به سیستم
          </button>
        </form>
      </div>
    </div>
  );
}
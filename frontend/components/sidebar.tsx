"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();

  if (!user) return null;

  const menuItems = [
    { name: "خلاصه گزارشات", href: "/", roles: ["admin", "user"] },
    { name: "تیکت‌های من", href: "/my-tickets", roles: ["user"] },
    { name: "اینباکس ارجاعات (AI)", href: "/admin/escalated", roles: ["admin"] },
    { name: "پایگاه دانش (KB)", href: "/knowledge-base", roles: ["admin", "user"] },
    { name: "تنظیمات سیستم", href: "/settings", roles: ["admin"] },
  ];

  const allowedItems = menuItems.filter((item) => item.roles.includes(user.role));

  return (
    <aside className="w-64 bg-white border-l border-slate-200 p-4 flex flex-col justify-between shadow-[1px_0_0_0_#e2e8f0]">
      <nav className="space-y-1">
        {allowedItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-4 py-3 rounded-xl text-sm transition-all duration-150 ${
                isActive 
                  ? "bg-slate-100 text-slate-900 font-bold" 
                  : "text-slate-500 hover:bg-slate-50 hover:text-slate-800"
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>
      
      <div className="px-4 py-2 text-[10px] text-slate-400 font-medium tracking-wide border-t border-slate-100 pt-3">
        دسترسی: {user.role === "admin" ? "مدیر پشتیبانی" : "کاربر سازمان"}
      </div>
    </aside>
  );
}
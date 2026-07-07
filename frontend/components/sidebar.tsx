"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

interface MenuItem {
  name: string;
  href: string;
  roles: ("admin" | "user")[];
}

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  const menuItems: MenuItem[] = [
    { name: "خلاصه گزارشات", href: "/", roles: ["admin", "user"] },
    { name: "صندوق تیکت‌ها", href: "/tickets", roles: ["admin"] },
    { name: "تیکت‌های من", href: "/my-tickets", roles: ["user"] },
    { name: "اینباکس ارجاعات (AI)", href: "/admin/escalated", roles: ["admin"] },
    { name: "پایگاه دانش (KB)", href: "/knowledge-base", roles: ["admin", "user"] },
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
      
      <div className="border-t border-slate-100 pt-3 space-y-2">
        
        <button 
          onClick={logout}
          className="w-full text-right px-4 py-2 text-xs font-semibold text-rose-500 hover:bg-rose-50 rounded-xl transition-colors cursor-pointer"
        >
        خروج از حساب
        </button>
        <div className="px-4 text-[10px] text-slate-400 font-medium">
          نقش: {user.role === "admin" ? "مدیر پشتیبانی" : "کاربر سازمان"}
        </div>
      </div>
    </aside>
  );
}
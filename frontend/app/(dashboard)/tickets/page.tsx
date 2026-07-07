"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import UrgencyBadge from "@/components/status-badge";

interface Ticket {
  id: number;
  title: string;
  description: string;
  category: "vpn" | "email" | "network" | "printer" | "account";
  category_label_fa: string;
  urgency: "low" | "medium" | "high" | "critical";
  status: "open" | "in_progress" | "resolved" | "closed";
  analysis_status: "pending" | "complete" | "failed";
  confidence: number;
  created_at: string;
}

const mockTickets: Ticket[] = [
  { id: 101, title: "مشکل عدم اتصال به VPN سازمان", description: "خطای احراز هویت میده و نیم ساعت دیگه جلسه دارم کارم کاملاً خوابیده.", category: "vpn", category_label_fa: "مشکل VPN", urgency: "critical", status: "open", analysis_status: "complete", confidence: 0.89, created_at: "۱۴۰۵/۰۳/۱۱ - ۱۰:۰۰" },
  { id: 102, title: "عدم باز شدن سرویس ایمیل بعد از تغییر رمز", description: "بعد از تغییر رمز عبور در اکتیو دایرکتوری، دیگه نمی‌تونم وارد اینباکس Outlook بشم.", category: "email", category_label_fa: "سرویس ایمیل", urgency: "high", status: "in_progress", analysis_status: "complete", confidence: 0.94, created_at: "۱۴۰۵/۰۳/۱۱ - ۱۰:۰۵" },
  { id: 103, title: "آفلاین بودن پرینتر طبقه دوم کارگاه", description: "پرینتر طبقه دوم آفلاین است و هیچ فایلی از سیستم‌های بچه خط چاپ ارسال نمیشه.", category: "printer", category_label_fa: "پرینتر و سخت‌افزار", urgency: "medium", status: "open", analysis_status: "pending", confidence: 0.0, created_at: "۱۴۰۵/۰۳/۱۱ - ۱۰:۱۰" },
  { id: 104, title: "درخواست دسترسی به مخازن گیت‌لب واحد DevOps", description: "برای پروژه جدید رادار نیاز به دسترسی Developer روی ریپازیتوری فرانت دارم.", category: "account", category_label_fa: "حساب و دسترسی", urgency: "low", status: "resolved", analysis_status: "complete", confidence: 0.91, created_at: "۱۴۰۵/۰۳/۱۰ - ۱۶:۴۵" }
];

export default function TicketsPage() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedUrgency, setSelectedUrgency] = useState("all");

  if (!user || user.role !== "admin") {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center space-y-2">
        <p className="text-sm font-bold text-slate-800">خطای دسترسی محدود</p>
        <p className="text-xs text-slate-400">شما مجوز دسترسی به صندوق مرکزی تیکت‌ها را ندارید.</p>
      </div>
    );
  }

  const handleAnalyze = (id: number) => {
    alert(`درخواست تحلیل هوش مصنوعی برای تیکت #${id} ارسال شد.`);
  };

  const filteredTickets = mockTickets.filter((ticket) => {
    const matchesSearch = ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) || ticket.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || ticket.category === selectedCategory;
    const matchesUrgency = selectedUrgency === "all" || ticket.urgency === selectedUrgency;
    return matchesSearch && matchesCategory && matchesUrgency;
  });

  return (
    <div className="space-y-6">
      
      <div className="space-y-2">
        <div className="flex items-baseline gap-2">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">صندوق ورودی تیکت‌ها</h1>
          <span className="text-xs font-bold text-slate-400 font-mono">({filteredTickets.length})</span>
        </div>
        <p className="text-xs text-slate-400">رصد زیرساخت هوشمندی و وضعیت تیکت‌های IT سازمان</p>
      </div>

      {/* نوار فیلترها */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs pt-1">
        <div className="relative w-full sm:w-72">
          <span className="absolute inset-y-0 right-3 flex items-center text-slate-400 pointer-events-none">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </span>
          <input
            type="text"
            placeholder="جستجو در عنوان یا شرح درخواست..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pr-8 pl-3 py-1.5 border border-slate-200 rounded-xl bg-white text-slate-800 placeholder-slate-400 transition-all focus:outline-none focus:border-slate-400"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex items-center bg-white border border-slate-200/80 rounded-xl px-2.5 py-1.5 hover:border-slate-300 transition-colors">
            <span className="text-slate-400 text-[10px] font-bold ml-1 select-none">دپارتمان:</span>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="bg-transparent text-slate-700 font-semibold focus:outline-none appearance-none pl-4 pr-0 cursor-pointer text-[11px]"
            >
              <option value="all">همه</option>
              <option value="vpn">مشکلات VPN</option>
              <option value="email">سرویس ایمیل</option>
              <option value="printer">پرینتر و سخت‌افزار</option>
              <option value="account">حساب و دسترسی</option>
            </select>
            <span className="absolute left-2.5 pointer-events-none text-slate-400 text-[9px]">▼</span>
          </div>

          <div className="relative flex items-center bg-white border border-slate-200/80 rounded-xl px-2.5 py-1.5 hover:border-slate-300 transition-colors">
            <span className="text-slate-400 text-[10px] font-bold ml-1 select-none">اولویت:</span>
            <select
              value={selectedUrgency}
              onChange={(e) => setSelectedUrgency(e.target.value)}
              className="bg-transparent text-slate-700 font-semibold focus:outline-none appearance-none pl-4 pr-0 cursor-pointer text-[11px]"
            >
              <option value="all">همه</option>
              <option value="low">کم اهمیت</option>
              <option value="medium">متوسط</option>
              <option value="high">فوری</option>
              <option value="critical">بحرانی</option>
            </select>
            <span className="absolute left-2.5 pointer-events-none text-slate-400 text-[9px]">▼</span>
          </div>
        </div>
      </div>

      {/* جدول تیکت‌ها */}
      <div className="bg-white rounded-2xl border border-slate-200/40 shadow-[0_2px_12px_rgba(0,0,0,0.01)] overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-right border-collapse">
            <thead>
              <tr className="border-b border-slate-100 text-[11px] font-bold text-slate-400 tracking-wide uppercase bg-slate-55/30">
                <th className="py-3.5 px-6 w-20">شناسه</th>
                <th className="py-3.5 px-4">شرح درخواست تیکت</th>
                <th className="py-3.5 px-4 w-36">دسته‌بندی</th>
                <th className="py-3.5 px-4 w-36">اولویت سیستم</th>
                <th className="py-3.5 px-4 w-24 text-center">اطمینان AI</th>
                <th className="py-3.5 px-4 w-28 text-center">وضعیت</th>
                <th className="py-3.5 px-6 w-40 text-left">زمان ثبت</th>
              </tr>
            </thead>
            <tbody className="text-xs text-slate-600 divide-y divide-slate-50/60">
              {filteredTickets.map((ticket) => (
                <tr key={ticket.id} className="hover:bg-slate-50/30 transition-colors group">
                  <td className="py-4.5 px-6 font-mono text-slate-400 text-[11px]">#{ticket.id}</td>
                  <td className="py-4.5 px-4 max-w-md">
                    <div className="space-y-0.5">
                      <p className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">{ticket.title}</p>
                      <p className="text-[11px] text-slate-400 font-normal leading-relaxed truncate">{ticket.description}</p>
                    </div>
                  </td>
                  <td className="py-4.5 px-4 text-slate-500 font-medium">{ticket.category_label_fa}</td>
                  <td className="py-4.5 px-4"><UrgencyBadge level={ticket.urgency} /></td>
                  <td className="py-4.5 px-4 text-center font-mono font-bold text-slate-700">
                    {ticket.analysis_status === "complete" ? (
                      <span className="bg-slate-50 px-2 py-0.5 rounded border border-slate-100 text-[11px]">{(ticket.confidence * 100).toFixed(0)}%</span>
                    ) : <span className="text-slate-300">---</span>}
                  </td>
                  <td className="py-4.5 px-4 text-center">
                    {ticket.analysis_status === "complete" && (
                      <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-blue-50/70 text-blue-600">
                        <span className="w-1 h-1 rounded-full bg-blue-500" /> تحلیل شده
                      </span>
                    )}
                    {ticket.analysis_status === "pending" && (
                      <button onClick={() => handleAnalyze(ticket.id)} className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 text-amber-600 border border-amber-200/40 hover:bg-amber-100 transition-colors cursor-pointer animate-pulse">
                        ⚡ تحلیل AI
                      </button>
                    )}
                  </td>
                  <td className="py-4.5 px-6 text-left text-slate-400 font-medium font-mono text-[11px]">{ticket.created_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
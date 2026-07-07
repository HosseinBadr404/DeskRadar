"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import UrgencyBadge from "@/components/status-badge";

const mockTicketDetail = {
  id: 101,
  title: "مشکل عدم اتصال به VPN سازمان",
  description: "خطای احراز هویت میده و نیم ساعت دیگه جلسه دارم کارم کاملاً خوابیده. لطفاً بررسی کنید همه بچه‌های واحد فروش همین مشکل رو دارن.",
  department: "واحد فروش",
  created_at: "۱۴۰۵/۰۳/۱۱ - ۱۰:۰۰",
  status_fa: "باز",
    analysis: {
    category_label_fa: "مشکل VPN سازمان",
    intent_label_fa: "خطای احراز هویت لایه دسترسی دورکاری",
    urgency: "critical" as const,
    confidence: 0.89,
    summary_fa: "کاربر به دلیل خطای احراز هویت در پروتکل تونل‌زنی نمی‌تواند به شبکه داخلی وصل شود. مشکل عمومی و در سطح واحد فروش گزارش شده است.",
    suggested_reply_fa: "سلام حسین عزیز، درخواست شما را دریافت کردیم. با توجه به قطعی عمومی در سرور احراز هویت لایه دسترسی فروش، تیم DevOps در حال بازنشانی سشن‌ها است. تا ۱۰ دقیقه آینده اتصال شما برقرار خواهد شد. ممنون از صبوری شما.",
    reasons_fa: [
      "تشخیص کلمات کلیدی بحرانی شامل (جلسه دارم، کارم خوابیده)",
      "تکرار همزمان قطعی احراز هویت در تیکت‌های هم‌پوشان واحد فروش",
      "انطباق معنایی ۹۱ درصدی با الگوی خطای سرور شعبه مرکزی"
    ]
  },

  intelligence: {
    similar_tickets: [
      { id: 98, title: "قطعی ارتباط VPN دپارتمان مالی", score: "۹۲%" },
      { id: 84, title: "خطای عدم پذیرش رمز عبور در کلاینت سیسکو", score: "۸۷%" }
    ],
    related_article: {
      id: 12,
      title: "راهنمای جامع رفع خطای دسترسی کلاینت‌های VPN و تغییر دامنه‌ها",
      score: 0.79
    }
  }
};

export default function TicketDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [copied, setCopied] = useState(false);
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null);
  const ticketId = params?.id;
  const handleCopyReply = () => {
    navigator.clipboard.writeText(mockTicketDetail.analysis.suggested_reply_fa);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
            <button 
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
      >
        ← بازگشت به صندوق ورودی
      </button>

      <div className="space-y-1.5">
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">{mockTicketDetail.title}</h1>
          <span className="font-mono text-xs font-bold text-slate-400 bg-slate-100 px-2 py-0.5 rounded">#{ticketId || mockTicketDetail.id}</span>
        </div>
        <p className="text-xs text-slate-400">ثبت شده توسط {mockTicketDetail.department} • زمان: {mockTicketDetail.created_at}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6"> 
          <div className="bg-white p-5 rounded-2xl border border-slate-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.01)] space-y-2.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">متن اصلی درخواست کاربر</h3>
            <p className="text-xs text-slate-700 leading-relaxed font-medium">{mockTicketDetail.description}</p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-slate-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.01)] space-y-5">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                <h3 className="text-xs font-bold text-slate-800">تحلیل متنی لایه AI Core</h3>
              </div>
              <span className="text-[11px] font-mono font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded">
                میزان اطمینان مدل: {(mockTicketDetail.analysis.confidence * 100).toFixed(0)}%
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="space-y-1">
                <span className="text-slate-400 block text-[11px]">دسته تشخیصی:</span>
                <span className="font-bold text-slate-800">{mockTicketDetail.analysis.category_label_fa}</span>
              </div>
              <div className="space-y-1">
                <span className="text-slate-400 block text-[11px]">قصد دقیق درخواست (Intent):</span>
                <span className="font-bold text-slate-800">{mockTicketDetail.analysis.intent_label_fa}</span>
              </div>
              <div className="space-y-1">
                <span className="text-slate-400 block text-[11px]">اولویت پیشنهادی سیستم:</span>
                <div className="pt-0.5"><UrgencyBadge level={mockTicketDetail.analysis.urgency} /></div>
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <span className="text-slate-400 block text-[11px] font-bold">خلاصه تحلیل هوشمند:</span>
              <p className="text-xs text-slate-600 leading-relaxed font-medium bg-slate-50/50 p-3 rounded-xl border border-slate-100">{mockTicketDetail.analysis.summary_fa}</p>
            </div>

            <div className="space-y-2 pt-1">
              <span className="text-slate-400 block text-[11px] font-bold">دلایل منطقی اتخاذ تصمیم مدل:</span>
              <ul className="space-y-1.5 text-xs text-slate-600 list-disc list-inside pr-1">
                {mockTicketDetail.analysis.reasons_fa.map((reason, i) => (
                  <li key={i} className="font-medium text-slate-650">{reason}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="bg-slate-900 text-white p-6 rounded-2xl shadow-sm space-y-4 relative overflow-hidden">
            <div className="absolute -top-12 -left-12 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl pointer-events-none" />
            
            <div className="flex items-center justify-between relative z-10">
              <h3 className="text-xs font-bold text-slate-400 tracking-wide">پاسخ پیشنهادی فارسی (AI Suggested)</h3>
              <button 
                onClick={handleCopyReply}
                className="text-[11px] font-bold bg-white/10 hover:bg-white/20 text-white px-3 py-1 rounded-lg transition-colors cursor-pointer"
              >
                {copied ? "✓ کپی شد" : "📋 کپی متن"}
              </button>
            </div>
            
            <p className="text-xs text-slate-200 leading-relaxed font-medium relative z-10 bg-white/[0.03] p-4 rounded-xl border border-white/[0.06]">
              {mockTicketDetail.analysis.suggested_reply_fa}
            </p>
          </div>

        </div>

        <div className="space-y-6">
          
          <div className="bg-white p-5 rounded-2xl border border-slate-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.01)] space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">مقاله راهنمای مرتبط (KB)</h3>
            <div className="space-y-2.5">
              <p className="text-xs font-semibold text-slate-800 hover:text-blue-600 cursor-pointer transition-colors leading-relaxed">
                {mockTicketDetail.intelligence.related_article.title}
              </p>
              
              <div className="flex items-center justify-between text-[11px] pt-1 border-t border-slate-50">
                <span className="text-slate-400 font-medium">میزان انطباق معنایی:</span>
                {mockTicketDetail.intelligence.related_article.score < 0.85 ? (
                  <span className="font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded">⚠️ اطمینان پایین</span>
                ) : (
                  <span className="font-mono font-bold text-emerald-600">{(mockTicketDetail.intelligence.related_article.score * 100).toFixed(0)}%</span>
                )}
              </div>
            </div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.01)] space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">تیکت‌های مشابه در دیتابیس</h3>
            <div className="divide-y divide-slate-100">
              {mockTicketDetail.intelligence.similar_tickets.map((ticket) => (
                <div 
                  key={ticket.id}
                  onClick={() => router.push(`/tickets/${ticket.id}`)}
                  className="py-3 flex items-center justify-between gap-3 cursor-pointer group last:pb-0 first:pt-0"
                >
                  <p className="text-xs font-semibold text-slate-700 group-hover:text-blue-600 transition-colors truncate max-w-[170px]">
                    {ticket.title}
                  </p>
                  <span className="text-[10px] font-mono font-bold text-slate-400 bg-slate-50 border border-slate-100 px-1.5 py-0.5 rounded">
                    {ticket.score} شباهت
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="bg-white p-5 rounded-2xl border border-slate-200/50 shadow-[0_2px_8px_rgba(0,0,0,0.01)] space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">ارزیابی صحت تحلیل سیستم</h3>
            <div className="space-y-3">
              <p className="text-[11px] text-slate-400 font-medium">آیا ارزیابی فوریت و دسته‌بندی هوش مصنوعی مورد تایید است؟</p>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  onClick={() => setFeedback("up")}
                  className={`py-2 rounded-xl font-bold transition-all cursor-pointer border ${
                    feedback === "up"
                      ? "bg-emerald-50 border-emerald-500 text-emerald-700"
                      : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  👍 مورد تایید بود
                </button>
                <button
                  onClick={() => setFeedback("down")}
                  className={`py-2 rounded-xl font-bold transition-all cursor-pointer border ${
                    feedback === "down"
                      ? "bg-rose-50 border-rose-500 text-rose-700"
                      : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  👎 نیاز به اصلاح دارد
                </button>
              </div>
              {feedback === "down" && (
                <div className="pt-2 animate-fadeIn space-y-2">
                  <p className="text-[10px] text-amber-600 font-bold">⚠️ گزارش اصلاحات به صورت خودکار در بانک Feedback API ثبت خواهد شد.</p>
                  <select className="w-full text-xs p-2 border border-slate-200 rounded-xl bg-slate-50/50 text-slate-600 focus:outline-none">
                    <option>انتخاب دسته اصلاحی صحیح...</option>
                    <option>سرویس ایمیل</option>
                    <option>پرینتر و سخت‌افزار</option>
                    <option>حساب و دسترسی</option>
                  </select>
                </div>
              )}
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
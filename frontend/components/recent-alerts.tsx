"use client";

export default function RecentAlerts() {
  const alerts = [
    { id: 1, type: "incident", msg: "تشخیص رخداد احتمالی در لایه احراز هویت VPN", time: "۵ دقیقه پیش", level: "بحرانی", color: "text-rose-600 bg-rose-50" },
    { id: 2, type: "sla", msg: "ریسک تاخیر SLA برای تیکت شماره #۱۰۴ سازمان", time: "۱۴ دقیقه پیش", level: "بالا", color: "text-amber-600 bg-amber-50" },
    { id: 3, type: "ticket", msg: "تیکت جدید با نارضایتی بالا از واحد مالی دریافت شد", time: "۳۲ دقیقه پیش", level: "بالا", color: "text-amber-600 bg-amber-50" },
    { id: 4, type: "incident", msg: "گزارش قطعی مکرر پرینتر آفلاین طبقه دوم کارگاه", time: "۱ ساعت پیش", level: "متوسط", color: "text-blue-600 bg-blue-50" },
    { id: 5, type: "system", msg: "بار پردازشی ماژول AI Analyzer به ۸۲٪ رسید", time: "۲ ساعت پیش", level: "کم اهمیت", color: "text-slate-500 bg-slate-100" },
  ];

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200/60 shadow-[0_2px_8px_rgba(0,0,0,0.01)] flex flex-col h-full">
      <div className="mb-4">
        <h3 className="text-sm font-bold text-slate-800">آخرین هشدارهای رادار</h3>
        <p className="text-[11px] text-slate-400 mt-0.5">وقایع زنده زیرساخت هوشمندی</p>
      </div>

      <div className="flex-1 divide-y divide-slate-100 overflow-hidden">
        {alerts.map((alert) => (
          <div key={alert.id} className="py-3 flex items-center justify-between gap-3 text-xs last:pb-0 first:pt-0">
            <div className="space-y-1 min-w-0 flex-1">
              <p className="text-slate-700 font-medium truncate leading-relaxed">{alert.msg}</p>
              <span className="text-[10px] text-slate-400 block">{alert.time}</span>
            </div>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold whitespace-nowrap ${alert.color}`}>
              {alert.level}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
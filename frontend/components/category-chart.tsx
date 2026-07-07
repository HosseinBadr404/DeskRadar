"use client";

export default function CategoryChart() {
  const chartData = [
    { category: "اتصال و مشکلات VPN", count: 14, percentage: "85%", color: "bg-blue-500" },
    { category: "سرویس ایمیل و Outlook", count: 8, percentage: "55%", color: "bg-amber-500" },
    { category: "شبکه و اینترنت داخلی", count: 6, percentage: "40%", color: "bg-rose-500" },
    { category: "پرینتر و سخت‌افزار کارگاه", count: 4, percentage: "25%", color: "bg-slate-400" },
    { category: "حساب کاربری و دسترسی‌ها", count: 2, percentage: "15%", color: "bg-emerald-500" },
  ];

  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200/60 shadow-[0_2px_8px_rgba(0,0,0,0.01)] flex flex-col justify-between h-full">
      <div className="mb-4">
        <h3 className="text-sm font-bold text-slate-800">تفکیک موضوعی تیکت‌ها (AI Cat)</h3>
        <p className="text-[11px] text-slate-400 mt-0.5">میزان تکرار تیکت‌های فارسی در دپارتمان‌ها</p>
      </div>

      <div className="space-y-4 flex-1 flex flex-col justify-center">
        {chartData.map((item, idx) => (
          <div key={idx} className="space-y-1.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-medium text-slate-600">{item.category}</span>
              <span className="font-bold text-slate-800">{item.count} تیکت</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full ${item.color} transition-all duration-500`}
                style={{ width: item.percentage }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
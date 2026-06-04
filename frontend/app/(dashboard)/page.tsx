import MetricCard from "@/components/metric-card";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-xl font-bold text-slate-900">خلاصه گزارشات</h1>
        <p className="text-xs text-slate-400">رصد زیرساخت هوشمندی و وضعیت تیکت‌های IT سازمان</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="تیکت‌های خاتمه یافته" 
          value={29} 
          valueColor="text-emerald-500" 
        />
        <MetricCard 
          title="پاسخ‌های موفق هوش مصنوعی" 
          value={18} 
          valueColor="text-blue-500" 
        />
        <MetricCard 
          title="تیکت‌های ارجاع شده به اپراتور" 
          value={34} 
          valueColor="text-amber-500" 
        />
        <MetricCard 
          title="رخدادهای احتمالی شبکه (AI)" 
          value={2} 
          valueColor="text-rose-500" 
        />
      </div>
    </div>
  );
}
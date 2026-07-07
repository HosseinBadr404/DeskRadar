import MetricCard from "@/components/metric-card";
import CategoryChart from "@/components/category-chart";
import RecentAlerts from "@/components/recent-alerts";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-xl font-bold text-slate-900">خلاصه گزارشات</h1>
        <p className="text-xs text-slate-400">خلاصه وضعیت کارگاه در بازه زمانی فعلی</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard 
          title="قطعات درحال تعمیر" 
          value={34} 
          valueColor="text-amber-500" 
        />
        <MetricCard 
          title="قطعات تاخیر خورده" 
          value={6} 
          valueColor="text-rose-500" 
        />
        <MetricCard 
          title="قطعات جدید ثبت شده" 
          value={6} 
          valueColor="text-emerald-500" 
        />
        <MetricCard 
          title="قطعات تکمیل شده" 
          value={29} 
          valueColor="text-blue-500" 
        />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-5">
        <div className="lg:col-span-2">
          <CategoryChart />
        </div>
        <div className="lg:col-span-2">
          <RecentAlerts />
        </div>
      </div>
    </div>
  );
}
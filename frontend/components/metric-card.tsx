"use client";

interface MetricCardProps {
  title: string;
  value: number | string;
  valueColor: string; 
}

export default function MetricCard({ title, value, valueColor }: MetricCardProps) {
  return (
    <div className="bg-white px-6 py-5 rounded-xl border border-slate-200/60 shadow-[0_2px_8px_rgba(0,0,0,0.02)] flex items-center justify-between transition-all hover:border-slate-300">
      <span className="text-sm font-medium text-slate-600">{title}</span>
            <h3 className={`text-2xl font-black ${valueColor} tracking-tight`}>
        {value}
      </h3>
    </div>
  );
}
"use client";

export default function LoadingSkeleton() {
  return (
    <div className="space-y-8 animate-pulse">
      <div className="space-y-2">
        <div className="h-6 bg-slate-200 rounded-md w-48"></div>
        <div className="h-4 bg-slate-150 rounded-md w-72"></div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white px-6 py-6 rounded-xl border border-slate-100 h-24 flex items-center justify-between">
            <div className="h-4 bg-slate-200 rounded w-24"></div>
            <div className="h-6 bg-slate-200 rounded w-12"></div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-100 h-80"></div>
        <div className="bg-white p-6 rounded-xl border border-slate-100 h-80"></div>
      </div>
    </div>
  );
}
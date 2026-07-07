"use client";

interface BadgeProps {
  level: "low" | "medium" | "high" | "critical";
}

export default function UrgencyBadge({ level }: BadgeProps) {
  const styles = {
    low: "bg-green-50 text-green-700 border-green-200",
    medium: "bg-blue-50 text-blue-700 border-blue-200",
    high: "bg-orange-50 text-orange-700 border-orange-200",
    critical: "bg-red-50 text-red-700 border-red-200 animate-pulse",
  };

  const labels = {
    low: "کم اهمیت",
    medium: "متوسط",
    high: "فوری / بالا",
    critical: "بحرانی",
  };

  return (
    <span className={`px-2.5 py-1 text-xs font-medium border rounded-full ${styles[level]}`}>
      {labels[level]}
    </span>
  );
}
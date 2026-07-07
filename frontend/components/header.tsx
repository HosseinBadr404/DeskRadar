"use client";

import { useAuth } from "@/lib/auth-context";

export default function Header() {
  const { user } = useAuth();

  return (
    <header className="h-18 bg-white border-b border-slate-200 flex items-center shadow-[0_1px_3px_rgba(0,0,0,0.02)]">
      
      <div className="w-64 h-full flex items-center gap-3 px-8 border-l border-slate-200">
        <img src="/deskino-logo.svg" alt="لوگو دسکینو" className="object-contain" />
      </div>

      <div className="flex-1 h-full px-6 flex items-center justify-end gap-6">
        
        <div className="flex items-center gap-6 text-sm text-slate-500">
          <button className="flex items-center gap-1 hover:text-slate-800 transition-colors cursor-pointer">
           مدیریت
          </button>
          <button className="flex items-center gap-1 hover:text-slate-800 transition-colors cursor-pointer">
           پشتیبانی تلفنی
          </button>
        </div>
        
        <div className="w-px h-5 bg-slate-200" />

        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-650">{user?.name || "احمد احمدی"}</span>
          
          <div className="w-8 h-8 rounded-full border border-slate-200 flex items-center justify-center shadow-inner">
            <svg 
              width="24" 
              height="24" 
              viewBox="0 0 24 24" 
              fill="none" 
              xmlns="http://www.w3.org/2000/svg"
              className="text-slate-500 w-4 h-4"
            >
              <path 
                d="M15.75 6C15.75 6.99456 15.3549 7.94839 14.6516 8.65165C13.9484 9.35491 12.9945 9.75 12 9.75C11.0054 9.75 10.0516 9.35491 9.34833 8.65165C8.64506 7.94839 8.24998 6.99456 8.24998 6C8.24998 5.00544 8.64506 4.05161 9.34833 3.34835C10.0516 2.64509 11.0054 2.25 12 2.25C12.9945 2.25 13.9484 2.64509 14.6516 3.34835C15.3549 4.05161 15.75 5.00544 15.75 6ZM4.50098 20.118C4.53311 18.1504 5.33731 16.2742 6.74015 14.894C8.14299 13.5139 10.0321 12.7405 12 12.7405C13.9679 12.7405 15.857 13.5139 17.2598 14.894C18.6626 16.2742 19.4668 18.1504 19.499 20.118C17.1464 21.1968 14.5881 21.7535 12 21.75C9.32398 21.75 6.78398 21.166 4.50098 20.118Z" 
                stroke="currentColor"
                strokeWidth="1.5" 
                strokeLinecap="round" 
                strokeLinejoin="round"
              />
            </svg>
          </div>
        </div>

      </div>
    </header>
  );
}
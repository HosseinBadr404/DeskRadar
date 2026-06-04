import Sidebar from "@/components/sidebar";
import Header from "@/components/header";
import { AuthProvider } from "@/lib/auth-context";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider> 
      <div className="flex flex-col min-h-screen bg-[#f8fafc]">
        <Header />
        
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 p-8 overflow-y-auto">
            {children}
          </main>
        </div>
      </div>
    </AuthProvider>
  );
}
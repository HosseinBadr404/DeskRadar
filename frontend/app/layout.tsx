import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";

export const metadata = {
  title: "ServiceDesk Radar",
  description: "AI-Powered Service Desk Dashboard",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl">
      <body>
        <AuthProvider>
          {children}
        </AuthProvider>
      </body>
    </html>
  );
}
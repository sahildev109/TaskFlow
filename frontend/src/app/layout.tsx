import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Toaster } from "react-hot-toast";
import { AuthProvider } from "@/hooks/useAuth";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "TaskFlow — Manage Your Work",
  description: "A modern task management application",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-gray-950 text-gray-100 min-h-screen`}>
        <AuthProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: { background: "#1f2937", color: "#f9fafb", border: "1px solid #374151" },
              success: { iconTheme: { primary: "#10b981", secondary: "#1f2937" } },
              error: { iconTheme: { primary: "#ef4444", secondary: "#1f2937" } },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { JetBrains_Mono, Sora } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { LayoutContent } from "@/components/layout/LayoutContent";

const sora = Sora({
  variable: "--font-sans",
  subsets: ["latin"],
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  display: 'swap',
});

export const metadata: Metadata = {
  title: "Olympiet - Олимпиадная Платформа",
  description: "PvP олимпиады по программированию",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body
        className={`${sora.variable} ${jetbrainsMono.variable} antialiased`}
      >
        <AuthProvider>
          <LayoutContent>
            {children}
          </LayoutContent>
        </AuthProvider>
      </body>
    </html>
  );
}

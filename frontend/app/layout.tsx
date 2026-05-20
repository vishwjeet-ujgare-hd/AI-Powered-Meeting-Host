import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GirishOS - AI Meeting Host",
  description: "AI-Powered Interactive Meeting Host for AI pe Charcha",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-[#0a0a0a]">{children}</body>
    </html>
  );
}

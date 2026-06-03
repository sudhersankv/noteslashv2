import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Noteslash",
  description: "Turn any audio into searchable, cited notes.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-neutral-50 text-neutral-900 antialiased">
        {children}
      </body>
    </html>
  );
}

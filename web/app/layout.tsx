import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Virtual Parliament — Polish Sejm AI Simulation",
  description:
    "Educational simulation of the Polish Sejm. Five party agents debate and vote on user-submitted bills, with every argument cited to a real Polish legal source.",
};

const Disclaimer = () => (
  <div className="w-full bg-white border-t border-slate-200 px-4 py-2 text-center text-[10px] text-slate-500 mt-auto">
    ⚠️ Educational simulation — not a political forecast or endorsement. No real MPs are represented.
  </div>
);

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <main className="flex-1 flex flex-col">{children}</main>
        <Disclaimer />
      </body>
    </html>
  );
}

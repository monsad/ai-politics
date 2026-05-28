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
  title: "Virtual Parliament — Wirtualny Sejm",
  description:
    "Educational simulation of the Polish Sejm. Five party agents debate and vote on user-submitted bills, with every argument cited to a real Polish legal source.",
};

const Disclaimer = ({ position }: { position: "top" | "bottom" }) => (
  <div
    className={`w-full px-4 py-2 text-center text-sm font-medium bg-amber-100 text-amber-900 border-amber-300 ${
      position === "top" ? "border-b" : "border-t mt-auto"
    }`}
  >
    ⚠️ EDUCATIONAL SIMULATION — not a political forecast, endorsement, or
    prediction. No real MPs are represented.
  </div>
);

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pl"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        <Disclaimer position="top" />
        <main className="flex-1 flex flex-col">{children}</main>
        <Disclaimer position="bottom" />
      </body>
    </html>
  );
}

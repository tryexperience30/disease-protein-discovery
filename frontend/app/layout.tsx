import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ModeProvider } from "@/components/ModeProvider";
import { Nav } from "@/components/Nav";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "Disease–Protein Network Intelligence",
    template: "%s — Disease–Protein Network Explorer",
  },
  description:
    "Research tool for computational disease–protein association analysis on human PPI networks.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <ModeProvider>
          <Nav />
          <main className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-10">{children}</main>
        </ModeProvider>
      </body>
    </html>
  );
}

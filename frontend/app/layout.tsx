import type { Metadata } from "next";
import { Inter, JetBrains_Mono, Space_Grotesk } from "next/font/google";
import { ModeProvider } from "@/components/ModeProvider";
import { Nav } from "@/components/Nav";
import { ThemeProvider } from "@/components/ThemeProvider";
import { VizSettingsProvider } from "@/components/VizSettingsProvider";
import "./globals.css";

const inter = Inter({ variable: "--font-ui", subsets: ["latin"] });
const spaceGrotesk = Space_Grotesk({ variable: "--font-display", subsets: ["latin"] });
const jetbrains = JetBrains_Mono({ variable: "--font-tech", subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    default: "Disease–Protein Network Intelligence",
    template: "%s — Disease–Protein Network Explorer",
  },
  description:
    "Research and educational tool for computational disease–protein association analysis on human PPI networks.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <body className={`${inter.variable} ${spaceGrotesk.variable} ${jetbrains.variable} antialiased`}>
        <ThemeProvider>
          <VizSettingsProvider>
            <ModeProvider>
              <Nav />
              <main className="mx-auto max-w-7xl px-4 py-8 md:px-6 md:py-12">{children}</main>
            </ModeProvider>
          </VizSettingsProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

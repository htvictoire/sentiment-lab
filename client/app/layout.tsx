import type { Metadata } from "next";
import localFont from "next/font/local";
import "@/styles/globals.css";

const poppins = localFont({
  src: [
    { path: "./fonts/poppins/poppins-400-latin.woff2", weight: "400", style: "normal" },
    { path: "./fonts/poppins/poppins-500-latin.woff2", weight: "500", style: "normal" },
    { path: "./fonts/poppins/poppins-600-latin.woff2", weight: "600", style: "normal" },
    { path: "./fonts/poppins/poppins-700-latin.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-poppins",
});

export const metadata: Metadata = {
  title: "Détection des sentiments WhatsApp",
  description: "Analyse des sentiments d'une conversation WhatsApp",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fr" className={poppins.variable}>
      <body className="font-sans">{children}</body>
    </html>
  );
}

import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "台灣天氣預報 GIS Dashboard | CWA Open Data",
  description: "基於中央氣象署開放資料 (F-C0032-001) 與 Next.js + React Leaflet 建立之 36 小時台灣天氣預報 GIS 儀表板",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <body className="antialiased min-h-screen bg-slate-950 text-slate-50">
        {children}
      </body>
    </html>
  );
}

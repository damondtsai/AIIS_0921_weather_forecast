"use client";

import React, { useState, useEffect, useCallback } from "react";
import dynamic from "next/dynamic";
import { RefreshCw, CloudSun, AlertCircle, CheckCircle2, ShieldCheck } from "lucide-react";
import { CountyWeatherSummary, ForecastRecord, ApiResponse } from "@/lib/types";
import SummaryCards from "./SummaryCards";
import ForecastChart from "./ForecastChart";
import ForecastTable from "./ForecastTable";
import CitySelector from "./CitySelector";

// Dynamic import of WeatherMap with SSR disabled to prevent Leaflet window is not defined error
const WeatherMap = dynamic(() => import("./WeatherMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[480px] rounded-2xl bg-slate-900 border border-slate-800 flex flex-col items-center justify-center text-slate-500 animate-pulse">
      <div className="w-10 h-10 border-4 border-sky-500 border-t-transparent rounded-full animate-spin mb-3" />
      <span>正在載入台灣 GIS 天氣地圖...</span>
    </div>
  ),
});

export default function Dashboard() {
  const [summaries, setSummaries] = useState<CountyWeatherSummary[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>("臺北市");
  const [selectedPeriodIndex, setSelectedPeriodIndex] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncing, setSyncing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");
  const [syncSuccessMsg, setSyncSuccessMsg] = useState<string | null>(null);

  // Fetch weather data from /api/weather
  const loadWeatherData = useCallback(async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const res = await fetch("/api/weather", { cache: "no-store" });
      const json: ApiResponse<CountyWeatherSummary[]> = await res.json();

      if (!json.ok || !json.data) {
        throw new Error(json.error || "無法載入氣象資料");
      }

      setSummaries(json.data);
      if (json.updatedAt) {
        setLastUpdated(json.updatedAt);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "連線發生錯誤，請稍後再試";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWeatherData();
  }, [loadWeatherData]);

  // Handle Manual Sync
  const handleManualSync = async () => {
    try {
      setSyncing(true);
      setSyncSuccessMsg(null);
      setErrorMessage(null);
      const res = await fetch("/api/sync", { method: "POST" });
      const json: ApiResponse = await res.json();

      if (!json.ok) {
        throw new Error(json.error || "同步失敗");
      }

      setSyncSuccessMsg(json.message || "成功同步氣象資料");
      await loadWeatherData();
      setTimeout(() => setSyncSuccessMsg(null), 5000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "同步發生錯誤";
      setErrorMessage(msg);
    } finally {
      setSyncing(false);
    }
  };

  // Find currently selected county data
  const currentSummary = summaries.find((s) => s.locationName === selectedCity);
  const forecasts = currentSummary?.forecasts || [];
  const currentForecast = forecasts[selectedPeriodIndex] || currentSummary?.currentForecast || null;

  const formatUpdateTime = (isoStr: string) => {
    if (!isoStr) return "剛更新";
    try {
      const d = new Date(isoStr);
      return d.toLocaleString("zh-TW", {
        month: "numeric",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="sticky top-0 z-50 bg-slate-950/85 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5 transition">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400">
              <CloudSun className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold tracking-tight text-white">
                  台灣天氣預報 GIS Dashboard
                </h1>
                <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> CWA F-C0032-001
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                中央氣象署 36 小時全台預報 · SQLite / libSQL 快取
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 self-end sm:self-auto">
            <div className="text-right hidden sm:block">
              <div className="text-xs text-slate-400">最後更新時間</div>
              <div className="text-xs font-mono font-medium text-slate-200">
                {formatUpdateTime(lastUpdated)}
              </div>
            </div>

            <button
              onClick={handleManualSync}
              disabled={syncing || loading}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-sky-600 hover:bg-sky-500 active:bg-sky-700 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-sky-600/20 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
              <span>{syncing ? "同步中..." : "重新整理 / 同步"}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Error Alert */}
        {errorMessage && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start justify-between gap-3 shadow-lg">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold">無法取得氣象資料</div>
                <div className="text-xs text-rose-300/90 mt-0.5">{errorMessage}</div>
              </div>
            </div>
            <button
              onClick={loadWeatherData}
              className="px-3 py-1 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium shrink-0 transition"
            >
              重新載入
            </button>
          </div>
        )}

        {/* Sync Success Alert */}
        {syncSuccessMsg && (
          <div className="p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 flex items-center gap-2.5 text-xs shadow-lg">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{syncSuccessMsg}</span>
          </div>
        )}

        {/* City Selector */}
        <CitySelector
          selectedCity={selectedCity}
          onSelectCity={(city) => setSelectedCity(city)}
        />

        {/* Time Period Tabs (今晚明晨 / 明日白天 / 明日晚上) */}
        {forecasts.length > 0 && (
          <div className="flex items-center gap-2 overflow-x-auto pb-1">
            <span className="text-xs font-medium text-slate-400 shrink-0">預報時段切換：</span>
            {forecasts.map((f, index) => {
              const titles = ["時段一 (今晚明晨)", "時段二 (明日白天)", "時段三 (明日晚上)"];
              const isSelected = selectedPeriodIndex === index;
              return (
                <button
                  key={index}
                  onClick={() => setSelectedPeriodIndex(index)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-medium transition cursor-pointer shrink-0 ${
                    isSelected
                      ? "bg-slate-800 text-sky-400 border border-sky-500/40 shadow-sm"
                      : "bg-slate-900/60 text-slate-400 border border-slate-800 hover:text-slate-200"
                  }`}
                >
                  {titles[index] || `時段 ${index + 1}`} ({f.start_time.slice(5, 11)})
                </button>
              );
            })}
          </div>
        )}

        {/* Summary Weather Cards */}
        <SummaryCards forecast={currentForecast} locationName={selectedCity} />

        {/* GIS Map and Trend Chart Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left / Top: Leaflet Map */}
          <div className="lg:col-span-6 h-[500px] lg:h-auto min-h-[480px]">
            <WeatherMap
              summaries={summaries}
              selectedLocation={selectedCity}
              onSelectCounty={(name) => setSelectedCity(name)}
            />
          </div>

          {/* Right / Bottom: Recharts Trend Chart */}
          <div className="lg:col-span-6 flex flex-col justify-between">
            <ForecastChart forecasts={forecasts} locationName={selectedCity} />
          </div>
        </div>

        {/* Detailed Forecast Table */}
        <ForecastTable forecasts={forecasts} locationName={selectedCity} />
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-800 bg-slate-950 py-6 px-4 text-center text-xs text-slate-500 space-y-1">
        <p>
          資料來源：中央氣象署 (CWA) 一般天氣預報開放資料 F-C0032-001 · 臺灣地理資訊系統
        </p>
        <p>
          技術架構：Next.js App Router ＋ TypeScript ＋ Tailwind CSS ＋ React Leaflet ＋ Recharts ＋ libSQL
        </p>
      </footer>
    </div>
  );
}

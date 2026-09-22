"use client";

import React from "react";
import { Cloud, CloudRain, Droplets, Sun, Thermometer, Wind, CloudLightning, ShieldAlert } from "lucide-react";
import { ForecastRecord } from "@/lib/types";

interface SummaryCardsProps {
  forecast: ForecastRecord | null;
  locationName: string;
}

export default function SummaryCards({ forecast, locationName }: SummaryCardsProps) {
  if (!forecast) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-32 rounded-2xl bg-slate-900/80 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  // Weather icon mapping
  const getWeatherIcon = (wx: string) => {
    if (wx.includes("雷")) return <CloudLightning className="w-8 h-8 text-amber-400" />;
    if (wx.includes("雨")) return <CloudRain className="w-8 h-8 text-sky-400" />;
    if (wx.includes("晴") && !wx.includes("雨")) return <Sun className="w-8 h-8 text-amber-400" />;
    if (wx.includes("風")) return <Wind className="w-8 h-8 text-teal-400" />;
    return <Cloud className="w-8 h-8 text-slate-300" />;
  };

  // Temperature badge color
  const getTempColor = (temp: number) => {
    if (temp < 20) return "text-blue-400 border-blue-500/30 bg-blue-500/10";
    if (temp < 25) return "text-emerald-400 border-emerald-500/30 bg-emerald-500/10";
    if (temp < 30) return "text-amber-400 border-amber-500/30 bg-amber-500/10";
    return "text-rose-400 border-rose-500/30 bg-rose-500/10";
  };

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. 天氣現象 */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg backdrop-blur hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-400">天氣現象</span>
          {getWeatherIcon(forecast.weather)}
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-white tracking-tight">{forecast.weather}</div>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
              {locationName}
            </span>
            <span>{forecast.comfort || "舒適"}</span>
          </div>
        </div>
      </div>

      {/* 2. 降雨機率 */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg backdrop-blur hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-400">降雨機率</span>
          <Droplets className="w-8 h-8 text-sky-400" />
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-sky-300">
            {forecast.pop}<span className="text-base font-normal text-slate-400 ml-1">%</span>
          </div>
          {/* Progress bar */}
          <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-sky-500 h-1.5 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(forecast.pop, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* 3. 最低氣溫 */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg backdrop-blur hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-400">最低氣溫</span>
          <Thermometer className="w-8 h-8 text-blue-400" />
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-blue-400">
            {forecast.min_t}<span className="text-base font-normal text-slate-400 ml-1">°C</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            夜間 / 清晨低溫
          </div>
        </div>
      </div>

      {/* 4. 最高氣溫 */}
      <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-lg backdrop-blur hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-slate-400">最高氣溫</span>
          <Thermometer className="w-8 h-8 text-rose-400" />
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-rose-400">
            {forecast.max_t}<span className="text-base font-normal text-slate-400 ml-1">°C</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">
            白天 / 午後高溫
          </div>
        </div>
      </div>
    </div>
  );
}

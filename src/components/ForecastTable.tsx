"use client";

import React from "react";
import { ForecastRecord } from "@/lib/types";
import { Droplets, Thermometer } from "lucide-react";

interface ForecastTableProps {
  forecasts: ForecastRecord[];
  locationName: string;
}

export default function ForecastTable({ forecasts, locationName }: ForecastTableProps) {
  if (!forecasts || forecasts.length === 0) {
    return (
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 text-slate-400 text-center">
        暫無詳細預報資料
      </div>
    );
  }

  const formatPeriodTitle = (index: number) => {
    if (index === 0) return "今晚至明晨";
    if (index === 1) return "明日白天";
    if (index === 2) return "明日晚上";
    return `時段 ${index + 1}`;
  };

  return (
    <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
          <span>📋</span> {locationName} 36 小時詳細預報表
        </h3>
        <span className="text-xs text-slate-400">
          共 {forecasts.length} 個預報時段
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-800/60 text-xs uppercase tracking-wider text-slate-400 border-b border-slate-800">
            <tr>
              <th className="py-3 px-4 rounded-l-lg">預報時段</th>
              <th className="py-3 px-4">時間區間</th>
              <th className="py-3 px-4">天氣現象</th>
              <th className="py-3 px-4">降雨機率</th>
              <th className="py-3 px-4">氣溫區間</th>
              <th className="py-3 px-4 rounded-r-lg">舒適度指數</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {forecasts.map((f, i) => (
              <tr key={i} className="hover:bg-slate-800/40 transition">
                <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                  <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-800 border border-slate-700 text-xs text-sky-400">
                    {i + 1}
                  </span>
                  <span>{formatPeriodTitle(i)}</span>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-400">
                  <div>{f.start_time}</div>
                  <div className="text-slate-500">至 {f.end_time}</div>
                </td>
                <td className="py-3.5 px-4 font-medium text-slate-200">
                  <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-xs text-amber-300">
                    {f.weather}
                  </span>
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-1.5 text-sky-400 font-semibold">
                    <Droplets className="w-4 h-4 text-sky-400" />
                    <span>{f.pop}%</span>
                  </div>
                </td>
                <td className="py-3.5 px-4">
                  <div className="flex items-center gap-1.5 font-medium">
                    <Thermometer className="w-4 h-4 text-blue-400" />
                    <span className="text-blue-400">{f.min_t}°C</span>
                    <span className="text-slate-500">~</span>
                    <span className="text-rose-400">{f.max_t}°C</span>
                  </div>
                </td>
                <td className="py-3.5 px-4 text-xs text-slate-400">
                  <span className="inline-block px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {f.comfort || "普通"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

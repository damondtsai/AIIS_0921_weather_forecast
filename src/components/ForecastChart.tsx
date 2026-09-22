"use client";

import React from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";
import { ForecastRecord } from "@/lib/types";

interface ForecastChartProps {
  forecasts: ForecastRecord[];
  locationName: string;
}

export default function ForecastChart({ forecasts, locationName }: ForecastChartProps) {
  if (!forecasts || forecasts.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center rounded-2xl bg-slate-900/80 border border-slate-800 text-slate-500">
        無圖表資料
      </div>
    );
  }

  // Format time period for X axis
  const formatPeriod = (start: string, end: string, index: number) => {
    try {
      const s = new Date(start);
      const e = new Date(end);
      const sHour = s.getHours();
      
      if (index === 0) return "第 1 時段 (今晚明晨)";
      if (index === 1) return "第 2 時段 (明日白天)";
      if (index === 2) return "第 3 時段 (明日晚上)";
      
      return `${s.getMonth() + 1}/${s.getDate()} ${sHour}點`;
    } catch {
      return `時段 ${index + 1}`;
    }
  };

  const chartData = forecasts.map((f, i) => ({
    period: formatPeriod(f.start_time, f.end_time, i),
    rawTime: `${f.start_time.slice(5, 16)} ~ ${f.end_time.slice(5, 16)}`,
    minT: f.min_t,
    maxT: f.max_t,
    pop: f.pop,
    weather: f.weather,
  }));

  // Min and max bounds for Y axis
  const allTemps = forecasts.flatMap((f) => [f.min_t, f.max_t]);
  const minBound = Math.floor(Math.min(...allTemps, 15) - 2);
  const maxBound = Math.ceil(Math.max(...allTemps, 32) + 2);

  return (
    <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h3 className="text-lg font-semibold text-slate-100 flex items-center gap-2">
            <span>📈</span> {locationName} 36 小時溫差與降雨趨勢
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            中央氣象署 3 時段高低溫區間與降雨機率預測
          </p>
        </div>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5 text-rose-400">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block" />
            最高溫 MaxT
          </div>
          <div className="flex items-center gap-1.5 text-blue-400">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block" />
            最低溫 MinT
          </div>
        </div>
      </div>

      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -15, bottom: 0 }}>
            <defs>
              <linearGradient id="colorMaxT" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorMinT" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis
              dataKey="period"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "#334155" }}
            />
            <YAxis
              domain={[minBound, maxBound]}
              unit="°C"
              stroke="#64748b"
              fontSize={12}
              tickLine={false}
              axisLine={{ stroke: "#334155" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="rounded-xl bg-slate-900 border border-slate-700 p-3 shadow-2xl text-xs space-y-1.5">
                      <div className="font-semibold text-slate-200">{data.period}</div>
                      <div className="text-slate-400 text-[11px]">{data.rawTime}</div>
                      <div className="pt-1 border-t border-slate-800 space-y-1">
                        <div className="flex justify-between gap-4 text-rose-400">
                          <span>最高溫：</span>
                          <span className="font-bold">{data.maxT} °C</span>
                        </div>
                        <div className="flex justify-between gap-4 text-blue-400">
                          <span>最低溫：</span>
                          <span className="font-bold">{data.minT} °C</span>
                        </div>
                        <div className="flex justify-between gap-4 text-sky-400">
                          <span>降雨機率：</span>
                          <span className="font-bold">{data.pop} %</span>
                        </div>
                        <div className="flex justify-between gap-4 text-amber-300">
                          <span>天氣狀況：</span>
                          <span>{data.weather}</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Area
              type="monotone"
              dataKey="maxT"
              name="最高溫"
              stroke="#f43f5e"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorMaxT)"
              dot={{ r: 5, fill: "#f43f5e", strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 7 }}
            />
            <Area
              type="monotone"
              dataKey="minT"
              name="最低溫"
              stroke="#3b82f6"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorMinT)"
              dot={{ r: 5, fill: "#3b82f6", strokeWidth: 2, stroke: "#fff" }}
              activeDot={{ r: 7 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

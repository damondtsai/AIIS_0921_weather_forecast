"use client";

import React from "react";
import { TAIWAN_COUNTIES } from "@/lib/constants";
import { MapPin } from "lucide-react";

interface CitySelectorProps {
  selectedCity: string;
  onSelectCity: (city: string) => void;
}

export default function CitySelector({ selectedCity, onSelectCity }: CitySelectorProps) {
  const regions = ["全部", "北部", "中部", "南部", "東部", "外島"] as const;
  const [activeRegion, setActiveRegion] = React.useState<string>("全部");

  const filteredCounties = activeRegion === "全部"
    ? TAIWAN_COUNTIES
    : TAIWAN_COUNTIES.filter((c) => c.region === activeRegion);

  return (
    <div className="flex flex-col gap-3 p-4 rounded-2xl bg-slate-900/90 border border-slate-800 backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <MapPin className="w-5 h-5 text-sky-400" />
          <span className="text-sm font-semibold text-slate-200">選擇縣市：</span>
          <select
            value={selectedCity}
            onChange={(e) => onSelectCity(e.target.value)}
            aria-label="選擇欲查詢之縣市"
            className="rounded-xl bg-slate-800 border border-slate-700 px-3 py-1.5 text-sm font-medium text-white focus:outline-none focus:ring-2 focus:ring-sky-500 transition cursor-pointer"
          >
            {TAIWAN_COUNTIES.map((c) => (
              <option key={c.name} value={c.name}>
                {c.name} ({c.region})
              </option>
            ))}
          </select>
        </div>

        {/* Region filter chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          {regions.map((reg) => (
            <button
              key={reg}
              onClick={() => setActiveRegion(reg)}
              className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
                activeRegion === reg
                  ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                  : "bg-slate-800/80 text-slate-400 hover:text-slate-200 hover:bg-slate-800"
              }`}
            >
              {reg}
            </button>
          ))}
        </div>
      </div>

      {/* Quick selectable county pills */}
      <div className="flex flex-wrap gap-1.5 pt-2 border-t border-slate-800/80">
        {filteredCounties.map((c) => {
          const isSelected = c.name === selectedCity;
          return (
            <button
              key={c.name}
              onClick={() => onSelectCity(c.name)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition cursor-pointer ${
                isSelected
                  ? "bg-sky-500 text-white font-semibold shadow-sm"
                  : "bg-slate-800/60 text-slate-300 hover:bg-slate-700 hover:text-white"
              }`}
            >
              {c.name}
            </button>
          );
        })}
      </div>
    </div>
  );
}

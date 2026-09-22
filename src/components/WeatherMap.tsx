"use client";

import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { CountyWeatherSummary } from "@/lib/types";
import { DEFAULT_MAP_CENTER, DEFAULT_MAP_ZOOM } from "@/lib/constants";
import { Droplets, Thermometer, MapPin } from "lucide-react";

interface WeatherMapProps {
  summaries: CountyWeatherSummary[];
  selectedLocation: string;
  onSelectCounty: (name: string) => void;
}

// Helper to center map smoothly when county changes
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom(), { animate: true });
  }, [center, map]);
  return null;
}

export default function WeatherMap({
  summaries,
  selectedLocation,
  onSelectCounty,
}: WeatherMapProps) {
  const [activeCenter, setActiveCenter] = useState<[number, number]>(DEFAULT_MAP_CENTER);

  // Temperature color helper
  const getTempBgColor = (temp: number) => {
    if (temp < 20) return "#3b82f6"; // Blue
    if (temp < 25) return "#10b981"; // Green
    if (temp < 30) return "#f97316"; // Orange
    return "#ef4444"; // Red
  };

  // Create custom DivIcon for county marker
  const createCountyIcon = (summary: CountyWeatherSummary, isSelected: boolean) => {
    const temp = summary.currentForecast?.max_t || 25;
    const color = getTempBgColor(temp);
    const borderStyle = isSelected
      ? "border: 2.5px solid #ffffff; box-shadow: 0 0 15px rgba(255,255,255,0.8), 0 4px 6px -1px rgba(0,0,0,0.5); transform: scale(1.15);"
      : "border: 1.5px solid rgba(255,255,255,0.4); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4);";

    const html = `
      <div style="
        background-color: ${color};
        color: #ffffff;
        padding: 4px 8px;
        border-radius: 9999px;
        font-size: 11px;
        font-weight: 700;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 4px;
        cursor: pointer;
        transition: all 0.2s ease;
        ${borderStyle}
      ">
        <span>${summary.locationName}</span>
        <span style="background: rgba(0,0,0,0.25); padding: 1px 5px; border-radius: 9999px;">${temp}°C</span>
      </div>
    `;

    return L.divIcon({
      className: "custom-weather-marker",
      html,
      iconSize: [80, 28],
      iconAnchor: [40, 14],
      popupAnchor: [0, -16],
    });
  };

  // When selected county changes, update map center if valid
  useEffect(() => {
    const selected = summaries.find((s) => s.locationName === selectedLocation);
    if (selected) {
      setActiveCenter([selected.lat, selected.lng]);
    }
  }, [selectedLocation, summaries]);

  return (
    <div className="relative w-full h-full min-h-[480px] rounded-2xl overflow-hidden border border-slate-800 shadow-2xl bg-slate-900">
      {/* Map Legend Overlay */}
      <div className="absolute top-3 right-3 z-[1000] bg-slate-900/90 backdrop-blur-md border border-slate-700/80 rounded-xl p-3 text-xs shadow-xl space-y-1.5 pointer-events-auto">
        <div className="font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-sky-400" />
          <span>氣溫分級圖例</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-blue-500 inline-block" />
          <span className="text-slate-300">&lt; 20°C (寒冷/稍涼)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-emerald-500 inline-block" />
          <span className="text-slate-300">20 ~ 24°C (舒適宜人)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-orange-500 inline-block" />
          <span className="text-slate-300">25 ~ 29°C (溫暖微熱)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-rose-500 inline-block" />
          <span className="text-slate-300">≥ 30°C (炎熱高溫)</span>
        </div>
      </div>

      <MapContainer
        center={DEFAULT_MAP_CENTER}
        zoom={DEFAULT_MAP_ZOOM}
        scrollWheelZoom={true}
        className="w-full h-full"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions" target="_blank">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        <MapRecenter center={activeCenter} />

        {summaries.map((summary) => {
          const isSelected = summary.locationName === selectedLocation;
          return (
            <Marker
              key={summary.locationName}
              position={[summary.lat, summary.lng]}
              icon={createCountyIcon(summary, isSelected)}
              eventHandlers={{
                click: () => onSelectCounty(summary.locationName),
              }}
            >
              <Popup>
                <div className="p-1 space-y-2 text-slate-100 min-w-[180px]">
                  <div className="flex items-center justify-between border-b border-slate-700 pb-1.5">
                    <span className="font-bold text-base text-sky-400">{summary.locationName}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {summary.region}
                    </span>
                  </div>

                  <div className="text-sm font-medium text-amber-300">
                    {summary.currentForecast?.weather || "多雲"}
                  </div>

                  <div className="text-xs space-y-1 text-slate-300">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1 text-slate-400">
                        <Thermometer className="w-3.5 h-3.5 text-blue-400" />
                        氣溫區間：
                      </span>
                      <span className="font-bold">
                        {summary.currentForecast?.min_t}°C ~ {summary.currentForecast?.max_t}°C
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1 text-slate-400">
                        <Droplets className="w-3.5 h-3.5 text-sky-400" />
                        降雨機率：
                      </span>
                      <span className="font-bold text-sky-300">
                        {summary.currentForecast?.pop}%
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => onSelectCounty(summary.locationName)}
                    className="w-full mt-2 py-1.5 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium transition cursor-pointer"
                  >
                    切換至此縣市詳細報表
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}

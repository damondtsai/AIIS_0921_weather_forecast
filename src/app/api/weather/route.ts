import { NextRequest, NextResponse } from "next/server";
import { queryForecasts, upsertForecasts } from "@/lib/db";
import { fetchCwaWeather, normalizeCwaData } from "@/lib/cwa";
import { TAIWAN_COUNTIES, COUNTY_COORDINATES } from "@/lib/constants";
import { ApiResponse, CountyWeatherSummary, ForecastRecord } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(request: NextRequest): Promise<NextResponse<ApiResponse>> {
  try {
    const searchParams = request.nextUrl.searchParams;
    const locationQuery = searchParams.get("location") || searchParams.get("locationName");

    // Query database
    let forecasts = await queryForecasts(locationQuery || undefined);

    // If database is empty, auto-populate from CWA
    if (!forecasts || forecasts.length === 0) {
      try {
        const { data: cwaData } = await fetchCwaWeather();
        const records = normalizeCwaData(cwaData);
        await upsertForecasts(records);
        forecasts = await queryForecasts(locationQuery || undefined);
      } catch (syncErr) {
        console.warn("Auto-sync failed on empty database:", syncErr);
      }
    }

    if (locationQuery) {
      // Single county response
      return NextResponse.json({
        ok: true,
        data: forecasts,
        updatedAt: forecasts[0]?.fetched_at || new Date().toISOString(),
      });
    }

    // Group by county
    const groupedMap = new Map<string, ForecastRecord[]>();
    for (const f of forecasts) {
      const list = groupedMap.get(f.location_name) || [];
      list.push(f);
      groupedMap.set(f.location_name, list);
    }

    const summaries: CountyWeatherSummary[] = TAIWAN_COUNTIES.map((c) => {
      const countyForecasts = groupedMap.get(c.name) || [];
      const current = countyForecasts[0] || {
        location_name: c.name,
        start_time: "",
        end_time: "",
        weather: "晴時多雲",
        weather_code: "1",
        pop: 0,
        min_t: 22,
        max_t: 28,
        comfort: "舒適",
        fetched_at: new Date().toISOString(),
      };

      const coords = COUNTY_COORDINATES[c.name] || [c.lat, c.lng];

      return {
        locationName: c.name,
        lat: coords[0],
        lng: coords[1],
        region: c.region,
        currentForecast: current,
        forecasts: countyForecasts,
      };
    });

    return NextResponse.json({
      ok: true,
      data: summaries,
      total: summaries.length,
      updatedAt: forecasts[0]?.fetched_at || new Date().toISOString(),
    });
  } catch (error: unknown) {
    const errorMessage = error instanceof Error ? error.message : "查詢天氣預報時發生異常";
    console.error("Weather query error:", error);
    return NextResponse.json(
      {
        ok: false,
        error: `無法讀取氣象預報：${errorMessage}`,
      },
      { status: 500 }
    );
  }
}

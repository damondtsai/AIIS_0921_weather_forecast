import { z } from "zod";
import { ForecastRecord } from "./types";
import sampleJsonData from "@/data/sample_cwa.json";

// Zod validation schemas for CWA F-C0032-001
export const CWAElementValueSchema = z.object({
  parameterName: z.string(),
  parameterValue: z.string().optional(),
  parameterUnit: z.string().optional(),
});

export const CWATimeSchema = z.object({
  startTime: z.string(),
  endTime: z.string(),
  parameter: CWAElementValueSchema,
});

export const CWAElementSchema = z.object({
  elementName: z.string(),
  time: z.array(CWATimeSchema),
});

export const CWALocationSchema = z.object({
  locationName: z.string(),
  weatherElement: z.array(CWAElementSchema),
});

export const CWAResponseSchema = z.object({
  success: z.union([z.string(), z.boolean()]).optional(),
  records: z.object({
    datasetDescription: z.string().optional(),
    location: z.array(CWALocationSchema),
  }),
});

export type CWAResponse = z.infer<typeof CWAResponseSchema>;

const CWA_API_ENDPOINT = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001";

/**
 * Fetch raw weather data from CWA Open Data API (F-C0032-001)
 * Falls back to local sample data if API key is missing or network fails in dev
 */
export async function fetchCwaWeather(apiKey?: string): Promise<{ data: CWAResponse; isFallback: boolean }> {
  const key = apiKey || process.env.CWA_API_KEY;

  if (key && key.trim() !== "" && key !== "your_cwa_api_key_here") {
    try {
      const url = new URL(CWA_API_ENDPOINT);
      url.searchParams.set("Authorization", key.trim());
      url.searchParams.set("format", "JSON");

      const response = await fetch(url.toString(), {
        cache: "no-store",
        signal: AbortSignal.timeout(10_000), // 10s timeout
      });

      if (response.ok) {
        const rawJson = await response.json();
        const parsed = CWAResponseSchema.parse(rawJson);
        return { data: parsed, isFallback: false };
      }
      console.warn(`CWA API returned status ${response.status}. Using fallback sample data.`);
    } catch (err) {
      console.warn("Error calling CWA API, falling back to bundled dataset:", err);
    }
  }

  // Load directly bundled sample data
  try {
    const parsed = CWAResponseSchema.parse(sampleJsonData);
    return { data: parsed, isFallback: true };
  } catch (parseErr) {
    console.error("Failed to parse bundled sample data:", parseErr);
  }

  throw new Error("無法取得中央氣象署資料，且無本地快取資料可用。請確認 CWA_API_KEY 或網路連線。");
}

/**
 * Normalizes CWA raw JSON data into clean ForecastRecord array
 */
export function normalizeCwaData(cwaData: CWAResponse): ForecastRecord[] {
  const records: ForecastRecord[] = [];
  const fetchedAt = new Date().toISOString();

  for (const loc of cwaData.records.location) {
    const locationName = loc.locationName;

    // Create element map: Wx, PoP, MinT, MaxT, CI
    const elementMap = new Map<string, Array<z.infer<typeof CWATimeSchema>>>();
    for (const el of loc.weatherElement) {
      elementMap.set(el.elementName, el.time);
    }

    const wxTimes = elementMap.get("Wx") || [];
    const popTimes = elementMap.get("PoP") || [];
    const minTTimes = elementMap.get("MinT") || [];
    const maxTTimes = elementMap.get("MaxT") || [];
    const ciTimes = elementMap.get("CI") || [];

    // Iterate through time slots defined by Wx
    for (let i = 0; i < wxTimes.length; i++) {
      const wxTime = wxTimes[i];
      const popTime = popTimes[i];
      const minTTime = minTTimes[i];
      const maxTTime = maxTTimes[i];
      const ciTime = ciTimes[i];

      const weather = wxTime.parameter.parameterName || "多雲";
      const weatherCode = wxTime.parameter.parameterValue || "1";

      let pop = 0;
      if (popTime?.parameter?.parameterName) {
        const parsed = parseInt(popTime.parameter.parameterName, 10);
        if (!isNaN(parsed)) pop = parsed;
      }

      let minT = 20;
      if (minTTime?.parameter?.parameterName) {
        const parsed = parseFloat(minTTime.parameter.parameterName);
        if (!isNaN(parsed)) minT = parsed;
      }

      let maxT = 28;
      if (maxTTime?.parameter?.parameterName) {
        const parsed = parseFloat(maxTTime.parameter.parameterName);
        if (!isNaN(parsed)) maxT = parsed;
      }

      const comfort = ciTime?.parameter?.parameterName || "舒適";

      records.push({
        location_name: locationName,
        start_time: wxTime.startTime,
        end_time: wxTime.endTime,
        weather,
        weather_code: weatherCode,
        pop,
        min_t: minT,
        max_t: maxT,
        comfort,
        fetched_at: fetchedAt,
      });
    }
  }

  return records;
}

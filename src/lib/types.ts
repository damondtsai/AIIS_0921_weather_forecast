export interface ForecastRecord {
  id?: number;
  location_name: string;
  start_time: string;
  end_time: string;
  weather: string;
  weather_code?: string;
  pop: number; // 降雨機率 % (0-100)
  min_t: number; // 最低溫 °C
  max_t: number; // 最高溫 °C
  comfort?: string; // 舒適度
  fetched_at: string;
}

export interface CountyLocation {
  name: string;
  lat: number;
  lng: number;
  region: "北部" | "中部" | "南部" | "東部" | "外島";
}

export interface CountyWeatherSummary {
  locationName: string;
  currentForecast: ForecastRecord;
  forecasts: ForecastRecord[];
  lat: number;
  lng: number;
  region: string;
}

export interface ApiResponse<T = unknown> {
  ok: boolean;
  data?: T;
  error?: string;
  message?: string;
  updatedAt?: string;
  total?: number;
}

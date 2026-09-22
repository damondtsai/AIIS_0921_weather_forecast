import { CountyLocation } from "./types";

export const TAIWAN_COUNTIES: CountyLocation[] = [
  // 北部
  { name: "基隆市", lat: 25.1276, lng: 121.7392, region: "北部" },
  { name: "臺北市", lat: 25.0330, lng: 121.5654, region: "北部" },
  { name: "新北市", lat: 25.0116, lng: 121.4657, region: "北部" },
  { name: "桃園市", lat: 24.9936, lng: 121.3010, region: "北部" },
  { name: "新竹市", lat: 24.8138, lng: 120.9675, region: "北部" },
  { name: "新竹縣", lat: 24.8387, lng: 121.0177, region: "北部" },
  { name: "宜蘭縣", lat: 24.7021, lng: 121.7377, region: "北部" },

  // 中部
  { name: "苗栗縣", lat: 24.5602, lng: 120.8214, region: "中部" },
  { name: "臺中市", lat: 24.1477, lng: 120.6736, region: "中部" },
  { name: "彰化縣", lat: 24.0518, lng: 120.5161, region: "中部" },
  { name: "南投縣", lat: 23.9609, lng: 120.9719, region: "中部" },
  { name: "雲林縣", lat: 23.7092, lng: 120.4313, region: "中部" },

  // 南部
  { name: "嘉義市", lat: 23.4800, lng: 120.4491, region: "南部" },
  { name: "嘉義縣", lat: 23.4518, lng: 120.2555, region: "南部" },
  { name: "臺南市", lat: 22.9997, lng: 120.2270, region: "南部" },
  { name: "高雄市", lat: 22.6273, lng: 120.3014, region: "南部" },
  { name: "屏東縣", lat: 22.5519, lng: 120.5487, region: "南部" },

  // 東部
  { name: "花蓮縣", lat: 23.9872, lng: 121.6016, region: "東部" },
  { name: "臺東縣", lat: 22.7583, lng: 121.1444, region: "東部" },

  // 外島
  { name: "澎湖縣", lat: 23.5711, lng: 119.5793, region: "外島" },
  { name: "金門縣", lat: 24.4493, lng: 118.3766, region: "外島" },
  { name: "連江縣", lat: 26.1505, lng: 119.9499, region: "外島" },
];

export const COUNTY_COORDINATES: Record<string, [number, number]> = Object.fromEntries(
  TAIWAN_COUNTIES.map((c) => [c.name, [c.lat, c.lng]])
);

export const DEFAULT_MAP_CENTER: [number, number] = [23.7, 120.95];
export const DEFAULT_MAP_ZOOM = 7.5;

/**
 * Vercel Serverless Function: /api/weather
 * 負責向中央氣象署 CWA API (F-C0032-001) 請求台灣 22 縣市最新 36 小時預報並輸出標準結構。
 */
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001';

// 台灣 22 縣市地理中繼資料
const TAIWAN_COUNTIES = {
  "臺北市": { code: "63000", lat: 25.0375, lon: 121.5637, region: "北部" },
  "新北市": { code: "65000", lat: 24.9157, lon: 121.6739, region: "北部" },
  "基隆市": { code: "10017", lat: 25.1276, lon: 121.7392, region: "北部" },
  "桃園市": { code: "68000", lat: 24.9936, lon: 121.3010, region: "北部" },
  "新竹市": { code: "10018", lat: 24.8138, lon: 120.9675, region: "北部" },
  "新竹縣": { code: "10004", lat: 24.7033, lon: 121.1252, region: "北部" },
  "苗栗縣": { code: "10005", lat: 24.5602, lon: 120.8214, region: "中部" },
  "臺中市": { code: "66000", lat: 24.1477, lon: 120.6736, region: "中部" },
  "彰化縣": { code: "10007", lat: 24.0518, lon: 120.5161, region: "中部" },
  "南投縣": { code: "10008", lat: 23.9609, lon: 120.9719, region: "中部" },
  "雲林縣": { code: "10009", lat: 23.7092, lon: 120.4313, region: "中部" },
  "嘉義市": { code: "10020", lat: 23.4800, lon: 120.4491, region: "南部" },
  "嘉義縣": { code: "10010", lat: 23.4518, lon: 120.2555, region: "南部" },
  "臺南市": { code: "67000", lat: 22.9997, lon: 120.2270, region: "南部" },
  "高雄市": { code: "64000", lat: 22.6273, lon: 120.3014, region: "南部" },
  "屏東縣": { code: "10013", lat: 22.5519, lon: 120.5487, region: "南部" },
  "宜蘭縣": { code: "10002", lat: 24.7021, lon: 121.7377, region: "東部" },
  "花蓮縣": { code: "10015", lat: 23.9871, lon: 121.6016, region: "東部" },
  "臺東縣": { code: "10014", lat: 22.7583, lon: 121.1444, region: "東部" },
  "澎湖縣": { code: "10016", lat: 23.5712, lon: 119.5793, region: "離島" },
  "金門縣": { code: "09020", lat: 24.4492, lon: 118.3766, region: "離島" },
  "連江縣": { code: "09007", lat: 26.1505, lon: 119.9499, region: "離島" }
};

function normalizeName(name) {
  if (!name) return "";
  let n = name.trim().replace(/台/g, "臺");
  if (TAIWAN_COUNTIES[n]) return n;
  if (n === "臺北") return "臺北市";
  if (n === "臺中") return "臺中市";
  if (n === "臺南") return "臺南市";
  if (n === "高雄") return "高雄市";
  return n;
}

function getWxIcon(wx) {
  if (!wx) return "⛅";
  if (wx.includes("雷")) return "⛈️";
  if (wx.includes("雨")) return (wx.includes("大雨") || wx.includes("豪雨")) ? "🌧️" : "🌦️";
  if (wx.includes("陰")) return "☁️";
  if (wx.includes("晴") && wx.includes("多雲")) return "🌤️";
  if (wx.includes("晴")) return "☀️";
  if (wx.includes("多雲")) return "⛅";
  if (wx.includes("霧") || wx.includes("霾")) return "🌫️";
  return "⛅";
}

function getTimePeriodTitle(index, startTime) {
  try {
    const hour = parseInt(startTime.substring(11, 13), 10);
    if (index === 0) {
      if (hour >= 0 && hour < 6) return "今日凌晨至清晨";
      if (hour >= 6 && hour < 18) return "今日白天";
      return "今晚至明晨";
    } else if (index === 1) {
      if (hour >= 6 && hour < 18) return "明日白天";
      return "明晚至後天清晨";
    } else if (index === 2) {
      if (hour >= 6 && hour < 18) return "後日白天";
      return "明日晚上";
    }
  } catch (e) {}
  return `預報時段 ${index + 1}`;
}

function parseCwaJson(rawJson, status, message) {
  const locations = rawJson?.records?.location || [];
  const results = [];

  for (const loc of locations) {
    const rawName = loc.locationName;
    const name = normalizeName(rawName);
    const meta = TAIWAN_COUNTIES[name] || {};
    const elements = loc.weatherElement || [];

    const slotMap = {};

    for (const elem of elements) {
      const elemName = elem.elementName;
      const times = elem.time || [];

      for (const t of times) {
        const key = `${t.startTime}_${t.endTime}`;
        if (!slotMap[key]) {
          slotMap[key] = {
            startTime: t.startTime,
            endTime: t.endTime,
            wx: null,
            pop: null,
            minT: null,
            maxT: null,
            ci: null
          };
        }

        const paramName = t.parameter?.parameterName;
        if (elemName === "Wx") {
          slotMap[key].wx = paramName;
        } else if (["PoP", "PoP12h", "PoP24h"].includes(elemName)) {
          slotMap[key].pop = paramName ? parseFloat(paramName) : null;
        } else if (elemName === "MinT") {
          slotMap[key].minT = paramName ? parseFloat(paramName) : null;
        } else if (elemName === "MaxT") {
          slotMap[key].maxT = paramName ? parseFloat(paramName) : null;
        } else if (elemName === "CI") {
          slotMap[key].ci = paramName;
        }
      }
    }

    const sortedSlots = Object.values(slotMap).sort((a, b) => a.startTime.localeCompare(b.startTime));
    const forecasts = sortedSlots.map((slot, idx) => ({
      period_index: idx,
      period_title: getTimePeriodTitle(idx, slot.startTime),
      start_time: slot.startTime,
      end_time: slot.endTime,
      wx: slot.wx || "多雲",
      wx_icon: getWxIcon(slot.wx),
      pop: slot.pop,
      min_t: slot.minT,
      max_t: slot.maxT,
      ci: slot.ci || "舒適"
    }));

    results.push({
      location_name: name,
      county_code: meta.code || "",
      region: meta.region || "其他",
      lat: meta.lat || 0,
      lon: meta.lon || 0,
      forecasts
    });
  }

  // 排序：北部、中部、南部、東部、離島，縣市名稱排序
  results.sort((a, b) => a.location_name.localeCompare(b.location_name, 'zh-Hant'));

  return {
    success: true,
    status,
    message,
    fetched_at: new Date().toISOString(),
    counties_count: results.length,
    data: results
  };
}

function loadSampleData() {
  try {
    const samplePath = path.join(process.cwd(), 'data', 'sample_cwa.json');
    if (fs.existsSync(samplePath)) {
      const content = fs.readFileSync(samplePath, 'utf8');
      return JSON.parse(content);
    }
  } catch (e) {
    console.error("Error loading sample_cwa.json:", e);
  }
  return { records: { location: [] } };
}

module.exports = async function handler(req, res) {
  // 設定 CORS 與 Cache 標頭
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Cache-Control', 'public, s-maxage=600, stale-while-revalidate=1800');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  const apiKey = process.env.CWA_API_KEY;

  if (!apiKey || apiKey === 'your_cwa_api_key_here') {
    const sampleJson = loadSampleData();
    const result = parseCwaJson(sampleJson, 'demo', '未設定 CWA_API_KEY，已啟用示範資料模式 (Demo Data)。');
    return res.status(200).json(result);
  }

  try {
    const targetUrl = `${BASE_URL}?Authorization=${encodeURIComponent(apiKey)}&format=JSON`;
    
    // 使用 fetch 發送請求
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(20000)
    });

    if (response.ok) {
      const data = await response.json();
      if (data.success === 'true' || data.records) {
        const result = parseCwaJson(data, 'live', '成功自交通部中央氣象署取得即時預報 (Live Data)。');
        return res.status(200).json(result);
      }
    }

    console.warn(`CWA API returned status ${response.status}, falling back to sample data.`);
    const sampleJson = loadSampleData();
    const result = parseCwaJson(sampleJson, 'demo', `CWA API 狀態碼 ${response.status}，已自動切換為示範資料。`);
    return res.status(200).json(result);

  } catch (error) {
    console.error('Fetch CWA Error:', error.message);
    const sampleJson = loadSampleData();
    const result = parseCwaJson(sampleJson, 'demo', `連線異常 (${error.name})，已自動切換為示範資料。`);
    return res.status(200).json(result);
  }
};

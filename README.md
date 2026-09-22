# 台灣天氣預報 GIS Dashboard (Taiwan Weather GIS)

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat&logo=next.js)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue?style=flat&logo=typescript)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3-38bdf8?style=flat&logo=tailwind-css)](https://tailwindcss.com/)
[![React Leaflet](https://img.shields.io/badge/React_Leaflet-5-10b981?style=flat&logo=leaflet)](https://react-leaflet.js.org/)
[![Recharts](https://img.shields.io/badge/Recharts-2-22c55e?style=flat)](https://recharts.org/)
[![libSQL](https://img.shields.io/badge/libSQL-SQLite-0080ff?style=flat)](https://turso.tech/libsql)

基於 **Next.js App Router ＋ TypeScript ＋ Tailwind CSS ＋ React Leaflet ＋ Recharts ＋ `@libsql/client`** 建置之現代化台灣 36 小時天氣預報 GIS 視覺化儀表板。資料源採用**交通部中央氣象署 (CWA) 一般天氣預報開放資料 (F-C0032-001)**。

---

## 🌟 核心功能與特色

1. **36 小時氣象預報**：取得全台 22 縣市今晚明晨、明日白天、明日晚上 3 個時段的天氣現象 (Wx)、降雨機率 (PoP)、最低溫 (MinT)、最高溫 (MaxT) 與舒適度 (CI)。
2. **台灣天氣 GIS 地圖**：
   - 採用 React Leaflet 呈現全台縣市氣象標記。
   - 標記氣溫徽章依照溫度自動分級配色（< 20°C 藍色、20–24°C 綠色、25–29°C 橘色、≥ 30°C 紅色）。
   - 地圖 Marker 與下拉選單具備**雙向即時聯動**（點擊地圖標記即可切換主儀表板縣市數據）。
3. **Recharts 溫度降雨趨勢圖**：清楚繪製 3 時段 MinT/MaxT 溫差區間面積圖與降雨曲線。
4. **SQLite / libSQL 混合架構**：
   - 本機開發環境：使用本地 SQLite 檔案 `file:weather.db`。
   - 雲端部署環境：無縫銜接 Turso (libSQL over HTTP)。
   - 具備 `(location_name, start_time, end_time)` 唯一複合索引與 `UPSERT` 機制，確保重複同步不產生冗餘資料。
5. **資安邊界保護**：
   - CWA API Key 僅於 Next.js 伺服器端（Route Handler）安全存取，絕不暴露至前端瀏覽器。
   - 支援離線與開發期 Fallback 範例資料，無 API Key 亦能正常運行與測試。

---

## 🏗️ 系統架構

```mermaid
flowchart TD
    A[中央氣象署 CWA API\nF-C0032-001] --> B[Next.js Route Handler\n/api/sync]
    B --> C[Zod Schema 驗證 & 正規化]
    C --> D[(SQLite / libSQL\n@libsql/client)]
    D --> E[Next.js API\n/api/weather]
    E --> F[Dashboard 主介面]
    F --> G[SummaryCards 摘要卡]
    F --> H[ForecastChart 趨勢圖 (Recharts)]
    F --> I[WeatherMap GIS 地圖 (React Leaflet)]
    F --> J[ForecastTable 詳細預報表]
```

---

## 🚀 快速開始 (Local Development)

### 1. 安裝相依套件

```bash
npm install
```

### 2. 設定環境變數

複製 `.env.example` 為 `.env.local`：

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```dotenv
# 中央氣象署 API 金鑰 (https://opendata.cwa.gov.tw/ 申請)
CWA_API_KEY=你的CWA授權碼

# 本機開發使用 SQLite
DATABASE_URL=file:weather.db
DATABASE_AUTH_TOKEN=
```

> **提示**：若未填寫 `CWA_API_KEY`，系統將自動啟動內建的 22 縣市離線示範資料集，以供開發與測試。

### 3. 啟動開發伺服器

```bash
npm run dev
```

開啟瀏覽器造訪 `http://localhost:3000` 即可檢視天氣儀表板。

---

## 🧪 檢查與建置指令

- **程式碼檢查 (Lint)**：
  ```bash
  npm run lint
  ```
- **正式環境打包 (Build)**：
  ```bash
  npm run build
  ```
- **手動同步氣象資料**：
  造訪或發送 POST 請求至 `http://localhost:3000/api/sync`。

---

## ☁️ Vercel 與 Turso (libSQL) 部署教學

1. **建立 Turso 資料庫**：
   - 註冊並建立 [Turso](https://turso.tech/) 資料庫。
   - 取得資料庫連線 URL (例如 `libsql://your-db.turso.io`) 與 Auth Token。
2. **部署至 Vercel**：
   - 將本專案推送至 GitHub Repository。
   - 在 Vercel 匯入專案，並於 **Settings -> Environment Variables** 設定：
     - `CWA_API_KEY`: 您的中央氣象署授權碼
     - `DATABASE_URL`: `libsql://your-db.turso.io`
     - `DATABASE_AUTH_TOKEN`: 您的 Turso Auth Token
3. **完成部署**：Vercel 會自動完成建置並上線，資料庫將自動在首次請求時初始化與同步。

---

## 📄 資料授權與來源

- **氣象資料**：交通部中央氣象署開放資料平台 (CWA Open Data) - 一般天氣預報 (F-C0032-001)
- **地圖底圖**：OpenStreetMap 貢獻者 & CARTO Dark Matter 樣式
- **授權條款**：MIT License

/**
 * Taiwan Weather Forecast (CWA V8 Dashboard App)
 * Leaflet.js GIS Map + Chart.js Trend Visualizations + CWA Open Data API Integration
 */

// 全域狀態
let weatherData = [];
let geojsonData = null;
let currentCounty = "臺中市";
let currentMetric = "max_t"; // "max_t" | "min_t" | "pop"
let currentPeriodIndex = 0; // 0: 時段一, 1: 時段二, 2: 時段三
let currentRegionFilter = "all";
let mapInstance = null;
let geojsonLayer = null;
let markersLayerGroup = null;
let trendChartInstance = null;

// DOM 元素載入完成
document.addEventListener("DOMContentLoaded", () => {
  initClock();
  initMap();
  bindEvents();
  loadData();
});

// 1. 初始化時鐘
function initClock() {
  const clockEl = document.getElementById("clockDisplay");
  function update() {
    const now = new Date();
    const formatted = now.toLocaleString("zh-TW", {
      timeZone: "Asia/Taipei",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    });
    clockEl.innerHTML = `<i class="fa-regular fa-clock"></i> 台北標準時間 ${formatted}`;
  }
  update();
  setInterval(update, 1000);
}

// 2. 初始化 Leaflet GIS 地圖
function initMap() {
  mapInstance = L.map("taiwanMap", {
    center: [23.7, 120.95],
    zoom: 7.5,
    minZoom: 6,
    maxZoom: 12,
    zoomControl: true
  });

  // 底圖
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
  }).addTo(mapInstance);

  markersLayerGroup = L.layerGroup().addTo(mapInstance);
}

// 3. 綁定按鈕與互動事件
function bindEvents() {
  // 縣市切換下拉
  const selectEl = document.getElementById("selectCounty");
  selectEl.addEventListener("change", (e) => {
    selectCounty(e.target.value);
  });

  // 地圖指標切換 (最高溫/最低溫/降雨機率)
  const metricBtns = document.querySelectorAll("#metricTabs .btn-pill");
  metricBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      metricBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentMetric = btn.dataset.metric;
      
      const labelEl = document.getElementById("currentMapMetricLabel");
      if (currentMetric === "max_t") labelEl.innerText = "最高氣溫圖層";
      else if (currentMetric === "min_t") labelEl.innerText = "最低氣溫圖層";
      else labelEl.innerText = "降雨機率圖層";

      updateMap();
    });
  });

  // 預報時段切換 (時段一/二/三)
  const periodBtns = document.querySelectorAll("#periodTabs .btn-pill");
  periodBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      periodBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentPeriodIndex = parseInt(btn.dataset.period, 10);
      updateMap();
    });
  });

  // 分區分頁切換
  const regionTabs = document.querySelectorAll("#regionTabs .region-tab");
  regionTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      regionTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentRegionFilter = tab.dataset.region;
      renderTable();
    });
  });

  // 搜尋列
  const searchInput = document.getElementById("tableSearchInput");
  searchInput.addEventListener("input", () => {
    renderTable();
  });

  // 立即更新按鈕
  document.getElementById("btnRefresh").addEventListener("click", () => {
    loadData(true);
  });
}

// 4. 載入氣象資料與 GeoJSON
async function loadData(forceRefresh = false) {
  const badgeEl = document.getElementById("liveStatusBadge");
  badgeEl.className = "status-badge badge-loading";
  badgeEl.innerHTML = '<span class="pulse-dot"></span> 更新中...';

  try {
    // 載入 GeoJSON (若尚未載入)
    if (!geojsonData) {
      const geoResp = await fetch("data/taiwan_counties.geojson");
      geojsonData = await geoResp.json();
    }

    // 呼叫 Serverless API 或本地 fallback
    let apiUrl = "/api/weather";
    let resp = null;
    try {
      resp = await fetch(apiUrl);
    } catch (err) {
      console.warn("API /api/weather unavailable, falling back to static sample_cwa.json");
    }

    let result = null;
    if (resp && resp.ok) {
      result = await resp.json();
    } else {
      // 本地靜態 Fallback 解析
      const sampleResp = await fetch("data/sample_cwa.json");
      const sampleJson = await sampleResp.json();
      result = parseFallbackData(sampleJson);
    }

    weatherData = result.data || [];
    
    // 更新狀態徽章
    if (result.status === "live") {
      badgeEl.className = "status-badge badge-live";
      badgeEl.innerHTML = '<span class="pulse-dot"></span> CWA 即時連線 (Live)';
    } else {
      badgeEl.className = "status-badge badge-demo";
      badgeEl.innerHTML = '▲ 示範資料模式 (Demo)';
      
      const bannerEl = document.getElementById("alertBanner");
      const bannerMsg = document.getElementById("alertMessage");
      bannerEl.style.display = "flex";
      bannerMsg.innerText = result.message || "目前處於示範資料模式。";
    }

    // 初始化縣市選單
    populateCountySelect();

    // 更新儀表板各區塊
    updateCountyDetails();
    updateMap();
    renderTable();

  } catch (err) {
    console.error("載入資料失敗:", err);
    badgeEl.className = "status-badge badge-demo";
    badgeEl.innerHTML = '✕ 連線失敗';
  }
}

// 5. 填入縣市下拉選單
function populateCountySelect() {
  const selectEl = document.getElementById("selectCounty");
  selectEl.innerHTML = "";

  weatherData.forEach(item => {
    const opt = document.createElement("option");
    opt.value = item.location_name;
    opt.innerText = `${item.location_name} (${item.region})`;
    if (item.location_name === currentCounty) {
      opt.selected = true;
    }
    selectEl.appendChild(opt);
  });
}

// 6. 選定縣市互動
function selectCounty(name) {
  currentCounty = name;
  document.getElementById("selectCounty").value = name;
  updateCountyDetails();
  updateMap();

  // 若在地圖上有座標，平移地圖至該縣市
  const cData = weatherData.find(d => d.location_name === name);
  if (cData && cData.lat && cData.lon && mapInstance) {
    mapInstance.panTo([cData.lat, cData.lon], { animate: true, duration: 0.8 });
  }
}

// 7. 更新選定縣市氣象面板 (Hero Summary + 3-Period Cards + Chart.js)
function updateCountyDetails() {
  const countyObj = weatherData.find(d => d.location_name === currentCounty) || weatherData[0];
  if (!countyObj) return;

  const fList = countyObj.forecasts || [];
  const firstSlot = fList[0] || {};

  document.getElementById("selectedCountyTitle").innerText = countyObj.location_name;
  document.getElementById("heroCounty").innerText = countyObj.location_name;
  document.getElementById("heroIcon").innerText = firstSlot.wx_icon || "⛅";
  document.getElementById("heroDesc").innerText = `${firstSlot.wx || "多雲"} · 舒適度：${firstSlot.ci || "舒適"}`;
  
  const minT = firstSlot.min_t !== null ? Math.round(firstSlot.min_t) : "--";
  const maxT = firstSlot.max_t !== null ? Math.round(firstSlot.max_t) : "--";
  document.getElementById("heroTemp").innerText = `${minT} ~ ${maxT}°C`;
  document.getElementById("heroPop").innerText = `💧 ${firstSlot.pop !== null ? firstSlot.pop + '%' : '--'}`;

  // 渲染 3 時段卡片
  const cardsContainer = document.getElementById("periodCards");
  cardsContainer.innerHTML = "";

  fList.slice(0, 3).forEach((slot, idx) => {
    const sTime = slot.start_time.substring(5, 16);
    const eTime = slot.end_time.substring(5, 16);
    const card = document.createElement("div");
    card.className = "period-card";
    card.innerHTML = `
      <div>
        <span class="period-badge">${slot.period_title}</span>
        <div class="period-time-sub">${sTime} ~ ${eTime}</div>
        <div class="period-icon">${slot.wx_icon}</div>
        <div class="period-wx">${slot.wx}</div>
      </div>
      <div>
        <div class="period-bottom-stat">
          <span class="period-temp">${Math.round(slot.min_t)} ~ ${Math.round(slot.max_t)}°C</span>
          <br>
          <span class="period-pop">💧 降雨 ${slot.pop !== null ? slot.pop + '%' : '--'}</span>
        </div>
        <div class="period-ci">🧘 ${slot.ci}</div>
      </div>
    `;
    cardsContainer.appendChild(card);
  });

  // 更新 Chart.js 趨勢圖
  renderTrendChart(fList, countyObj.location_name);
}

// 8. 繪製 Chart.js 36 小時趨勢圖
function renderTrendChart(forecasts, countyName) {
  const ctx = document.getElementById("trendChart").getContext("2d");

  const labels = forecasts.map(f => {
    const s = f.start_time.substring(5, 16);
    const e = f.end_time.substring(5, 16);
    return `${f.period_title}\n(${s} ~ ${e})`;
  });

  const maxTemps = forecasts.map(f => f.max_t);
  const minTemps = forecasts.map(f => f.min_t);
  const pops = forecasts.map(f => f.pop || 0);

  if (trendChartInstance) {
    trendChartInstance.destroy();
  }

  trendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "最高氣溫 (°C)",
          data: maxTemps,
          borderColor: "#EF4444",
          backgroundColor: "rgba(239, 68, 68, 0.1)",
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 6,
          pointBackgroundColor: "#EF4444",
          yAxisID: "y"
        },
        {
          label: "最低氣溫 (°C)",
          data: minTemps,
          borderColor: "#0284C7",
          backgroundColor: "rgba(2, 132, 199, 0.1)",
          borderDash: [5, 5],
          tension: 0.35,
          borderWidth: 3,
          pointRadius: 6,
          pointBackgroundColor: "#0284C7",
          yAxisID: "y"
        },
        {
          type: "bar",
          label: "降雨機率 (%)",
          data: pops,
          backgroundColor: "rgba(56, 189, 248, 0.65)",
          borderColor: "#0284C7",
          borderWidth: 1,
          borderRadius: 6,
          yAxisID: "y1"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false
      },
      plugins: {
        legend: {
          position: "top",
          labels: { font: { family: "'Noto Sans TC', sans-serif", size: 12 } }
        },
        tooltip: {
          padding: 10,
          titleFont: { size: 13 },
          bodyFont: { size: 12 }
        }
      },
      scales: {
        y: {
          type: "linear",
          display: true,
          position: "left",
          title: { display: true, text: "溫度 (°C)" },
          grid: { color: "#F1F5F9" }
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          min: 0,
          max: 100,
          title: { display: true, text: "降雨率 (%)" },
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

// 9. 更新 GIS 地圖與圖例
function updateMap() {
  if (!mapInstance || !geojsonData) return;

  // 移除舊圖層
  if (geojsonLayer) {
    mapInstance.removeLayer(geojsonLayer);
  }
  markersLayerGroup.clearLayers();

  // 繪製 Polygon
  geojsonLayer = L.geoJSON(geojsonData, {
    style: (feature) => {
      const name = feature.properties.COUNTYNAME || feature.properties.name;
      const cData = weatherData.find(d => d.location_name === name);
      const slot = cData ? (cData.forecasts[currentPeriodIndex] || cData.forecasts[0]) : null;

      let val = null;
      if (slot) {
        if (currentMetric === "max_t") val = slot.max_t;
        else if (currentMetric === "min_t") val = slot.min_t;
        else val = slot.pop;
      }

      const isHighlight = (name === currentCounty);
      const fillColor = currentMetric === "pop" ? getPopColor(val) : getTempColor(val);

      return {
        fillColor: fillColor,
        weight: isHighlight ? 3.5 : 1.2,
        opacity: 1,
        color: isHighlight ? "#0B4F8A" : "#64748B",
        fillOpacity: isHighlight ? 0.9 : 0.72
      };
    },
    onEachFeature: (feature, layer) => {
      const name = feature.properties.COUNTYNAME || feature.properties.name;
      const cData = weatherData.find(d => d.location_name === name);
      const slot = cData ? (cData.forecasts[currentPeriodIndex] || cData.forecasts[0]) : null;

      if (slot) {
        const popupContent = `
          <div style="font-family:'Noto Sans TC',sans-serif; min-width:180px; padding:4px;">
            <div style="font-weight:800; color:#0B4F8A; font-size:15px; margin-bottom:4px;">
              ${name} <span style="font-size:18px;">${slot.wx_icon}</span>
            </div>
            <div style="font-size:12px; color:#64748B; margin-bottom:6px;">${slot.period_title}</div>
            <div style="font-size:13px; line-height:1.6;">
              <b>天氣：</b>${slot.wx}<br>
              <b>氣溫：</b><span style="color:#EF4444;font-weight:700;">${Math.round(slot.min_t)} ~ ${Math.round(slot.max_t)}°C</span><br>
              <b>降雨機率：</b><span style="color:#0284C7;font-weight:700;">💧 ${slot.pop !== null ? slot.pop + '%' : '--'}</span><br>
              <b>舒適度：</b>${slot.ci}
            </div>
          </div>
        `;
        layer.bindPopup(popupContent);
      }

      layer.on({
        click: () => {
          selectCounty(name);
        },
        mouseover: (e) => {
          layer.setStyle({ fillOpacity: 0.95, weight: 3 });
        },
        mouseout: (e) => {
          geojsonLayer.resetStyle(layer);
        }
      });
    }
  }).addTo(mapInstance);

  // 繪製 CWA 氣象膠囊 (Weather Pill Markers)
  weatherData.forEach(item => {
    if (!item.lat || !item.lon) return;

    const slot = item.forecasts[currentPeriodIndex] || item.forecasts[0];
    if (!slot) return;

    const isHighlight = (item.location_name === currentCounty);
    const activeClass = isHighlight ? "active" : "";

    let metricHtml = "";
    if (currentMetric === "max_t") {
      metricHtml = `<span class="temp-badge">${Math.round(slot.max_t)}°</span>`;
    } else if (currentMetric === "min_t") {
      metricHtml = `<span style="color:#0284C7;font-size:10px;">${Math.round(slot.min_t)}°</span>`;
    } else {
      metricHtml = `<span style="color:#0284C7;font-size:10px;">💧${slot.pop || 0}%</span>`;
    }

    const iconHtml = `
      <div class="weather-pill ${activeClass}" onclick="selectCounty('${item.location_name}')">
        <span>${slot.wx_icon}</span>
        <span>${item.location_name.substring(0, 2)}</span>
        ${metricHtml}
      </div>
    `;

    const customIcon = L.divIcon({
      html: iconHtml,
      className: "cwa-div-icon",
      iconSize: [68, 22],
      iconAnchor: [34, 11]
    });

    L.marker([item.lat, item.lon], { icon: customIcon }).addTo(markersLayerGroup);
  });

  // 更新圖例
  renderLegend();
}

// 10. 溫度與降雨顏色對照函式
function getTempColor(t) {
  if (t === null || t === undefined) return "#94A3B8";
  if (t < 18) return "#2563EB";
  if (t < 24) return "#0284C7";
  if (t < 28) return "#10B981";
  if (t <= 32) return "#F59E0B";
  return "#EF4444";
}

function getPopColor(p) {
  if (p === null || p === undefined) return "#94A3B8";
  if (p < 20) return "#BAE6FD";
  if (p <= 40) return "#38BDF8";
  if (p <= 70) return "#0284C7";
  return "#4338CA";
}

function renderLegend() {
  const legendTitle = document.getElementById("legendTitle");
  const legendItems = document.getElementById("legendItems");

  if (currentMetric === "pop") {
    legendTitle.innerText = "降雨機率分級 (%)";
    legendItems.innerHTML = `
      <div class="legend-item"><div class="legend-color-box" style="background:#4338CA;"></div> > 70% (高降雨)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#0284C7;"></div> 40 ~ 70% (局部陣雨)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#38BDF8;"></div> 20 ~ 40% (短暫雨)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#BAE6FD;"></div> 0 ~ 20% (機率低)</div>
    `;
  } else {
    legendTitle.innerText = "氣溫分級 (°C)";
    legendItems.innerHTML = `
      <div class="legend-item"><div class="legend-color-box" style="background:#EF4444;"></div> > 32°C (高溫炎熱)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#F59E0B;"></div> 28 ~ 32°C (溫暖炎熱)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#10B981;"></div> 24 ~ 28°C (舒適宜人)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#0284C7;"></div> 18 ~ 24°C (涼爽)</div>
      <div class="legend-item"><div class="legend-color-box" style="background:#2563EB;"></div> < 18°C (稍涼)</div>
    `;
  }
}

// 11. 渲染 22 縣市預報表格
function renderTable() {
  const tbody = document.getElementById("weatherTableBody");
  tbody.innerHTML = "";

  const searchKeyword = document.getElementById("tableSearchInput").value.trim();

  const filtered = weatherData.filter(item => {
    // 區域篩選
    if (currentRegionFilter !== "all" && item.region !== currentRegionFilter) {
      return false;
    }
    // 關鍵字搜尋
    if (searchKeyword && !item.location_name.includes(searchKeyword)) {
      return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;color:#94A3B8;padding:20px;">無符合條件的縣市資料</td></tr>`;
    return;
  }

  filtered.forEach(item => {
    const slot = item.forecasts[currentPeriodIndex] || item.forecasts[0] || {};
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><b>${item.location_name}</b></td>
      <td><span class="badge-region">${item.region}</span></td>
      <td style="color:#64748B;">${slot.period_title || '--'}</td>
      <td>${slot.wx_icon || ''} ${slot.wx || '--'}</td>
      <td style="color:#0284C7;font-weight:700;">${slot.min_t !== null ? slot.min_t + '°C' : '--'}</td>
      <td style="color:#EF4444;font-weight:700;">${slot.max_t !== null ? slot.max_t + '°C' : '--'}</td>
      <td style="color:#0284C7;font-weight:700;">💧 ${slot.pop !== null ? slot.pop + '%' : '--'}</td>
      <td style="color:#D97706;">${slot.ci || '--'}</td>
      <td><button class="btn-view-county" onclick="selectCounty('${item.location_name}')">查看概況</button></td>
    `;
    tbody.appendChild(tr);
  });
}

// 12. 本地靜態 Fallback 解析輔助函式
function parseFallbackData(rawJson) {
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

  function getWxIcon(wx) {
    if (!wx) return "⛅";
    if (wx.includes("雷")) return "⛈️";
    if (wx.includes("雨")) return (wx.includes("大雨") || wx.includes("豪雨")) ? "🌧️" : "🌦️";
    if (wx.includes("陰")) return "☁️";
    if (wx.includes("晴") && wx.includes("多雲")) return "🌤️";
    if (wx.includes("晴")) return "☀️";
    if (wx.includes("多雲")) return "⛅";
    return "⛅";
  }

  function getTitle(idx) {
    return idx === 0 ? "今晚至明晨" : (idx === 1 ? "明日白天" : "明日晚上");
  }

  const locations = rawJson?.records?.location || [];
  const results = locations.map(loc => {
    const rawName = loc.locationName.replace(/台/g, "臺");
    const meta = TAIWAN_COUNTIES[rawName] || {};
    const elements = loc.weatherElement || [];
    const slotMap = {};

    elements.forEach(elem => {
      const eName = elem.elementName;
      (elem.time || []).forEach(t => {
        const key = `${t.startTime}_${t.endTime}`;
        if (!slotMap[key]) slotMap[key] = { startTime: t.startTime, endTime: t.endTime };
        const val = t.parameter?.parameterName;
        if (eName === "Wx") slotMap[key].wx = val;
        else if (["PoP", "PoP12h"].includes(eName)) slotMap[key].pop = val ? parseFloat(val) : null;
        else if (eName === "MinT") slotMap[key].minT = val ? parseFloat(val) : null;
        else if (eName === "MaxT") slotMap[key].maxT = val ? parseFloat(val) : null;
        else if (eName === "CI") slotMap[key].ci = val;
      });
    });

    const sorted = Object.values(slotMap).sort((a, b) => a.startTime.localeCompare(b.startTime));
    const forecasts = sorted.map((s, idx) => ({
      period_index: idx,
      period_title: getTitle(idx),
      start_time: s.startTime,
      end_time: s.endTime,
      wx: s.wx || "多雲",
      wx_icon: getWxIcon(s.wx),
      pop: s.pop,
      min_t: s.minT,
      max_t: s.maxT,
      ci: s.ci || "舒適"
    }));

    return {
      location_name: rawName,
      county_code: meta.code || "",
      region: meta.region || "其他",
      lat: meta.lat || 0,
      lon: meta.lon || 0,
      forecasts
    };
  });

  return {
    success: true,
    status: "demo",
    message: "已載入靜態示範資料 (Demo Data)。",
    data: results
  };
}

"""
Taiwan Weather Forecast GIS Dashboard
台灣氣象預報 GIS 網頁儀表板
中央氣象署 CWA Open Data × Python × SQLite × Streamlit × Folium × Plotly
"""
import os
import sys
from datetime import datetime
import pandas as pd
import pytz
import streamlit as st

# 設定專案路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.location_service import get_all_locations, normalize_location_name
from services.cwa_client import fetch_forecast_data, get_cwa_api_key
from services.cwa_parser import parse_cwa_response
from services.database import (
    init_database,
    save_forecasts,
    get_all_forecasts_df,
    get_available_time_slots,
    get_database_stats
)
from components.weather_cards import render_weather_cards
from components.weather_map import render_weather_map
from components.weather_chart import render_weather_charts
from components.weather_table import render_weather_table

TAIPEI_TZ = pytz.timezone("Asia/Taipei")

# 1. 頁面基礎設定
st.set_page_config(
    page_title="Taiwan Weather Forecast | 台灣氣象預報 GIS",
    page_icon="🌦️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 注入客製化 CSS 提升視覺美感
st.markdown("""
<style>
    /* 全站字體與主色系調整 */
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans TC", sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #0284C7 100%);
        padding: 24px 28px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .sub-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.18);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 13px;
        margin-right: 8px;
        font-weight: 500;
    }
    .status-badge-live {
        background-color: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
    }
    .status-badge-demo {
        background-color: #F59E0B;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
    }
    .status-badge-error {
        background-color: #EF4444;
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 700;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        font-weight: 600;
        border: none;
        padding: 8px 16px;
    }
    .stButton>button:hover {
        background-color: #2563EB;
        color: white;
    }
</style>
""", unsafe_allow_html=True)


# 2. 快取資料載入函式 (TTL 1800 秒)
@st.cache_data(ttl=1800)
def load_and_sync_weather_data() -> dict:
    """從 CWA API 取得氣象資料並同步至 SQLite 資料庫。"""
    init_database()
    raw_data, status, message = fetch_forecast_data()
    saved_count = 0
    if raw_data:
        forecasts = parse_cwa_response(raw_data)
        if forecasts:
            saved_count = save_forecasts(forecasts)
    return {
        "status": status,
        "message": message,
        "saved_count": saved_count,
        "sync_time": datetime.now(TAIPEI_TZ).strftime("%Y-%m-%d %H:%M:%S")
    }


def main():
    # 確保資料庫初始化與載入
    sync_result = load_and_sync_weather_data()
    status = sync_result["status"]
    message = sync_result["message"]

    # 讀取資料庫現有預報資料
    all_df = get_all_forecasts_df()
    stats = get_database_stats()

    # 3. 側邊欄控制面板
    with st.sidebar:
        st.markdown("### ⚙️ 控制面板與篩選")

        # 手動更新按鈕
        if st.button("🔄 立即更新 CWA 氣象資料"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # 縣市選擇 (預設「臺中市」)
        all_counties = get_all_locations()
        default_index = all_counties.index("臺中市") if "臺中市" in all_counties else 0
        selected_county = st.selectbox(
            "📍 選擇縣市",
            options=all_counties,
            index=default_index,
            help="選擇欲檢視即時氣象預報與趨勢圖之縣市"
        )

        # 預報時段選單
        time_slots = get_available_time_slots()
        slot_options = []
        if time_slots:
            for s, e in time_slots:
                s_fmt = s.replace("T", " ")[:16]
                e_fmt = e.replace("T", " ")[:16]
                slot_options.append(f"{s_fmt} ~ {e_fmt}")
            
            selected_slot_str = st.selectbox(
                "🕒 預報時段",
                options=slot_options,
                index=0,
                help="切換 GIS 地圖與 KPI 卡片所展示之預報區段"
            )
            selected_slot_idx = slot_options.index(selected_slot_str)
            selected_start_time, selected_end_time = time_slots[selected_slot_idx]
        else:
            selected_start_time, selected_end_time = None, None
            st.warning("目前無可用預報時段。")

        # 地圖指標切換
        map_metric = st.radio(
            "🗺️ 地圖著色指標",
            options=["最高溫", "最低溫", "降雨機率"],
            index=0,
            horizontal=True
        )

        st.markdown("---")
        st.markdown("### 📊 系統資料庫資訊")
        st.write(f"• 總預報筆數: **{stats['total_records']}** 筆")
        st.write(f"• 涵蓋縣市: **{stats['locations_count']}** / 22")
        st.write(f"• 最近更新: **{stats['last_fetched_at'] or '無'}**")

        st.markdown("---")
        st.markdown("""
        <div style="font-size:12px; color:#6B7280; line-height:1.6;">
            <b>資料來源說明：</b><br>
            中央氣象署開放資料平臺 (CWA Open Data)<br>
            預報資料集：<code>F-C0032-001</code><br>
            GIS 座標系統：WGS84 (EPSG:4326)
        </div>
        """, unsafe_allow_html=True)

    # 4. 頂部主標題區
    status_badge_html = ""
    if status == "live":
        status_badge_html = '<span class="status-badge-live">● Live Data (即時連線)</span>'
    elif status == "demo":
        status_badge_html = '<span class="status-badge-demo">▲ Demo Data (示範資料模式)</span>'
    else:
        status_badge_html = '<span class="status-badge-error">✕ API Error (連線異常)</span>'

    last_update_display = stats['last_fetched_at'] or sync_result['sync_time']

    st.markdown(f"""
    <div class="main-header">
        <div style="font-size: 13px; font-weight: 600; letter-spacing: 1px; color: #93C5FD; margin-bottom: 4px;">
            AI 創新微課程專案
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <h1 style="margin: 0; font-size: 26px; font-weight: 800; color: white;">
                    Taiwan Weather Forecast 台灣氣象預報 GIS Dashboard
                </h1>
                <div style="margin-top: 8px;">
                    <span class="sub-badge">中央氣象署 CWA Open Data</span>
                    <span class="sub-badge">Python 3.14</span>
                    <span class="sub-badge">SQLite3</span>
                    <span class="sub-badge">Folium GIS</span>
                    <span class="sub-badge">Plotly</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div>{status_badge_html}</div>
                <div style="font-size: 12px; color: #E2E8F0; margin-top: 6px;">
                    最後同步時間: {last_update_display}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 若為示範模式，顯示明顯提示橫幅
    if status == "demo":
        st.warning(f"ℹ️ **提示：** {message}")

    # 5. 取得目前選定縣市與時段之資料
    county_df = all_df[all_df["location_name"] == selected_county]
    if selected_start_time and selected_end_time:
        slot_df = all_df[(all_df["start_time"] == selected_start_time) & (all_df["end_time"] == selected_end_time)]
        current_forecast_df = county_df[(county_df["start_time"] == selected_start_time) & (county_df["end_time"] == selected_end_time)]
        current_forecast = current_forecast_df.iloc[0].to_dict() if not current_forecast_df.empty else None
    else:
        slot_df = pd.DataFrame()
        current_forecast = None

    # 6. KPI 卡片區
    st.markdown(f"### 📌 【{selected_county}】當前預報概況 ({selected_slot_str if slot_options else '無時段'})")
    render_weather_cards(current_forecast, selected_county)

    st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)

    # 7. 主內容區 (左側 Folium 地圖，右側 Plotly 趨勢圖)
    map_col, chart_col = st.columns([1.1, 0.9])

    with map_col:
        st.markdown(f"### 🗺️ 台灣全區氣象 GIS 地圖（指標：{map_metric}）")
        render_weather_map(slot_df, metric_type=map_metric, highlight_county=selected_county)

    with chart_col:
        st.markdown(f"### 📊 【{selected_county}】36小時氣象趨勢圖")
        render_weather_charts(county_df, selected_county)

    st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

    # 8. 完整資料表區
    st.markdown("### 📋 全台 22 縣市完整預報資料表")
    render_weather_table(all_df)


if __name__ == "__main__":
    main()

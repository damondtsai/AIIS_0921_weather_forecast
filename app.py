"""
Taiwan Weather Forecast GIS Dashboard (CWA V8 Style)
交通部中央氣象署風格之台灣氣象預報 GIS 空間視覺化儀表板
"""
import os
import sys
from datetime import datetime
import pandas as pd
import pytz
import streamlit as st

# 設定專案路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from services.location_service import get_all_locations, normalize_location_name, TAIWAN_COUNTIES
from services.cwa_client import fetch_forecast_data
from services.cwa_parser import parse_cwa_response
from services.database import (
    init_database,
    save_forecasts,
    get_all_forecasts_df,
    get_available_time_slots,
    get_database_stats
)
from components.weather_cards import render_weather_cards, render_cwa_hero_summary
from components.weather_map import render_weather_map
from components.weather_chart import render_weather_charts
from components.weather_table import render_weather_table

TAIPEI_TZ = pytz.timezone("Asia/Taipei")

# 1. 頁面設定
st.set_page_config(
    page_title="中央氣象署 台灣氣象預報 GIS 資訊網",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CWA V8 專屬 CSS 主題樣式
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans TC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 頂部 CWA 官方海藍導覽列 */
    .cwa-navbar {
        background: linear-gradient(90deg, #0B4F8A 0%, #086EB6 40%, #0093D8 100%);
        padding: 16px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(11, 79, 138, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }
    .cwa-brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .cwa-logo-icon {
        background: rgba(255, 255, 255, 0.2);
        border: 2px solid rgba(255, 255, 255, 0.4);
        width: 44px;
        height: 44px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }
    .cwa-title {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 0.5px;
        color: #FFFFFF;
        margin: 0;
    }
    .cwa-subtitle {
        font-size: 12px;
        color: #E0F2FE;
        font-weight: 500;
        margin-top: 2px;
    }
    .cwa-badge-live {
        background: #10B981;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        box-shadow: 0 2px 5px rgba(16, 185, 129, 0.3);
    }
    .cwa-badge-demo {
        background: #F59E0B;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }
    .section-header {
        border-left: 5px solid #0284C7;
        padding-left: 10px;
        font-size: 18px;
        font-weight: 800;
        color: #0F172A;
        margin: 18px 0 12px 0;
    }
</style>
""", unsafe_allow_html=True)


# 3. 快取資料載入函式 (TTL 1800 秒)
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
    sync_result = load_and_sync_weather_data()
    status = sync_result["status"]
    message = sync_result["message"]

    all_df = get_all_forecasts_df()
    stats = get_database_stats()

    # 4. 側邊欄控制與快速篩選
    with st.sidebar:
        st.markdown("### ⚙️ 氣象圖台控制項")
        
        # 立即更新按鈕
        if st.button("🔄 立即更新 CWA 即時氣象"):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

        # 縣市選擇（預設「臺中市」）
        all_counties = get_all_locations()
        default_index = all_counties.index("臺中市") if "臺中市" in all_counties else 0
        selected_county = st.selectbox(
            "📍 選擇預報縣市",
            options=all_counties,
            index=default_index,
            help="切換欲檢視之台灣行政區預報"
        )

        # 預報時段切換
        time_slots = get_available_time_slots()
        slot_options = []
        if time_slots:
            for idx, (s, e) in enumerate(time_slots):
                s_fmt = s.replace("T", " ")[:16]
                e_fmt = e.replace("T", " ")[:16]
                period_title = "時段 1 (今晚/明日)" if idx == 0 else f"時段 {idx+1}"
                slot_options.append(f"{period_title} ({s_fmt[5:]} ~ {e_fmt[5:]})")
            
            selected_slot_str = st.selectbox(
                "🕒 地圖顯示時段",
                options=slot_options,
                index=0,
                help="切換 GIS 地圖上各縣市顯示的預報時段"
            )
            selected_slot_idx = slot_options.index(selected_slot_str)
            selected_start_time, selected_end_time = time_slots[selected_slot_idx]
        else:
            selected_start_time, selected_end_time = None, None

        # 地圖著色指標
        map_metric = st.radio(
            "🗺️ 地圖圖層指標",
            options=["最高溫", "最低溫", "降雨機率"],
            index=0,
            horizontal=True
        )

        st.markdown("---")
        st.markdown("### ℹ️ 資料庫狀態")
        st.write(f"• 同步時間: **{stats['last_fetched_at'] or sync_result['sync_time']}**")
        st.write(f"• 預報筆數: **{stats['total_records']}** 筆 (22 縣市)")
        st.caption("資料來源：交通部中央氣象署 CWA Open Data (F-C0032-001)")

    # 5. 頂部 CWA 品牌導覽列
    status_badge_html = (
        '<span class="cwa-badge-live">● CWA 即時連線 (Live)</span>'
        if status == "live" else
        '<span class="cwa-badge-demo">▲ 示範資料模式 (Demo)</span>'
    )

    st.markdown(f"""
    <div class="cwa-navbar">
        <div class="cwa-brand">
            <div class="cwa-logo-icon">🌤️</div>
            <div>
                <div class="cwa-title">交通部中央氣象署 氣象預報全球資訊網</div>
                <div class="cwa-subtitle">Taiwan Weather Forecast GIS Dashboard · 今明 36 小時天氣預報</div>
            </div>
        </div>
        <div style="text-align: right;">
            <div>{status_badge_html}</div>
            <div style="font-size: 12px; color: #E0F2FE; margin-top: 4px;">
                台北標準時間: {datetime.now(TAIPEI_TZ).strftime('%Y/%m/%d %H:%M')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if status == "demo":
        st.warning(f"ℹ️ **提示：** {message}")

    # 6. 當前選定縣市資料
    county_df = all_df[all_df["location_name"] == selected_county]
    if selected_start_time and selected_end_time:
        slot_df = all_df[(all_df["start_time"] == selected_start_time) & (all_df["end_time"] == selected_end_time)]
    else:
        slot_df = pd.DataFrame()

    # 7. 主版面配置 (仿 CWA V8：左側地圖，右側選定縣市 36 小時預報卡片與曲線)
    col_map, col_detail = st.columns([1.1, 0.9])

    with col_map:
        st.markdown(f'<div class="section-header">🗺️ 台灣各縣市氣象圖台（指標：{map_metric}）</div>', unsafe_allow_html=True)
        render_weather_map(slot_df, metric_type=map_metric, highlight_county=selected_county)

    with col_detail:
        st.markdown(f'<div class="section-header">📍 【{selected_county}】今明 36 小時天氣預報</div>', unsafe_allow_html=True)
        # 頂部縣市概況看板
        render_cwa_hero_summary(selected_county, county_df)
        
        # 3 時段卡片
        render_weather_cards(county_df, selected_county)

        st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
        # 36 小時氣溫與降雨趨勢圖
        render_weather_charts(county_df, selected_county)

    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)

    # 8. 下方全台分區預報矩陣資料表 (CWA 風格)
    st.markdown('<div class="section-header">📋 全台 22 縣市天氣預報清單</div>', unsafe_allow_html=True)
    render_weather_table(all_df)


if __name__ == "__main__":
    main()

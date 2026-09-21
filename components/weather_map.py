"""
Weather GIS Map Component
使用 Folium 與台灣 22 縣市 GeoJSON 繪製互動式氣象地圖，支援指標切換、分級著色、懸浮提示與詳細氣象 Popup。
"""
import json
import os
from typing import Any, Dict, Optional
import folium
from folium.plugins import Fullscreen
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from services.location_service import normalize_location_name

GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "taiwan_counties.geojson"
)


def _get_temp_color(temp: Optional[float]) -> str:
    """
    溫度分級顏色：
    - < 20°C: 藍色 (#3B82F6)
    - 20–25°C: 綠色 (#10B981)
    - 25–30°C: 橙色 (#F59E0B)
    - > 30°C: 紅色 (#EF4444)
    - 無資料: 灰色 (#9CA3AF)
    """
    if temp is None:
        return "#9CA3AF"
    if temp < 20:
        return "#3B82F6"
    elif temp <= 25:
        return "#10B981"
    elif temp <= 30:
        return "#F59E0B"
    else:
        return "#EF4444"


def _get_pop_color(pop: Optional[float]) -> str:
    """
    降雨機率分級顏色：
    - 0–20%: 淺藍 (#93C5FD)
    - 20–50%: 藍色 (#3B82F6)
    - 50–80%: 深藍 (#1D4ED8)
    - > 80%: 紫色 (#6D28D9)
    - 無資料: 灰色 (#9CA3AF)
    """
    if pop is None:
        return "#9CA3AF"
    if pop < 20:
        return "#93C5FD"
    elif pop <= 50:
        return "#3B82F6"
    elif pop <= 80:
        return "#1D4ED8"
    else:
        return "#6D28D9"


def _build_popup_html(county_name: str, forecast: Optional[Dict[str, Any]]) -> str:
    """產生精美繁體中文氣象資訊 Popup HTML。"""
    if not forecast:
        return f"""
        <div style="font-family: sans-serif; min-width: 180px; padding: 6px;">
            <h4 style="margin:0 0 6px 0; color:#1E3A8A;">{county_name}</h4>
            <p style="color:#6B7280; font-size:12px; margin:0;">目前時段無此縣市預報資料</p>
        </div>
        """

    wx = forecast.get("wx") or "--"
    pop = forecast.get("pop")
    pop_str = f"{int(pop)}%" if pop is not None else "--"
    min_t = forecast.get("min_t")
    min_t_str = f"{min_t:.1f}°C" if min_t is not None else "--"
    max_t = forecast.get("max_t")
    max_t_str = f"{max_t:.1f}°C" if max_t is not None else "--"
    ci = forecast.get("ci") or "--"
    start_t = forecast.get("start_time", "").replace("T", " ")[:16]
    end_t = forecast.get("end_time", "").replace("T", " ")[:16]
    fetched_at = forecast.get("fetched_at", "").replace("T", " ")[:19]

    return f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial;
                min-width: 230px; padding: 8px 10px; line-height: 1.5; color: #1F2937;">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #3B82F6; padding-bottom: 4px; margin-bottom: 6px;">
            <h3 style="margin: 0; color: #1E3A8A; font-size: 16px; font-weight: 700;">{county_name}</h3>
            <span style="background:#DBEAFE; color:#1D4ED8; font-size:11px; padding:2px 6px; border-radius:4px; font-weight:600;">{wx}</span>
        </div>
        <div style="font-size: 12px; color: #4B5563; margin-bottom: 6px;">
            時段: {start_t} ~ {end_t}
        </div>
        <table style="width:100%; font-size:12px; border-collapse:collapse; margin-bottom: 6px;">
            <tr>
                <td style="color:#6B7280; padding:2px 0;">最高溫度:</td>
                <td style="font-weight:700; color:#DC2626; text-align:right;">{max_t_str}</td>
            </tr>
            <tr>
                <td style="color:#6B7280; padding:2px 0;">最低溫度:</td>
                <td style="font-weight:700; color:#2563EB; text-align:right;">{min_t_str}</td>
            </tr>
            <tr>
                <td style="color:#6B7280; padding:2px 0;">降雨機率:</td>
                <td style="font-weight:700; color:#0D9488; text-align:right;">{pop_str}</td>
            </tr>
            <tr>
                <td style="color:#6B7280; padding:2px 0;">舒適度:</td>
                <td style="font-weight:600; color:#D97706; text-align:right;">{ci}</td>
            </tr>
        </table>
        <div style="font-size: 10px; color: #9CA3AF; border-top: 1px dashed #E5E7EB; padding-top: 4px;">
            最後更新: {fetched_at}
        </div>
    </div>
    """


def render_weather_map(
    slot_df: pd.DataFrame,
    metric_type: str = "最高溫",
    highlight_county: Optional[str] = None
) -> None:
    """
    建立並顯示 Folium GIS 台灣氣象地圖。
    
    參數:
    - slot_df: 特定預報時段之各縣市 DataFrame
    - metric_type: "最高溫" | "最低溫" | "降雨機率"
    - highlight_county: 目前選定的縣市名稱
    """
    if not os.path.exists(GEOJSON_PATH):
        st.error("找不到 GeoJSON 地圖資料檔 (data/taiwan_counties.geojson)。")
        return

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # 建立縣市預報字典以供快速匹配
    forecast_dict: Dict[str, Dict[str, Any]] = {}
    if not slot_df.empty:
        for _, row in slot_df.iterrows():
            norm_name = normalize_location_name(row["location_name"])
            if norm_name:
                forecast_dict[norm_name] = row.to_dict()

    # 初始建立地圖 (中心設於台灣中部)
    m = folium.Map(
        location=[23.7, 120.95],
        zoom_start=7.4,
        tiles="CartoDB positron",
        control_scale=True,
    )
    Fullscreen(position="topright").add_to(m)

    # 根據選定指標為 GeoJSON 各 Feature 設定樣式
    def style_function(feature):
        props = feature.get("properties", {})
        raw_name = props.get("COUNTYNAME") or props.get("name")
        c_name = normalize_location_name(raw_name)
        fc = forecast_dict.get(c_name)

        if metric_type == "最高溫":
            val = fc.get("max_t") if fc else None
            fill_color = _get_temp_color(val)
        elif metric_type == "最低溫":
            val = fc.get("min_t") if fc else None
            fill_color = _get_temp_color(val)
        else:  # 降雨機率
            val = fc.get("pop") if fc else None
            fill_color = _get_pop_color(val)

        is_highlight = (c_name == highlight_county)
        return {
            "fillColor": fill_color,
            "color": "#1E3A8A" if is_highlight else "#64748B",
            "weight": 3.5 if is_highlight else 1.2,
            "fillOpacity": 0.85 if is_highlight else 0.65,
        }

    # 建立 GeoJson 圖層與 Popup / Tooltip
    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        raw_name = props.get("COUNTYNAME") or props.get("name")
        c_name = normalize_location_name(raw_name)
        fc = forecast_dict.get(c_name)

        # 浮動提示文字
        if metric_type == "最高溫":
            metric_val = f"{fc.get('max_t')}°C" if (fc and fc.get('max_t') is not None) else "無資料"
        elif metric_type == "最低溫":
            metric_val = f"{fc.get('min_t')}°C" if (fc and fc.get('min_t') is not None) else "無資料"
        else:
            metric_val = f"{int(fc.get('pop'))}%" if (fc and fc.get('pop') is not None) else "無資料"

        wx_desc = fc.get("wx", "") if fc else ""
        tooltip_txt = f"<b>{c_name}</b> | {metric_type}: {metric_val} {('(' + wx_desc + ')') if wx_desc else ''}"

        popup_html = _build_popup_html(c_name, fc)
        popup = folium.Popup(folium.Html(popup_html, script=True), max_width=300)

        # 建立單一 Feature 圖層
        geo_feature = folium.GeoJson(
            feature,
            style_function=style_function,
            tooltip=folium.Tooltip(tooltip_txt),
            popup=popup,
            name=c_name
        )
        geo_feature.add_to(m)

        # 若為被選定縣市，在中心點放置醒目 Pulse 標記
        if c_name == highlight_county and props.get("lat") and props.get("lon"):
            folium.CircleMarker(
                location=[props["lat"], props["lon"]],
                radius=8,
                color="#EF4444",
                fill=True,
                fill_color="#FDE047",
                fill_opacity=0.9,
                weight=3,
                popup=popup,
                tooltip=f"★ 目前選定: {c_name}"
            ).add_to(m)

    # 建立自訂圖例 HTML
    if metric_type in ("最高溫", "最低溫"):
        legend_html = """
        <div style="position: fixed; bottom: 30px; right: 20px; z-index: 1000;
                    background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(4px);
                    padding: 10px 14px; border-radius: 8px; border: 1px solid #E2E8F0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-size: 12px; font-family: sans-serif;">
            <div style="font-weight: 700; margin-bottom: 6px; color: #1E293B;">氣溫圖例 (°C)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#EF4444; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> > 30°C (高溫炎熱)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#F59E0B; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 25 ~ 30°C (溫暖)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#10B981; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 20 ~ 25°C (舒適)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#3B82F6; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> < 20°C (偏涼)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#9CA3AF; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 無資料</div>
        </div>
        """
    else:
        legend_html = """
        <div style="position: fixed; bottom: 30px; right: 20px; z-index: 1000;
                    background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(4px);
                    padding: 10px 14px; border-radius: 8px; border: 1px solid #E2E8F0;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-size: 12px; font-family: sans-serif;">
            <div style="font-weight: 700; margin-bottom: 6px; color: #1E293B;">降雨機率圖例 (%)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#6D28D9; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> > 80% (極易降雨)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#1D4ED8; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 50 ~ 80% (高降雨率)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#3B82F6; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 20 ~ 50% (局部可能降雨)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#93C5FD; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 0 ~ 20% (降雨機率低)</div>
            <div><span style="display:inline-block; width:14px; height:14px; background:#9CA3AF; border-radius:3px; vertical-align:middle; margin-right:6px;"></span> 無資料</div>
        </div>
        """

    m.get_root().html.add_child(folium.Element(legend_html))

    # 渲染至 Streamlit
    st_folium(m, width="100%", height=560, returned_objects=[])

"""
Weather GIS Map Component (CWA V8 Style)
仿照中央氣象署全球資訊網 V8 版首頁，呈現台灣地圖與各縣市氣象微章、分級著色與詳細 Popup。
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
from components.weather_cards import get_wx_icon

GEOJSON_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "taiwan_counties.geojson"
)


def _get_temp_color(temp: Optional[float]) -> str:
    """溫度分級顏色 (CWA 風格)。"""
    if temp is None:
        return "#94A3B8"
    if temp < 18:
        return "#2563EB"
    elif temp < 24:
        return "#0284C7"
    elif temp < 28:
        return "#10B981"
    elif temp <= 32:
        return "#F59E0B"
    else:
        return "#EF4444"


def _get_pop_color(pop: Optional[float]) -> str:
    """降雨機率分級顏色 (CWA 風格)。"""
    if pop is None:
        return "#94A3B8"
    if pop < 20:
        return "#BAE6FD"
    elif pop <= 40:
        return "#38BDF8"
    elif pop <= 70:
        return "#0284C7"
    else:
        return "#4338CA"


def _build_cwa_popup(county_name: str, forecast: Optional[Dict[str, Any]]) -> str:
    """產生 CWA 官方氣象署風格之彈出資訊窗。"""
    if not forecast:
        return f"""
        <div style="font-family: sans-serif; padding: 6px; min-width: 160px;">
            <b style="color:#0B4F8A; font-size:14px;">{county_name}</b>
            <p style="color:#64748B; font-size:12px; margin:4px 0 0 0;">目前無預報資料</p>
        </div>
        """

    wx = forecast.get("wx") or "--"
    icon = get_wx_icon(wx)
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
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                min-width: 220px; padding: 10px; color: #1E293B; line-height: 1.4;">
        <div style="background: linear-gradient(135deg, #0B4F8A 0%, #0284C7 100%);
                    color: white; padding: 8px 12px; border-radius: 8px 8px 0 0; margin: -10px -10px 10px -10px;
                    display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 16px; font-weight: 800;">{county_name}</span>
            <span style="font-size: 20px;">{icon}</span>
        </div>
        <div style="font-size: 12px; color: #64748B; margin-bottom: 8px;">
            🕒 {start_t[5:]} ~ {end_t[5:]}
        </div>
        <div style="background: #F1F5F9; border-radius: 6px; padding: 8px; margin-bottom: 8px; font-size: 13px;">
            <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                <span style="color:#64748B;">天氣狀況:</span>
                <b style="color:#0F172A;">{wx}</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                <span style="color:#64748B;">溫度區間:</span>
                <b style="color:#DC2626;">{min_t_str} ~ {max_t_str}</b>
            </div>
            <div style="display:flex; justify-content:space-between; margin-bottom: 4px;">
                <span style="color:#64748B;">降雨機率:</span>
                <b style="color:#0284C7;">💧 {pop_str}</b>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span style="color:#64748B;">舒適度:</span>
                <b style="color:#D97706;">{ci}</b>
            </div>
        </div>
        <div style="font-size: 10px; color: #94A3B8; text-align: right;">
            資料來源：中央氣象署 ({fetched_at[5:16]})
        </div>
    </div>
    """


def render_weather_map(
    slot_df: pd.DataFrame,
    metric_type: str = "最高溫",
    highlight_county: Optional[str] = None
) -> None:
    """
    建立並顯示 CWA V8 風格之互動氣象 GIS 地圖。
    """
    if not os.path.exists(GEOJSON_PATH):
        st.error("找不到 GeoJSON 地圖圖資。")
        return

    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    # 建立縣市預報字典
    forecast_dict: Dict[str, Dict[str, Any]] = {}
    if not slot_df.empty:
        for _, row in slot_df.iterrows():
            norm_name = normalize_location_name(row["location_name"])
            if norm_name:
                forecast_dict[norm_name] = row.to_dict()

    # 地圖底圖：採用淡雅簡約底圖，突出台灣各縣市輪廓
    m = folium.Map(
        location=[23.7, 120.95],
        zoom_start=7.4,
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        control_scale=True,
    )
    Fullscreen(position="topright").add_to(m)

    # 樣式定義函式
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
            "color": "#0B4F8A" if is_highlight else "#94A3B8",
            "weight": 3.0 if is_highlight else 1.0,
            "fillOpacity": 0.85 if is_highlight else 0.65,
        }

    # 加入各縣市 Polygon 與天氣標籤 Badge
    for feature in geojson_data.get("features", []):
        props = feature.get("properties", {})
        raw_name = props.get("COUNTYNAME") or props.get("name")
        c_name = normalize_location_name(raw_name)
        fc = forecast_dict.get(c_name)

        wx_desc = fc.get("wx", "") if fc else ""
        icon = get_wx_icon(wx_desc)
        min_t = fc.get("min_t")
        max_t = fc.get("max_t")
        pop = fc.get("pop")

        temp_text = f"{int(min_t)}~{int(max_t)}°" if (min_t is not None and max_t is not None) else ""
        pop_text = f"{int(pop)}%" if pop is not None else ""

        tooltip_txt = f"<b>{c_name}</b> · {wx_desc} · {temp_text} (降雨: {pop_text})"
        popup_html = _build_cwa_popup(c_name, fc)
        popup = folium.Popup(folium.Html(popup_html, script=True), max_width=280)

        # Polygon 圖層
        folium.GeoJson(
            feature,
            style_function=style_function,
            tooltip=folium.Tooltip(tooltip_txt),
            popup=popup,
            name=c_name
        ).add_to(m)

        # 在縣市中心點加入 CWA 氣象膠囊標籤 (Weather Pill)
        lat = props.get("lat")
        lon = props.get("lon")
        if lat and lon:
            is_highlight = (c_name == highlight_county)
            border_style = "2px solid #DC2626; box-shadow: 0 0 8px rgba(220,38,38,0.6);" if is_highlight else "1px solid #CBD5E1;"
            bg_color = "#FFFBEB" if is_highlight else "#FFFFFF"
            
            # CWA 徽章 HTML
            div_html = f"""
            <div style="background: {bg_color}; border: {border_style}; border-radius: 14px;
                        padding: 2px 6px; font-family: sans-serif; font-size: 11px; font-weight: 700;
                        white-space: nowrap; box-shadow: 0 2px 4px rgba(0,0,0,0.15); display: flex;
                        align-items: center; gap: 3px; cursor: pointer; color: #1E293B;">
                <span>{icon}</span>
                <span>{c_name[:2]}</span>
                <span style="color: #DC2626; font-size: 10px;">{int(max_t) if max_t is not None else ''}°</span>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                icon=folium.DivIcon(html=div_html, icon_size=(70, 20), icon_anchor=(35, 10)),
                popup=popup,
                tooltip=tooltip_txt
            ).add_to(m)

    # CWA 風格圖例
    legend_title = f"氣溫分級 (°C)" if metric_type in ("最高溫", "最低溫") else "降雨機率 (%)"
    if metric_type in ("最高溫", "最低溫"):
        legend_items = """
        <div><span style="display:inline-block;width:12px;height:12px;background:#EF4444;border-radius:2px;margin-right:5px;"></span> > 32°C (高溫)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#F59E0B;border-radius:2px;margin-right:5px;"></span> 28 ~ 32°C (炎熱)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#10B981;border-radius:2px;margin-right:5px;"></span> 24 ~ 28°C (溫和)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#0284C7;border-radius:2px;margin-right:5px;"></span> 18 ~ 24°C (舒適)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#2563EB;border-radius:2px;margin-right:5px;"></span> < 18°C (稍涼)</div>
        """
    else:
        legend_items = """
        <div><span style="display:inline-block;width:12px;height:12px;background:#4338CA;border-radius:2px;margin-right:5px;"></span> > 70% (高機率降雨)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#0284C7;border-radius:2px;margin-right:5px;"></span> 40 ~ 70% (局部陣雨)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#38BDF8;border-radius:2px;margin-right:5px;"></span> 20 ~ 40% (零星短暫雨)</div>
        <div><span style="display:inline-block;width:12px;height:12px;background:#BAE6FD;border-radius:2px;margin-right:5px;"></span> 0 ~ 20% (降雨機率低)</div>
        """

    legend_html = f"""
    <div style="position: fixed; bottom: 25px; right: 20px; z-index: 1000;
                background: rgba(255, 255, 255, 0.95); border: 1px solid #CBD5E1;
                border-radius: 8px; padding: 10px 14px; font-size: 11px; font-family: sans-serif;
                box-shadow: 0 4px 10px rgba(0,0,0,0.12); line-height: 1.6;">
        <div style="font-weight: 800; color: #0B4F8A; margin-bottom: 4px; border-bottom: 1px solid #E2E8F0; padding-bottom: 2px;">
            {legend_title}
        </div>
        {legend_items}
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width="100%", height=580, returned_objects=[])

"""
Weather Cards Component
呈現當前選定縣市之各項氣象 KPI 卡片 (最高溫、最低溫、降雨機率、天氣現象、舒適度)。
"""
from typing import Any, Dict, Optional
import streamlit as st


def _get_wx_icon(wx: Optional[str]) -> str:
    """根據天氣現象關鍵字回傳對應的 Emoji/圖示。"""
    if not wx:
        return "⛅"
    if "雷" in wx:
        return "⛈️"
    if "雨" in wx:
        return "🌧️"
    if "晴" in wx and "雲" not in wx:
        return "☀️"
    if "晴" in wx and "多雲" in wx:
        return "🌤️"
    if "陰" in wx:
        return "☁️"
    if "多雲" in wx:
        return "⛅"
    if "霧" in wx or "霾" in wx:
        return "🌫️"
    return "⛅"


def render_weather_cards(forecast_data: Optional[Dict[str, Any]], location_name: str) -> None:
    """
    渲染天氣 KPI 卡片。
    forecast_data 應包含: wx, pop, min_t, max_t, ci, start_time, end_time, fetched_at
    """
    if not forecast_data:
        st.info(f"尚無 {location_name} 在選定時段之預報資料。")
        return

    wx = forecast_data.get("wx") or "未知"
    pop = forecast_data.get("pop")
    min_t = forecast_data.get("min_t")
    max_t = forecast_data.get("max_t")
    ci = forecast_data.get("ci") or "無描述"
    icon = _get_wx_icon(wx)

    pop_str = f"{int(pop)}%" if pop is not None else "--"
    min_t_str = f"{min_t:.1f}°C" if min_t is not None else "--"
    max_t_str = f"{max_t:.1f}°C" if max_t is not None else "--"

    # 使用 Streamlit 欄位渲染專業卡片
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
                        padding: 18px 14px; border-radius: 12px; color: white; text-align: center;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 500; opacity: 0.9;">天氣現象</div>
                <div style="font-size: 28px; margin: 4px 0;">{icon}</div>
                <div style="font-size: 16px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{wx}">{wx}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #B91C1C 0%, #EF4444 100%);
                        padding: 18px 14px; border-radius: 12px; color: white; text-align: center;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 500; opacity: 0.9;">最高氣溫</div>
                <div style="font-size: 28px; margin: 4px 0;">🌡️</div>
                <div style="font-size: 20px; font-weight: 700;">{max_t_str}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0369A1 0%, #0284C7 100%);
                        padding: 18px 14px; border-radius: 12px; color: white; text-align: center;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 500; opacity: 0.9;">最低氣溫</div>
                <div style="font-size: 28px; margin: 4px 0;">❄️</div>
                <div style="font-size: 20px; font-weight: 700;">{min_t_str}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%);
                        padding: 18px 14px; border-radius: 12px; color: white; text-align: center;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 500; opacity: 0.9;">降雨機率 (12h)</div>
                <div style="font-size: 28px; margin: 4px 0;">💧</div>
                <div style="font-size: 20px; font-weight: 700;">{pop_str}</div>
            </div>
        """, unsafe_allow_html=True)

    with col5:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%);
                        padding: 18px 14px; border-radius: 12px; color: white; text-align: center;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 500; opacity: 0.9;">舒適度指數</div>
                <div style="font-size: 28px; margin: 4px 0;">🧘</div>
                <div style="font-size: 15px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{ci}">{ci}</div>
            </div>
        """, unsafe_allow_html=True)

"""
Weather Cards Component (CWA V8 Style)
呈現中央氣象署風格之「36 小時三時段預報卡片」與「當前氣象綜述看板」。
"""
from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st


def get_wx_icon(wx: Optional[str]) -> str:
    """根據天氣現象關鍵字回傳對應的圖示。"""
    if not wx:
        return "⛅"
    if "雷" in wx:
        return "⛈️"
    if "雨" in wx:
        if "大雨" in wx or "豪雨" in wx:
            return "🌧️"
        return "🌦️"
    if "陰" in wx:
        return "☁️"
    if "晴" in wx and "多雲" in wx:
        return "🌤️"
    if "晴" in wx:
        return "☀️"
    if "多雲" in wx:
        return "⛅"
    if "霧" in wx or "霾" in wx:
        return "🌫️"
    return "⛅"


def _get_time_period_title(index: int, start_time: str) -> str:
    """根據時段順序與時間產生 CWA 常見標籤（如：今晚至明晨、明日白天、明日晚上）。"""
    try:
        hour = int(start_time[11:13]) if len(start_time) >= 13 else 0
        if index == 0:
            if 0 <= hour < 6:
                return "今日凌晨至清晨"
            elif 6 <= hour < 18:
                return "今日白天"
            else:
                return "今晚至明晨"
        elif index == 1:
            if 6 <= hour < 18:
                return "明日白天"
            else:
                return "明晚至後天清晨"
        elif index == 2:
            if 6 <= hour < 18:
                return "後日白天"
            else:
                return "明日晚上"
    except Exception:
        pass
    return f"預報時段 {index + 1}"


def render_cwa_hero_summary(location_name: str, county_df: pd.DataFrame) -> None:
    """繪製 CWA 頂部縣市即時預報看板。"""
    if county_df.empty:
        return

    first_row = county_df.sort_values("start_time").iloc[0]
    wx = first_row.get("wx") or "多雲"
    icon = get_wx_icon(wx)
    min_t = first_row.get("min_t")
    max_t = first_row.get("max_t")
    pop = first_row.get("pop")
    ci = first_row.get("ci") or "舒適"

    temp_range = f"{int(min_t)} ~ {int(max_t)}°C" if (min_t is not None and max_t is not None) else "--"
    pop_str = f"{int(pop)}%" if pop is not None else "--"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0B4F8A 0%, #1573B6 60%, #0093D8 100%);
                border-radius: 12px; padding: 20px 24px; color: white; margin-bottom: 20px;
                box-shadow: 0 4px 15px rgba(11, 79, 138, 0.25); display: flex;
                flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;">
        <div style="display: flex; align-items: center; gap: 18px;">
            <div style="font-size: 50px; line-height: 1; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">{icon}</div>
            <div>
                <div style="font-size: 24px; font-weight: 800; letter-spacing: 0.5px;">{location_name}</div>
                <div style="font-size: 16px; font-weight: 600; opacity: 0.95; margin-top: 2px;">{wx} · 舒適度：{ci}</div>
            </div>
        </div>
        <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
            <div style="text-align: center; background: rgba(255,255,255,0.15); padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.25);">
                <div style="font-size: 12px; opacity: 0.85; font-weight: 500;">預估氣溫</div>
                <div style="font-size: 22px; font-weight: 800; color: #FFFDF0;">{temp_range}</div>
            </div>
            <div style="text-align: center; background: rgba(255,255,255,0.15); padding: 8px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.25);">
                <div style="font-size: 12px; opacity: 0.85; font-weight: 500;">降雨機率</div>
                <div style="font-size: 22px; font-weight: 800; color: #93E2FF;">💧 {pop_str}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_weather_cards(county_df: pd.DataFrame, location_name: str) -> None:
    """
    渲染 CWA 經典「36 小時三時段預報卡片」 (如：今晚至明晨、明日白天、明日晚上)。
    """
    if county_df.empty:
        st.info(f"尚無 {location_name} 之預報時段資料。")
        return

    df_sorted = county_df.sort_values("start_time").reset_index(drop=True)
    cols = st.columns(min(len(df_sorted), 3))

    for idx, row in df_sorted.iterrows():
        if idx >= 3:
            break
        col = cols[idx]
        
        start_t = row.get("start_time", "").replace("T", " ")[:16]
        end_t = row.get("end_time", "").replace("T", " ")[:16]
        period_title = _get_time_period_title(idx, start_t)
        
        wx = row.get("wx") or "多雲"
        icon = get_wx_icon(wx)
        min_t = row.get("min_t")
        max_t = row.get("max_t")
        pop = row.get("pop")
        ci = row.get("ci") or "無"

        temp_str = f"{int(min_t)} ~ {int(max_t)}°C" if (min_t is not None and max_t is not None) else "--"
        pop_str = f"{int(pop)}%" if pop is not None else "--"
        
        # 時段時間簡寫
        s_short = start_t[5:] if len(start_t) >= 16 else start_t
        e_short = end_t[5:] if len(end_t) >= 16 else end_t

        with col:
            st.markdown(f"""
            <div style="background: white; border-radius: 12px; border: 1px solid #E2E8F0;
                        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.06), 0 2px 4px -1px rgba(0,0,0,0.04);
                        padding: 16px 14px; text-align: center; height: 100%; display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <div style="background: #0284C7; color: white; padding: 4px 10px; border-radius: 20px;
                                font-size: 13px; font-weight: 700; display: inline-block; margin-bottom: 8px;">
                        {period_title}
                    </div>
                    <div style="font-size: 11px; color: #64748B; margin-bottom: 8px;">{s_short} ~ {e_short}</div>
                    <div style="font-size: 38px; margin: 4px 0;">{icon}</div>
                    <div style="font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 6px;">{wx}</div>
                </div>
                <div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 8px; margin-top: 6px;">
                        <div style="display: flex; justify-content: space-around; align-items: center;">
                            <div>
                                <span style="font-size: 11px; color: #64748B;">氣溫</span><br>
                                <b style="font-size: 16px; color: #DC2626;">{temp_str}</b>
                            </div>
                            <div style="border-left: 1px solid #E2E8F0; height: 24px;"></div>
                            <div>
                                <span style="font-size: 11px; color: #64748B;">降雨機率</span><br>
                                <b style="font-size: 16px; color: #0284C7;">💧 {pop_str}</b>
                            </div>
                        </div>
                    </div>
                    <div style="font-size: 12px; color: #D97706; font-weight: 600; margin-top: 8px; background: #FEF3C7; padding: 4px 8px; border-radius: 6px;">
                        🧘 {ci}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

"""
Weather Trend Chart Component
使用 Plotly 繪製 36 小時氣溫變化 (最高溫/最低溫) 與降雨機率趨勢圖。
"""
from typing import Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def render_weather_charts(location_df: pd.DataFrame, location_name: str) -> None:
    """
    繪製指定縣市的 36 小時氣象趨勢圖表。
    
    包含：
    - 主圖：最高溫 (紅色) 與最低溫 (藍色) 折線圖
    - 次圖/副軸：降雨機率長條圖 (藍綠色)
    """
    if location_df.empty:
        st.info(f"目前無 {location_name} 之趨勢圖表資料。")
        return

    # 排序時間
    df = location_df.sort_values("start_time").copy()

    # 產生 X 軸易讀時段標籤
    time_labels = []
    for _, row in df.iterrows():
        s = row["start_time"].replace("T", " ")[:16]
        e = row["end_time"].replace("T", " ")[:16]
        # 取簡化標籤，例如 "09-21 18:00 ~ 09-22 06:00"
        s_short = s[5:] if len(s) >= 16 else s
        e_short = e[5:] if len(e) >= 16 else e
        time_labels.append(f"{s_short}<br>至 {e_short}")

    df["time_label"] = time_labels

    # 建立雙 Y 軸子圖表 (上方溫度，下方降雨機率)
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.12,
        subplot_titles=(f"📈 {location_name} 36小時氣溫趨勢 (°C)", f"🌧️ {location_name} 降雨機率 (%)"),
        row_heights=[0.6, 0.4]
    )

    # 1. 最高溫 (紅色線)
    fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["max_t"],
            name="最高溫 (MaxT)",
            mode="lines+markers+text",
            line=dict(color="#EF4444", width=3),
            marker=dict(size=9, color="#EF4444"),
            text=[f"{v:.0f}°C" if pd.notnull(v) else "" for v in df["max_t"]],
            textposition="top center",
            textfont=dict(size=12, color="#991B1B", family="sans-serif"),
            hovertemplate="<b>最高溫</b>: %{y:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )

    # 2. 最低溫 (藍色線)
    fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["min_t"],
            name="最低溫 (MinT)",
            mode="lines+markers+text",
            line=dict(color="#3B82F6", width=3, dash="dot"),
            marker=dict(size=9, color="#3B82F6"),
            text=[f"{v:.0f}°C" if pd.notnull(v) else "" for v in df["min_t"]],
            textposition="bottom center",
            textfont=dict(size=12, color="#1E40AF", family="sans-serif"),
            hovertemplate="<b>最低溫</b>: %{y:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )

    # 3. 降雨機率 (長條圖)
    fig.add_trace(
        go.Bar(
            x=df["time_label"],
            y=df["pop"],
            name="降雨機率 (PoP)",
            marker=dict(
                color="#0EA5E9",
                opacity=0.85,
                line=dict(color="#0284C7", width=1.5)
            ),
            text=[f"{int(v)}%" if pd.notnull(v) else "0%" for v in df["pop"]],
            textposition="auto",
            textfont=dict(size=11, color="#FFFFFF"),
            hovertemplate="<b>降雨機率</b>: %{y:.0f}%<extra></extra>"
        ),
        row=2, col=1
    )

    # 圖表排版與美化
    fig.update_layout(
        template="plotly_white",
        height=480,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5
        ),
        hovermode="x unified",
    )

    fig.update_yaxes(title_text="溫度 (°C)", row=1, col=1, gridcolor="#F1F5F9")
    fig.update_yaxes(title_text="降雨率 (%)", range=[0, 105], row=2, col=1, gridcolor="#F1F5F9")
    fig.update_xaxes(gridcolor="#F1F5F9")

    st.plotly_chart(fig, use_container_width=True)

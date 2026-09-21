"""
Weather Trend Chart Component (CWA V8 Style)
使用 Plotly 繪製中央氣象署風格之 36 小時氣溫趨勢 (平滑曲線) 與降雨機率長條圖。
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


def render_weather_charts(location_df: pd.DataFrame, location_name: str) -> None:
    """繪製 CWA 風格的 36 小時氣象趨勢圖表。"""
    if location_df.empty:
        st.info(f"目前無 {location_name} 之趨勢圖表資料。")
        return

    df = location_df.sort_values("start_time").copy()

    time_labels = []
    for _, row in df.iterrows():
        s = row["start_time"].replace("T", " ")[:16]
        e = row["end_time"].replace("T", " ")[:16]
        s_short = s[5:] if len(s) >= 16 else s
        e_short = e[5:] if len(e) >= 16 else e
        time_labels.append(f"{s_short}<br>至 {e_short}")

    df["time_label"] = time_labels

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.14,
        subplot_titles=(
            f"<b>🌡️ {location_name} 36 小時氣溫趨勢 (°C)</b>",
            f"<b>💧 {location_name} 降雨機率 (%)</b>"
        ),
        row_heights=[0.6, 0.4]
    )

    # 1. 最高溫 (珊瑚紅/CWA 紅)
    fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["max_t"],
            name="最高溫 (MaxT)",
            mode="lines+markers+text",
            line=dict(color="#E11D48", width=3, shape="spline"),
            marker=dict(size=10, color="#E11D48", symbol="circle"),
            text=[f"{v:.0f}°C" if pd.notnull(v) else "" for v in df["max_t"]],
            textposition="top center",
            textfont=dict(size=13, color="#9F1239", family="sans-serif"),
            hovertemplate="<b>最高溫</b>: %{y:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )

    # 2. 最低溫 (海洋藍/CWA 藍)
    fig.add_trace(
        go.Scatter(
            x=df["time_label"],
            y=df["min_t"],
            name="最低溫 (MinT)",
            mode="lines+markers+text",
            line=dict(color="#0284C7", width=3, shape="spline", dash="dash"),
            marker=dict(size=10, color="#0284C7", symbol="diamond"),
            text=[f"{v:.0f}°C" if pd.notnull(v) else "" for v in df["min_t"]],
            textposition="bottom center",
            textfont=dict(size=13, color="#0369A1", family="sans-serif"),
            hovertemplate="<b>最低溫</b>: %{y:.1f}°C<extra></extra>"
        ),
        row=1, col=1
    )

    # 3. 降雨機率 (天藍長條圖)
    fig.add_trace(
        go.Bar(
            x=df["time_label"],
            y=df["pop"],
            name="降雨機率 (PoP)",
            marker=dict(
                color="#38BDF8",
                opacity=0.9,
                line=dict(color="#0284C7", width=1.5)
            ),
            text=[f"{int(v)}%" if pd.notnull(v) else "0%" for v in df["pop"]],
            textposition="auto",
            textfont=dict(size=12, color="#0C4A6E", family="sans-serif"),
            hovertemplate="<b>降雨機率</b>: %{y:.0f}%<extra></extra>"
        ),
        row=2, col=1
    )

    fig.update_layout(
        template="plotly_white",
        height=480,
        margin=dict(l=30, r=20, t=50, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(255, 255, 255, 0.8)"
        ),
        hovermode="x unified",
    )

    fig.update_yaxes(title_text="氣溫 (°C)", row=1, col=1, gridcolor="#F1F5F9")
    fig.update_yaxes(title_text="降雨率 (%)", range=[0, 105], row=2, col=1, gridcolor="#F1F5F9")
    fig.update_xaxes(gridcolor="#F1F5F9")

    st.plotly_chart(fig, width="stretch")

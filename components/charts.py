"""Reusable Plotly chart builders for the dashboard."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from utils.data_loader import STATUS_COLORS, RISK_COLORS

FONT = dict(family="Inter, system-ui, sans-serif", color="#3d3d3a")
MARGIN = dict(l=8, r=8, t=32, b=8)
PAPER_BG = "rgba(0,0,0,0)"
PLOT_BG  = "rgba(0,0,0,0)"
GRID_CLR = "rgba(180,178,169,0.3)"


def compliance_donut(breakdown: dict, title: str = "Compliance") -> go.Figure:
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    colors = [STATUS_COLORS.get(l, "#888") for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.68,
        marker=dict(colors=colors, line=dict(color="#fff", width=2)),
        textinfo="none",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, **FONT), x=0.5, xanchor="center"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(l=8, r=8, t=36, b=40),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=FONT,
    )
    return fig


def pam_onboarding_bar(df: pd.DataFrame, group_col: str, title: str = "CyberArk Onboarding") -> go.Figure:
    col = "PAM_Onboarded"
    if col not in df.columns or group_col not in df.columns:
        return empty_fig(title)
    grp = df.groupby([group_col, col]).size().reset_index(name="Count")
    fig = px.bar(grp, x=group_col, y="Count", color=col,
                 color_discrete_map={
                     "Onboarded": "#0ca30c", "Not Onboarded": "#d03b3b",
                     "Pending": "#fab219", "Exempted": "#6250d6"},
                 barmode="stack", title=title,
                 labels={group_col: "", "Count": "Records"})
    _style(fig)
    return fig


def compliance_bar(df: pd.DataFrame, group_col: str, title: str) -> go.Figure:
    col = "Compliance_Status"
    if col not in df.columns or group_col not in df.columns:
        return empty_fig(title)
    grp = df.groupby([group_col, col]).size().reset_index(name="Count")
    fig = px.bar(grp, x=group_col, y="Count", color=col,
                 color_discrete_map=STATUS_COLORS,
                 barmode="stack", title=title,
                 labels={group_col: "", "Count": "Records"})
    _style(fig)
    return fig


def risk_bar(df: pd.DataFrame, group_col: str = "Risk_Rating", title: str = "Risk Distribution") -> go.Figure:
    if group_col not in df.columns:
        return empty_fig(title)
    order = ["Critical", "High", "Medium", "Low"]
    vc = df[group_col].value_counts().reindex(order).fillna(0).reset_index()
    vc.columns = ["Risk", "Count"]
    fig = px.bar(vc, x="Risk", y="Count", color="Risk",
                 color_discrete_map=RISK_COLORS, title=title,
                 labels={"Risk": "", "Count": "Records"})
    fig.update_layout(showlegend=False)
    _style(fig)
    return fig


def trend_line(df: pd.DataFrame, date_col: str, value_col: str, title: str) -> go.Figure:
    if date_col not in df.columns or value_col not in df.columns:
        return empty_fig(title)
    ts = df.copy()
    ts[date_col] = pd.to_datetime(ts[date_col], errors="coerce")
    ts = ts.dropna(subset=[date_col])
    ts = ts.set_index(date_col)[value_col].resample("ME").mean().reset_index()
    fig = go.Figure(go.Scatter(
        x=ts[date_col], y=ts[value_col].round(1),
        mode="lines+markers",
        line=dict(color="#2a78d6", width=2),
        marker=dict(size=5),
        hovertemplate="%{x|%b %Y}: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=13), x=0.5, xanchor="center"),
                      xaxis=dict(showgrid=False), yaxis=dict(gridcolor=GRID_CLR),
                      margin=MARGIN, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG, font=FONT)
    return fig


def auth_gauge(pct: float, title: str = "Auth Integration") -> go.Figure:
    color = "#0ca30c" if pct >= 80 else "#fab219" if pct >= 60 else "#d03b3b"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct,
        number=dict(suffix="%", font=dict(size=28)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#888"),
            bar=dict(color=color, thickness=0.25),
            bgcolor="rgba(0,0,0,0)",
            steps=[
                dict(range=[0, 60],  color="rgba(210,59,59,0.12)"),
                dict(range=[60, 80], color="rgba(250,178,25,0.12)"),
                dict(range=[80, 100],color="rgba(12,163,12,0.12)"),
            ],
            threshold=dict(line=dict(color="black", width=2), thickness=0.6, value=80),
        ),
        title=dict(text=title, font=dict(size=12)),
    ))
    fig.update_layout(margin=dict(l=16, r=16, t=32, b=8),
                      paper_bgcolor=PAPER_BG, font=FONT, height=200)
    return fig


def pwd_mgmt_donut(breakdown: dict, title: str = "Password Management") -> go.Figure:
    colors = {"Automatic": "#0ca30c", "Manual": "#fab219",
              "Not Configured": "#d03b3b", "Exempted": "#6250d6"}
    labels = [k for k in breakdown if k != "Not Applicable"]
    values = [breakdown[k] for k in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.65,
        marker=dict(colors=[colors.get(l, "#888") for l in labels],
                    line=dict(color="#fff", width=2)),
        textinfo="none",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13), x=0.5, xanchor="center"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5,
                    font=dict(size=10)),
        margin=dict(l=8, r=8, t=36, b=48),
        paper_bgcolor=PAPER_BG, font=FONT,
    )
    return fig


def breakglass_bar(df: pd.DataFrame, title: str = "Break-Glass Onboarding") -> go.Figure:
    col = "CyberArk_Onboarding_Status"
    if col not in df.columns:
        return empty_fig(title)
    vc = df[col].value_counts().reset_index()
    vc.columns = ["Status", "Count"]
    colors = {"Onboarded": "#0ca30c", "Not Onboarded": "#d03b3b",
               "Pending": "#fab219", "Exempted": "#6250d6"}
    fig = px.bar(vc, x="Status", y="Count", color="Status",
                 color_discrete_map=colors, title=title,
                 labels={"Status": "", "Count": "Resources"})
    fig.update_layout(showlegend=False)
    _style(fig)
    return fig


def heatmap_compliance(df: pd.DataFrame, x_col: str, y_col: str, title: str) -> go.Figure:
    if x_col not in df.columns or y_col not in df.columns:
        return empty_fig(title)
    pivot = df.groupby([y_col, x_col]).size().unstack(fill_value=0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#eaf3de"],[0.5,"#fab219"],[1,"#d03b3b"]],
        hovertemplate="%{y} / %{x}: %{z}<extra></extra>",
        showscale=True,
    ))
    fig.update_layout(title=dict(text=title, font=dict(size=13), x=0.5, xanchor="center"),
                      margin=dict(l=8, r=8, t=36, b=8),
                      paper_bgcolor=PAPER_BG, font=FONT)
    return fig


def empty_fig(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="No data available", xref="paper", yref="paper",
                       x=0.5, y=0.5, showarrow=False, font=dict(size=13, color="#888"))
    fig.update_layout(title=dict(text=title, font=dict(size=13), x=0.5),
                      paper_bgcolor=PAPER_BG, margin=MARGIN, font=FONT)
    return fig


def _style(fig: go.Figure):
    fig.update_layout(
        margin=MARGIN, paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=FONT,
        xaxis=dict(showgrid=False, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID_CLR, tickfont=dict(size=10)),
        title=dict(font=dict(size=13), x=0.5, xanchor="center"),
        legend=dict(font=dict(size=10), orientation="h",
                    yanchor="bottom", y=-0.35, xanchor="center", x=0.5),
    )

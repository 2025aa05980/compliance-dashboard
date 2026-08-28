"""Reusable Dash layout components."""
from __future__ import annotations

from dash import html, dcc, dash_table
import dash_bootstrap_components as dbc
import pandas as pd

STATUS_BADGE = {
    "Compliant":           "success",
    "Non-Compliant":       "danger",
    "Partially Compliant": "warning",
    "Exception Approved":  "info",
    "Not Assessed":        "secondary",
    "Onboarded":           "success",
    "Not Onboarded":       "danger",
    "Pending":             "warning",
    "Exempted":            "info",
    "Integrated":          "success",
    "Not Integrated":      "danger",
    "Partial":             "warning",
    "Automatic":           "success",
    "Manual":              "warning",
    "Not Configured":      "danger",
}

RISK_BADGE = {
    "Critical": "danger",
    "High":     "warning",
    "Medium":   "primary",
    "Low":      "success",
}


def kpi_card(title: str, value, subtitle: str = "", color: str = "dark",
             icon: str = "bi-shield-check", delta: str = "") -> dbc.Card:
    color_map = {"green": "#0ca30c", "red": "#d03b3b",
                 "yellow": "#fab219", "blue": "#2a78d6", "purple": "#6250d6", "dark": "#1f3a5f"}
    c = color_map.get(color, color)
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"bi {icon} fs-3", style={"color": c, "opacity": "0.8"}),
                html.Div([
                    html.P(title, className="text-muted mb-0", style={"fontSize": "11px", "fontWeight": "500", "textTransform": "uppercase", "letterSpacing": "0.5px"}),
                    html.H4(str(value), className="mb-0 fw-bold", style={"color": c, "fontSize": "26px"}),
                    html.Small(subtitle, className="text-muted") if subtitle else None,
                    html.Span(delta, className=f"badge bg-{'success' if '+' in str(delta) else 'danger'} ms-2 small") if delta else None,
                ], className="ms-2"),
            ], className="d-flex align-items-center"),
        ])
    ], className="shadow-sm border-0 h-100",
       style={"borderLeft": f"4px solid {c} !important", "background": "white"})


def stat_row(items: list[dict]) -> dbc.Row:
    """items = [{"title":..,"value":..,"subtitle":..,"color":..,"icon":..}]"""
    cols = []
    for item in items:
        cols.append(dbc.Col(kpi_card(**item), xs=12, sm=6, md=4, lg=3, xl=2, className="mb-3"))
    return dbc.Row(cols, className="g-2")


def compliance_table(df: pd.DataFrame, table_id: str,
                     visible_cols: list | None = None,
                     max_rows: int = 500,
                     height: str = "420px") -> dash_table.DataTable:
    if df is None or len(df) == 0:
        return html.P("No data available.", className="text-muted p-3")

    if visible_cols:
        cols = [c for c in visible_cols if c in df.columns]
    else:
        cols = list(df.columns)

    display_df = df[cols].head(max_rows).copy()
    # Stringify datetime cols
    for c in display_df.columns:
        if pd.api.types.is_datetime64_any_dtype(display_df[c]):
            display_df[c] = display_df[c].dt.strftime("%Y-%m-%d")
    display_df = display_df.fillna("").astype(str)

    style_data_conditional = []
    if "Compliance_Status" in cols:
        for status, color in [
            ("Compliant",           "#e8f5e9"),
            ("Non-Compliant",       "#fdecea"),
            ("Partially Compliant", "#fff8e1"),
            ("Exception Approved",  "#f3e5f5"),
            ("Not Assessed",        "#f5f5f5"),
        ]:
            style_data_conditional.append({
                "if": {"filter_query": f'{{Compliance_Status}} = "{status}"',
                       "column_id": "Compliance_Status"},
                "backgroundColor": color,
                "fontWeight": "500",
            })
    if "Risk_Rating" in cols:
        for risk, color in [
            ("Critical", "#fdecea"), ("High", "#fff8e1"),
            ("Medium", "#e3f2fd"),   ("Low", "#e8f5e9"),
        ]:
            style_data_conditional.append({
                "if": {"filter_query": f'{{Risk_Rating}} = "{risk}"',
                       "column_id": "Risk_Rating"},
                "backgroundColor": color,
                "fontWeight": "500",
            })

    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": c.replace("_", " "), "id": c} for c in cols],
        data=display_df.to_dict("records"),
        page_size=20,
        page_action="native",
        sort_action="native",
        filter_action="native",
        filter_options={"case": "insensitive"},
        export_format="csv",
        export_headers="display",
        style_table={"overflowX": "auto", "minWidth": "100%", "maxHeight": height},
        style_header={
            "backgroundColor": "#1f3a5f",
            "color": "white",
            "fontWeight": "600",
            "fontSize": "11px",
            "textTransform": "uppercase",
            "letterSpacing": "0.4px",
            "padding": "10px 12px",
            "position": "sticky",
            "top": 0,
            "zIndex": 999,
        },
        style_data={
            "fontSize": "12px",
            "padding": "7px 12px",
            "border": "1px solid #f0efec",
            "color": "#3d3d3a",
        },
        style_data_conditional=style_data_conditional,
        style_filter={
            "backgroundColor": "#f8f8f6",
            "fontSize": "11px",
            "padding": "4px 8px",
        },
        fixed_rows={"headers": True},
        row_selectable="multi",
        selected_rows=[],
        tooltip_data=[{c: {"value": str(row[c]), "type": "markdown"} for c in cols}
                      for row in display_df.to_dict("records")],
        tooltip_duration=None,
    )


def filter_bar(prefix: str, df: pd.DataFrame, filter_cols: list[str]) -> html.Div:
    """Auto-generate dropdown filters for a given list of columns."""
    dropdowns = []
    for col in filter_cols:
        if col not in df.columns:
            continue
        opts = [{"label": "All", "value": "ALL"}] + \
               [{"label": str(v), "value": str(v)}
                for v in sorted(df[col].dropna().unique())]
        dropdowns.append(
            dbc.Col(
                dcc.Dropdown(
                    id=f"{prefix}-filter-{col}",
                    options=opts,
                    value="ALL",
                    clearable=False,
                    style={"fontSize": "12px"},
                    placeholder=col.replace("_", " "),
                ),
                xs=12, sm=6, md=4, lg=2, className="mb-2"
            )
        )
    return dbc.Row(dropdowns, className="g-1 mb-3")


def section_header(title: str, subtitle: str = "") -> html.Div:
    return html.Div([
        html.H5(title, className="fw-semibold mb-0", style={"color": "#1f3a5f"}),
        html.Small(subtitle, className="text-muted") if subtitle else None,
        html.Hr(className="my-2", style={"borderColor": "#e8e7e2"}),
    ], className="mb-3")


def alert_badge(text: str, color: str = "danger") -> dbc.Badge:
    return dbc.Badge(text, color=color, className="me-1 px-2 py-1",
                     style={"fontSize": "11px"})


def download_buttons(prefix: str) -> html.Div:
    return html.Div([
        dbc.Button([html.I(className="bi bi-filetype-csv me-1"), "Export CSV"],
                   id=f"{prefix}-dl-csv", color="outline-secondary", size="sm", className="me-2"),
        dbc.Button([html.I(className="bi bi-file-earmark-excel me-1"), "Export Excel"],
                   id=f"{prefix}-dl-xlsx", color="outline-success", size="sm", className="me-2"),
        dcc.Download(id=f"{prefix}-download-csv"),
        dcc.Download(id=f"{prefix}-download-xlsx"),
    ], className="d-flex align-items-center")

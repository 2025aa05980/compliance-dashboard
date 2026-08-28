"""
IAM Compliance Dashboard — Production Grade
Framework: Plotly Dash 4 + Dash Bootstrap Components
Auth: Session-based with role-gated views
Data: CSV flat files (swap load() for DB queries in production)
"""

import dash
from dash import dash_table, dcc, html, Input, Output, State, callback, ctx, ALL, MATCH, no_update
import dash_bootstrap_components as dbc
import pandas as pd
import json
import os

from utils.data_loader import (
    load, load_users, load_field_config, DATASETS, LABEL_MAP,
    compliance_summary, cyberark_summary, pwd_mgmt_summary, auth_summary,
    global_kpis, STATUS_COLORS, RISK_COLORS
)
from utils.report_exporter import df_to_csv_bytes, df_to_excel_bytes
from components.charts import (
    compliance_donut, pam_onboarding_bar, compliance_bar, risk_bar,
    auth_gauge, pwd_mgmt_donut, breakglass_bar, heatmap_compliance, empty_fig
)
from components.ui import (
    kpi_card, stat_row, compliance_table, filter_bar,
    section_header, download_buttons
)

# ─────────────────────────────────────────────
# APP INIT
# ─────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        dbc.icons.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="IAM Compliance Dashboard",
    update_title=None,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server

# ─────────────────────────────────────────────
# CONSTANTS / STYLES
# ─────────────────────────────────────────────
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0, "left": 0, "bottom": 0,
    "width": "220px",
    "background": "#1a2f4a",
    "overflowY": "auto",
    "zIndex": 1000,
    "transition": "all 0.25s ease",
}

CONTENT_STYLE = {
    "marginLeft": "220px",
    "minHeight": "100vh",
    "background": "#f4f3ef",
    "fontFamily": "Inter, system-ui, sans-serif",
}

NAV_ITEMS = [
    ("bi-speedometer2",       "Executive Summary",   "/"),
    ("bi-bar-chart-line",     "Compliance Overview", "/compliance"),
    ("bi-person-badge",       "Human Accounts",      "/human"),
    ("bi-shield-lock",        "Privileged Accounts", "/privileged"),
    ("bi-robot",              "Service & Bot / AI",  "/nonhuman"),
    ("bi-server",             "Assets — Windows",    "/windows"),
    ("bi-terminal",           "Assets — Linux",      "/linux"),
    ("bi-router",             "Network Devices",     "/network"),
    ("bi-hdd-stack",          "Virtual / ESXi",      "/virtual"),
    ("bi-app-indicator",      "Applications",        "/applications"),
    ("bi-key",                "Break-Glass",         "/breakglass"),
    ("bi-sliders",            "Admin — Field Config","/admin"),
    ("bi-question-circle",    "Dynamic Query",       "/query"),
]

ROLE_NAV_FILTER = {
    "Executive":  ["/", "/compliance", "/breakglass"],
    "Leadership": ["/", "/compliance", "/human", "/privileged", "/nonhuman",
                   "/windows", "/linux", "/network", "/virtual", "/applications", "/breakglass"],
    "Operations": [n[2] for n in NAV_ITEMS if n[2] != "/admin"],
    "Admin":      [n[2] for n in NAV_ITEMS],
}

# ─────────────────────────────────────────────
# LOGIN PAGE
# ─────────────────────────────────────────────
def login_layout():
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.I(className="bi bi-shield-lock-fill display-4",
                                   style={"color": "#1a2f4a"}),
                            html.H3("IAM Compliance Dashboard", className="fw-bold mt-3",
                                    style={"color": "#1a2f4a"}),
                            html.P("Secure access — authenticate to continue",
                                   className="text-muted small"),
                        ], className="text-center mb-4"),
                        dbc.Form([
                            dbc.Row([
                                dbc.Label("Username", width=12, className="fw-semibold small"),
                                dbc.Col(dbc.Input(id="login-user", type="text",
                                                  placeholder="Enter username", size="lg",
                                                  className="mb-3"), width=12),
                            ]),
                            dbc.Row([
                                dbc.Label("Password", width=12, className="fw-semibold small"),
                                dbc.Col(dbc.Input(id="login-pass", type="password",
                                                  placeholder="Enter password", size="lg",
                                                  className="mb-3",
                                                  n_submit=0), width=12),
                            ]),
                            html.Div(id="login-error", className="text-danger small mb-2"),
                            dbc.Button("Sign In", id="login-btn", color="primary",
                                       size="lg", className="w-100 fw-semibold",
                                       style={"background": "#1a2f4a", "borderColor": "#1a2f4a"}),
                        ]),
                        html.Hr(),
                        html.P("Demo credentials:", className="fw-semibold small mb-1"),
                        html.Div([
                            dbc.Badge("exec_admin / exec123 → Executive", color="danger", className="d-block mb-1 text-start p-2"),
                            dbc.Badge("leader_ops / lead123 → Leadership", color="warning", className="d-block mb-1 text-start p-2"),
                            dbc.Badge("ops_analyst / ops123 → Operations", color="primary", className="d-block mb-1 text-start p-2"),
                            dbc.Badge("rpt_admin / admin123 → Admin", color="success", className="d-block text-start p-2"),
                        ]),
                    ])
                ], className="shadow-lg border-0", style={"borderRadius": "16px"})
            ], md=5, lg=4, className="mx-auto"),
        ], className="min-vh-100 align-items-center", align="center"),
    ], style={"background": "linear-gradient(135deg, #1a2f4a 0%, #2a78d6 100%)",
              "padding": "2rem"})


app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="session-store", storage_type="session",
              data={"logged_in": False, "role": None, "username": None, "display_name": None}),
    dcc.Store(id="field-config-store", storage_type="session"),
    html.Div(id="login-panel", children=login_layout()),
    html.Div(id="page-wrapper"),
    dcc.Download(id="global-download"),
], style={"fontFamily": "Inter, system-ui, sans-serif"})


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
def sidebar(role: str, current_path: str) -> html.Div:
    allowed = ROLE_NAV_FILTER.get(role, [])
    nav_links = []
    for icon, label, path in NAV_ITEMS:
        if path not in allowed:
            continue
        is_active = (current_path == path) or (path != "/" and current_path.startswith(path))
        nav_links.append(
            dcc.Link(
                html.Div([
                    html.I(className=f"bi {icon} me-2", style={"width": "18px"}),
                    html.Span(label, style={"fontSize": "12px"}),
                ], className="d-flex align-items-center px-3 py-2",
                   style={"color": "white" if is_active else "rgba(255,255,255,0.65)",
                          "background": "rgba(255,255,255,0.12)" if is_active else "transparent",
                          "borderRadius": "6px", "margin": "1px 8px",
                          "fontWeight": "500" if is_active else "400",
                          "cursor": "pointer", "transition": "all 0.15s"}),
                href=path, refresh=False, style={"textDecoration": "none"},
            )
        )
    role_colors = {"Executive": "danger", "Leadership": "warning",
                   "Operations": "primary", "Admin": "success"}
    return html.Div([
        html.Div([
            html.I(className="bi bi-shield-lock-fill me-2 text-white", style={"fontSize": "20px"}),
            html.Span("IAM Dashboard", style={"color": "white", "fontWeight": "700", "fontSize": "14px"}),
        ], className="d-flex align-items-center px-3 py-3",
           style={"borderBottom": "1px solid rgba(255,255,255,0.15)"}),
        html.Div([
            dbc.Badge(role, color=role_colors.get(role, "secondary"),
                      className="ms-3 mb-3 mt-2 px-2 py-1",
                      style={"fontSize": "10px"}),
        ]),
        html.Nav(nav_links),
        html.Div([
            html.Hr(style={"borderColor": "rgba(255,255,255,0.2)"}),
            dbc.Button([html.I(className="bi bi-box-arrow-right me-1"), "Sign Out"],
                       id="logout-btn", color="link", size="sm",
                       style={"color": "rgba(255,255,255,0.6)", "fontSize": "12px"}),
        ], style={"position": "absolute", "bottom": "12px", "left": 0, "right": 0}),
    ], style=SIDEBAR_STYLE)


# ─────────────────────────────────────────────
# TOPBAR
# ─────────────────────────────────────────────
def topbar(display_name: str, page_title: str) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col(html.H6(page_title, className="mb-0 fw-bold",
                            style={"color": "#1a2f4a"}), className="d-flex align-items-center"),
            dbc.Col([
                html.Span([
                    html.I(className="bi bi-person-circle me-1 text-muted"),
                    html.Span(display_name, className="text-muted small"),
                ], className="d-flex align-items-center justify-content-end"),
            ], className="text-end"),
        ])
    ], style={"background": "white", "padding": "12px 24px",
              "borderBottom": "1px solid #e8e7e2", "position": "sticky", "top": 0, "zIndex": 500})


# ─────────────────────────────────────────────
# PAGE: EXECUTIVE SUMMARY
# ─────────────────────────────────────────────
def page_executive(role: str) -> html.Div:
    kpis = global_kpis()

    # Domain-level compliance for heatmap
    domain_rows = []
    for ds, label in LABEL_MAP.items():
        try:
            df = load(ds)
            s = compliance_summary(df)
            c = cyberark_summary(df)
            a = auth_summary(df)
            domain_rows.append({
                "Domain": label,
                "Total": s.get("total", 0),
                "Compliant %": s.get("pct_compliant", 0),
                "PAM Onboarded %": c.get("pct_onboarded", 0),
                "Auth Integrated %": a.get("pct_integrated", 0),
            })
        except Exception:
            pass
    domain_df = pd.DataFrame(domain_rows)

    import plotly.graph_objects as go
    # Heatmap of compliance pct across domains
    if not domain_df.empty:
        heat_fig = go.Figure(go.Bar(
            x=domain_df["Domain"],
            y=domain_df["Compliant %"],
            marker_color=[
                "#0ca30c" if v >= 80 else "#fab219" if v >= 60 else "#d03b3b"
                for v in domain_df["Compliant %"]
            ],
            text=domain_df["Compliant %"].apply(lambda x: f"{x:.0f}%"),
            textposition="outside",
            hovertemplate="%{x}<br>Compliant: %{y:.1f}%<extra></extra>",
        ))
        heat_fig.update_layout(
            title=dict(text="Compliance Rate by Domain", font=dict(size=13), x=0.5, xanchor="center"),
            xaxis=dict(showgrid=False, tickfont=dict(size=10)),
            yaxis=dict(range=[0, 110], ticksuffix="%", gridcolor="rgba(180,178,169,0.3)"),
            margin=dict(l=8, r=8, t=36, b=8),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif"),
            showlegend=False,
        )
    else:
        heat_fig = empty_fig("Compliance by Domain")

    # Multi-metric bar
    if not domain_df.empty:
        import plotly.express as px
        melt = domain_df.melt(id_vars="Domain",
                               value_vars=["Compliant %", "PAM Onboarded %", "Auth Integrated %"],
                               var_name="Metric", value_name="Percentage")
        multi_fig = px.bar(melt, x="Domain", y="Percentage", color="Metric", barmode="group",
                           color_discrete_sequence=["#0ca30c", "#2a78d6", "#fab219"],
                           labels={"Domain": "", "Percentage": "% Compliant/Integrated"})
        multi_fig.update_layout(
            title=dict(text="Compliance / PAM / Auth Integration by Domain",
                       font=dict(size=13), x=0.5, xanchor="center"),
            xaxis=dict(showgrid=False, tickfont=dict(size=9)),
            yaxis=dict(range=[0, 115], ticksuffix="%", gridcolor="rgba(180,178,169,0.3)"),
            margin=dict(l=8, r=8, t=36, b=8),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif"),
            legend=dict(orientation="h", y=-0.3, x=0.5, xanchor="center", font=dict(size=10)),
        )
    else:
        multi_fig = empty_fig("Multi-metric")

    kpi_items = [
        {"title": "Total Records",    "value": f"{kpis['total_records']:,}",    "color": "dark",   "icon": "bi-database", "subtitle": "across all domains"},
        {"title": "Overall Compliant","value": f"{kpis['pct_compliant']}%",     "color": "green",  "icon": "bi-patch-check", "subtitle": f"{kpis['compliant']:,} records"},
        {"title": "Non-Compliant",    "value": f"{kpis['non_compliant']:,}",    "color": "red",    "icon": "bi-x-circle", "subtitle": "require action"},
        {"title": "PAM Onboarded",    "value": f"{kpis['pct_pam']}%",          "color": "blue",   "icon": "bi-shield-lock", "subtitle": f"{kpis['pam_onboarded']:,} of {kpis['pam_total']:,}"},
        {"title": "Auto Pwd Mgmt",    "value": f"{kpis['pct_pwd_auto']}%",     "color": "purple", "icon": "bi-key", "subtitle": f"{kpis['pwd_auto']:,} records"},
        {"title": "Auth Integrated",  "value": f"{kpis['pct_auth']}%",         "color": "yellow", "icon": "bi-plug", "subtitle": f"{kpis['auth_integrated']:,} records"},
        {"title": "Critical Findings","value": f"{kpis['critical_findings']:,}","color": "red",   "icon": "bi-exclamation-triangle", "subtitle": "open vulnerabilities"},
        {"title": "High Findings",    "value": f"{kpis['high_findings']:,}",   "color": "yellow","icon": "bi-exclamation-circle", "subtitle": "open vulnerabilities"},
    ]

    # Domain summary table
    if not domain_df.empty:
        dom_table_data = domain_df.to_dict("records")
    else:
        dom_table_data = []

    return html.Div([
        section_header("Executive Summary", "Organisation-wide IAM & PAM compliance posture"),
        stat_row(kpi_items),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=heat_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=6, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=multi_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=6, className="mb-3"),
        ]),
        dbc.Card([
            dbc.CardHeader(html.Strong("Domain Compliance Summary", className="text-dark")),
            dbc.CardBody(
                dash_table.DataTable(
                    columns=[{"name": c, "id": c} for c in domain_df.columns] if not domain_df.empty else [],
                    data=dom_table_data,
                    style_header={"backgroundColor": "#1f3a5f", "color": "white",
                                  "fontWeight": "600", "fontSize": "11px"},
                    style_data={"fontSize": "12px", "padding": "7px 12px"},
                    style_data_conditional=[
                        {"if": {"filter_query": "{Compliant %} >= 80", "column_id": "Compliant %"},
                         "backgroundColor": "#e8f5e9", "color": "#1b5e20"},
                        {"if": {"filter_query": "{Compliant %} < 60", "column_id": "Compliant %"},
                         "backgroundColor": "#fdecea", "color": "#b71c1c"},
                    ],
                    style_table={"overflowX": "auto"},
                ) if not domain_df.empty else html.P("No data")
            )
        ], className="shadow-sm border-0 mb-3"),
    ], className="p-4")


# ─────────────────────────────────────────────
# PAGE: COMPLIANCE OVERVIEW
# ─────────────────────────────────────────────
def page_compliance_overview(role: str) -> html.Div:
    charts = []
    for ds, label in LABEL_MAP.items():
        try:
            df = load(ds)
            s = compliance_summary(df)
            fig = compliance_donut(s.get("breakdown", {}), label)
            charts.append(
                dbc.Col(dbc.Card(dbc.CardBody([
                    dcc.Graph(figure=fig, config={"displayModeBar": False}, style={"height": "220px"}),
                    html.Hr(className="my-1"),
                    html.Div([
                        html.Span(f"Total: {s['total']}", className="text-muted small me-2"),
                        html.Span(f"{s['pct_compliant']}% compliant",
                                  className="fw-bold small",
                                  style={"color": "#0ca30c" if s['pct_compliant'] >= 75 else "#fab219" if s['pct_compliant'] >= 55 else "#d03b3b"}),
                    ]),
                ]), className="shadow-sm border-0 h-100"), md=4, lg=3, className="mb-3")
            )
        except Exception as e:
            pass

    # CyberArk onboarding overall
    try:
        from utils.data_loader import load as dload
        all_pam = []
        for ds in DATASETS:
            d = dload(ds)
            if "PAM_Onboarded" in d.columns:
                all_pam.append(d[["PAM_Onboarded"]].copy())
        pam_df = pd.concat(all_pam)
        pam_vc = pam_df["PAM_Onboarded"].value_counts().to_dict()
        pam_fig = compliance_donut(pam_vc, "CyberArk Onboarding (All)")
    except Exception:
        pam_fig = empty_fig("CyberArk Onboarding")

    try:
        all_auth = []
        for ds in DATASETS:
            d = load(ds)
            if "Auth_Framework_Integration" in d.columns:
                all_auth.append(d[["Auth_Framework_Integration"]].copy())
        auth_df = pd.concat(all_auth)
        auth_vc = auth_df["Auth_Framework_Integration"].value_counts().to_dict()
        auth_fig = compliance_donut(auth_vc, "Auth Framework Integration (All)")
    except Exception:
        auth_fig = empty_fig("Auth Integration")

    try:
        all_pwd = []
        for ds in DATASETS:
            d = load(ds)
            if "Password_Mgmt" in d.columns:
                sub = d[d["Password_Mgmt"] != "Not Applicable"]
                if len(sub):
                    all_pwd.append(sub[["Password_Mgmt"]].copy())
        pwd_df = pd.concat(all_pwd)
        pwd_vc = pwd_df["Password_Mgmt"].value_counts().to_dict()
        pwd_fig = pwd_mgmt_donut(pwd_vc, "Password Management (All)")
    except Exception:
        pwd_fig = empty_fig("Password Mgmt")

    return html.Div([
        section_header("Compliance Overview", "Compliance status across all domains"),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=pam_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=4, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=auth_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=4, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=pwd_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=4, className="mb-3"),
        ]),
        html.H6("Per-Domain Status Breakdown", className="fw-semibold mb-3 mt-1",
                style={"color": "#1f3a5f"}),
        dbc.Row(charts),
    ], className="p-4")


# ─────────────────────────────────────────────
# PAGE FACTORY: generic dataset page
# ─────────────────────────────────────────────
def page_dataset(dataset: str, role: str, field_config: dict,
                 extra_charts_fn=None) -> html.Div:
    label = LABEL_MAP.get(dataset, dataset)
    try:
        df = load(dataset)
    except Exception as e:
        return html.Div(f"Error loading {label}: {e}", className="p-4 text-danger")

    vis_cols = None
    if role not in ("Operations", "Admin"):
        from utils.data_loader import get_visible_columns
        vis_cols = get_visible_columns(dataset, role, field_config)

    s  = compliance_summary(df)
    ca = cyberark_summary(df)
    pw = pwd_mgmt_summary(df)
    au = auth_summary(df)

    kpi_items = [
        {"title": "Total Records",   "value": s["total"],              "color": "dark",   "icon": "bi-database"},
        {"title": "Compliant",       "value": f"{s['pct_compliant']}%","color": "green",  "icon": "bi-patch-check", "subtitle": f"{s['compliant']} records"},
        {"title": "Non-Compliant",   "value": s["non_compliant"],      "color": "red",    "icon": "bi-x-circle"},
        {"title": "PAM Onboarded",   "value": f"{ca.get('pct_onboarded',0)}%", "color": "blue", "icon": "bi-shield-lock",
         "subtitle": f"{ca.get('onboarded',0)} of {ca.get('total',0)}"},
        {"title": "Auto Pwd Mgmt",   "value": f"{pw.get('pct_automatic',0)}%", "color": "purple", "icon": "bi-key"},
        {"title": "Auth Integrated", "value": f"{au.get('pct_integrated',0)}%","color": "yellow","icon": "bi-plug"},
    ]

    # Filter columns available in this dataset
    filter_col_candidates = ["Compliance_Status", "Risk_Rating", "PAM_Onboarded",
                              "Environment", "Business_Unit", "Auth_Framework_Integration",
                              "Password_Mgmt", "Account_Status", "Asset_Type", "Bot_Type",
                              "Agent_Type", "Account_Type", "Employment_Type"]
    available_filters = [c for c in filter_col_candidates if c in df.columns]

    comp_fig = compliance_donut(s.get("breakdown", {}), f"{label} — Compliance")
    risk_fig = risk_bar(df, title=f"{label} — Risk Rating")

    has_pam = "PAM_Onboarded" in df.columns
    has_auth = "Auth_Framework_Integration" in df.columns

    pam_fig  = pam_onboarding_bar(df, "Environment" if "Environment" in df.columns else df.columns[0],
                                   "CyberArk Onboarding by Environment") if has_pam else empty_fig("PAM")
    auth_pct = au.get("pct_integrated", 0)
    auth_fig = auth_gauge(auth_pct, "Auth Framework Integration")

    return html.Div([
        section_header(label, f"Detailed compliance view · {s['total']} records"),
        stat_row(kpi_items),

        # Charts row
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=comp_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=risk_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=pam_fig, config={"displayModeBar": False})),
                             className="shadow-sm border-0"), md=3, className="mb-3"),
            dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=auth_fig, config={"displayModeBar": False},
                                                    style={"height": "200px"})),
                             className="shadow-sm border-0"), md=3, className="mb-3"),
        ]),

        # Extra domain-specific charts
        html.Div(extra_charts_fn(df) if extra_charts_fn else []),

        # Filter + Table
        dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col(html.Strong(f"Records ({s['total']})", className="text-dark"), className="d-flex align-items-center"),
                    dbc.Col([
                        dbc.Button([html.I(className="bi bi-filetype-csv me-1"), "CSV"],
                                   id={"type": "dl-csv", "dataset": dataset},
                                   color="outline-secondary", size="sm", className="me-2"),
                        dbc.Button([html.I(className="bi bi-file-earmark-excel me-1"), "Excel"],
                                   id={"type": "dl-xlsx", "dataset": dataset},
                                   color="outline-success", size="sm"),
                    ], className="text-end"),
                ])
            ]),
            dbc.CardBody([
                filter_bar(dataset, df, available_filters),
                html.Div(id={"type": "table-container", "dataset": dataset},
                         children=compliance_table(df, f"tbl-{dataset}", vis_cols)),
            ]),
        ], className="shadow-sm border-0 mb-3"),

        dcc.Download(id={"type": "download-csv",  "dataset": dataset}),
        dcc.Download(id={"type": "download-xlsx", "dataset": dataset}),
    ], className="p-4")


# ─────────────────────────────────────────────
# EXTRA CHARTS — domain specific
# ─────────────────────────────────────────────
def extra_nonhuman(df: pd.DataFrame) -> list:
    if "Bot_Type" in df.columns:
        fig = compliance_bar(df, "Bot_Type", "Compliance by Bot Type")
        return [dbc.Row([dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={"displayModeBar": False})),
                                          className="shadow-sm border-0"), md=6)], className="mb-3")]
    if "Agent_Type" in df.columns:
        fig = compliance_bar(df, "Agent_Type", "Compliance by Agent Type")
        return [dbc.Row([dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={"displayModeBar": False})),
                                          className="shadow-sm border-0"), md=6)], className="mb-3")]
    return []


def extra_breakglass(df: pd.DataFrame) -> list:
    fig = breakglass_bar(df, "Break-Glass — CyberArk Onboarding Status")
    pwd_vc = df["Password_Mgmt"].value_counts().to_dict() if "Password_Mgmt" in df.columns else {}
    pwd_fig = pwd_mgmt_donut(pwd_vc, "Password Management")
    return [dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={"displayModeBar": False})),
                         className="shadow-sm border-0"), md=6, className="mb-3"),
        dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=pwd_fig, config={"displayModeBar": False})),
                         className="shadow-sm border-0"), md=6, className="mb-3"),
    ])]


# ─────────────────────────────────────────────
# PAGE: ADMIN — FIELD CONFIG
# ─────────────────────────────────────────────
def page_admin(role: str, field_config: dict) -> html.Div:
    if role != "Admin":
        return html.Div([
            dbc.Alert("Access denied — Admin role required.", color="danger", className="m-4"),
        ])

    config_display = []
    for ds, roles in field_config.items():
        rows = []
        for r, cols in roles.items():
            col_display = ", ".join(cols) if cols else "All columns visible"
            rows.append(html.Tr([html.Td(r), html.Td(col_display, style={"fontSize": "11px", "color": "#555"})]))
        config_display.append(dbc.Card([
            dbc.CardHeader(html.Strong(LABEL_MAP.get(ds, ds))),
            dbc.CardBody(dbc.Table([
                html.Thead(html.Tr([html.Th("Role"), html.Th("Visible Columns")])),
                html.Tbody(rows),
            ], bordered=True, hover=True, size="sm", className="mb-0")),
        ], className="shadow-sm border-0 mb-3"))

    users_df = load_users()
    users_table = dash_table.DataTable(
        columns=[{"name": c.replace("_", " "), "id": c} for c in ["username", "role", "display_name"]],
        data=users_df[["username", "role", "display_name"]].to_dict("records"),
        style_header={"backgroundColor": "#1f3a5f", "color": "white", "fontWeight": "600", "fontSize": "11px"},
        style_data={"fontSize": "12px", "padding": "7px 12px"},
        style_table={"overflowX": "auto"},
    )

    return html.Div([
        section_header("Admin — Field Configuration", "Role-based column visibility settings"),
        dbc.Alert([
            html.I(className="bi bi-info-circle me-2"),
            "Roles set to 'None' see all columns. Modify ",
            html.Code("data/field_config.json"),
            " to customise visibility per role per dataset."
        ], color="info", className="mb-3"),
        html.H6("User Registry", className="fw-semibold mb-2", style={"color": "#1f3a5f"}),
        dbc.Card(dbc.CardBody(users_table), className="shadow-sm border-0 mb-4"),
        html.H6("Field Visibility Configuration", className="fw-semibold mb-2", style={"color": "#1f3a5f"}),
        *config_display,
    ], className="p-4")


# ─────────────────────────────────────────────
# PAGE: DYNAMIC QUERY
# ─────────────────────────────────────────────
def page_query() -> html.Div:
    dataset_opts = [{"label": v, "value": k} for k, v in LABEL_MAP.items()]
    return html.Div([
        section_header("Dynamic Query", "Ad-hoc compliance queries across any dataset"),
        dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Dataset", className="fw-semibold small"),
                        dcc.Dropdown(id="q-dataset", options=dataset_opts,
                                     placeholder="Select dataset…", clearable=False,
                                     style={"fontSize": "13px"}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Filter column", className="fw-semibold small"),
                        dcc.Dropdown(id="q-col", options=[], placeholder="Select column…",
                                     style={"fontSize": "13px"}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Filter value", className="fw-semibold small"),
                        dcc.Dropdown(id="q-val", options=[], placeholder="Select value…",
                                     style={"fontSize": "13px"}),
                    ], md=3),
                    dbc.Col([
                        dbc.Label("Group by", className="fw-semibold small"),
                        dcc.Dropdown(id="q-group", options=[], placeholder="Group results by…",
                                     style={"fontSize": "13px"}),
                    ], md=3),
                ], className="mb-3"),
                dbc.Button([html.I(className="bi bi-search me-1"), "Run Query"],
                           id="q-run", color="primary", className="me-2",
                           style={"background": "#1a2f4a", "borderColor": "#1a2f4a"}),
                dbc.Button([html.I(className="bi bi-filetype-csv me-1"), "Export CSV"],
                           id="q-csv", color="outline-secondary", className="me-2"),
                dbc.Button([html.I(className="bi bi-file-earmark-excel me-1"), "Export Excel"],
                           id="q-xlsx", color="outline-success"),
                dcc.Download(id="q-download"),
            ])
        ], className="shadow-sm border-0 mb-3"),
        html.Div(id="q-chart-area"),
        html.Div(id="q-table-area"),
    ], className="p-4")


# ─────────────────────────────────────────────
# NON-HUMAN COMBINED PAGE
# ─────────────────────────────────────────────
def page_nonhuman(role: str, field_config: dict) -> html.Div:
    return html.Div([
        section_header("Service Accounts, Bots & AI Agents", "Non-human identity compliance"),
        dbc.Tabs([
            dbc.Tab(page_dataset("service_accounts", role, field_config), label="Service Accounts", tab_id="svc"),
            dbc.Tab(page_dataset("bot_accounts",     role, field_config, extra_charts_fn=extra_nonhuman), label="Bot Accounts", tab_id="bot"),
            dbc.Tab(page_dataset("ai_agents",        role, field_config), label="AI Agents", tab_id="ai"),
        ], active_tab="svc", className="mb-0"),
    ], className="p-4")


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
def render_page(pathname: str, session: dict) -> html.Div:
    if not pathname:
        pathname = "/"
    role = session.get("role", "")
    display_name = session.get("display_name", "")
    field_config = load_field_config()

    page_titles = {
        "/":            "Executive Summary",
        "/compliance":  "Compliance Overview",
        "/human":       "Human Accounts",
        "/privileged":  "Privileged Accounts",
        "/nonhuman":    "Service, Bot & AI Agents",
        "/windows":     "Windows Servers",
        "/linux":       "Linux Servers",
        "/network":     "Network Devices",
        "/virtual":     "Virtual / ESXi Assets",
        "/applications":"Applications",
        "/breakglass":  "Break-Glass Resources",
        "/admin":       "Admin — Field Config",
        "/query":       "Dynamic Query",
    }
    pt = page_titles.get(pathname, "IAM Dashboard")

    if pathname == "/":
        content = page_executive(role)
    elif pathname == "/compliance":
        content = page_compliance_overview(role)
    elif pathname == "/human":
        content = page_dataset("human_accounts", role, field_config)
    elif pathname == "/privileged":
        content = page_dataset("privileged_accounts", role, field_config)
    elif pathname == "/nonhuman":
        content = page_nonhuman(role, field_config)
    elif pathname == "/windows":
        content = page_dataset("windows_servers", role, field_config)
    elif pathname == "/linux":
        content = page_dataset("linux_servers", role, field_config)
    elif pathname == "/network":
        content = page_dataset("network_devices", role, field_config)
    elif pathname == "/virtual":
        content = page_dataset("virtual_assets", role, field_config)
    elif pathname == "/applications":
        content = page_dataset("applications", role, field_config)
    elif pathname == "/breakglass":
        content = page_dataset("breakglass", role, field_config, extra_charts_fn=extra_breakglass)
    elif pathname == "/admin":
        content = page_admin(role, field_config)
    elif pathname == "/query":
        content = page_query()
    else:
        content = html.Div("Page not found", className="p-4 text-muted")

    return html.Div([
        sidebar(role, pathname),
        html.Div([
            topbar(display_name, pt),
            content,
        ], style=CONTENT_STYLE),
    ])


# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────

# Main page wrapper
@app.callback(
    Output("page-wrapper", "children"),
    Output("login-panel", "style"),
    Input("session-store", "data"),
    Input("url", "pathname"),
)
def route(session, pathname):
    if not session or not session.get("logged_in"):
        return "", {"display": "block"}
    return render_page(pathname or "/", session), {"display": "none"}


# Login
@app.callback(
    Output("session-store", "data"),
    Output("login-error", "children"),
    Input("login-btn", "n_clicks"),
    State("login-user", "value"),
    State("login-pass",  "value"),
    State("session-store", "data"),
    prevent_initial_call=True,
)
def login(n_clicks, username, password, current_session):
    if current_session and current_session.get("logged_in"):
        return current_session, no_update
    if not n_clicks:
        return no_update, no_update
    if not username or not password:
        return current_session, "Please enter username and password."
    users = load_users()
    match = users[(users["username"] == username) & (users["password_hash"] == password)]
    if len(match):
        row = match.iloc[0]
        return {"logged_in": True, "role": row["role"],
                "username": username, "display_name": row["display_name"]}, ""
    return current_session, "Invalid credentials. Check the demo logins below."


# Logout
@app.callback(
    Output("session-store", "data", allow_duplicate=True),
    Output("url", "pathname"),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def logout(n):
    if not n:
        return no_update, no_update
    return {"logged_in": False, "role": None, "username": None, "display_name": None}, "/"


# ── Dynamic Query: populate columns from selected dataset ──
@app.callback(
    Output("q-col",   "options"),
    Output("q-group", "options"),
    Input("q-dataset", "value"),
    prevent_initial_call=True,
)
def update_query_cols(dataset):
    if not dataset:
        return [], []
    try:
        df = load(dataset)
        opts = [{"label": c.replace("_", " "), "value": c} for c in df.columns]
        return opts, opts
    except Exception:
        return [], []


@app.callback(
    Output("q-val", "options"),
    Input("q-col",     "value"),
    State("q-dataset", "value"),
    prevent_initial_call=True,
)
def update_query_vals(col, dataset):
    if not col or not dataset:
        return []
    try:
        df = load(dataset)
        vals = [{"label": str(v), "value": str(v)}
                for v in sorted(df[col].dropna().unique())]
        return [{"label": "All", "value": "ALL"}] + vals
    except Exception:
        return []


@app.callback(
    Output("q-chart-area", "children"),
    Output("q-table-area", "children"),
    Input("q-run", "n_clicks"),
    State("q-dataset", "value"),
    State("q-col",     "value"),
    State("q-val",     "value"),
    State("q-group",   "value"),
    prevent_initial_call=True,
)
def run_query(n, dataset, col, val, group):
    if not dataset:
        return dbc.Alert("Select a dataset first.", color="warning"), ""
    try:
        df = load(dataset)
        if col and val and val != "ALL":
            df = df[df[col].astype(str) == val]
        chart_row = []
        if group and group in df.columns:
            if "Compliance_Status" in df.columns:
                fig = compliance_bar(df, group, f"Compliance by {group.replace('_',' ')}")
                chart_row.append(
                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig, config={"displayModeBar": False})),
                                     className="shadow-sm border-0"), md=6, className="mb-3")
                )
            if "Risk_Rating" in df.columns:
                fig2 = risk_bar(df, group, f"Risk by {group.replace('_',' ')}")
                chart_row.append(
                    dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(figure=fig2, config={"displayModeBar": False})),
                                     className="shadow-sm border-0"), md=6, className="mb-3")
                )

        table = compliance_table(df, "q-result-table")
        return (dbc.Row(chart_row) if chart_row else "",
                dbc.Card([
                    dbc.CardHeader(html.Strong(f"Query results — {len(df)} records")),
                    dbc.CardBody(table),
                ], className="shadow-sm border-0"))
    except Exception as e:
        return dbc.Alert(f"Query error: {e}", color="danger"), ""


# ── CSV export (pattern-match on dataset-level buttons) ──
@app.callback(
    Output({"type": "download-csv", "dataset": MATCH}, "data"),
    Input({"type": "dl-csv",        "dataset": MATCH}, "n_clicks"),
    State({"type": "dl-csv",        "dataset": MATCH}, "id"),
    prevent_initial_call=True,
)
def export_csv(n, btn_id):
    if not n:
        return no_update
    dataset = btn_id["dataset"]
    df = load(dataset)
    label = LABEL_MAP.get(dataset, dataset).replace(" ", "_")
    return dcc.send_bytes(df_to_csv_bytes(df), f"IAM_{label}_{pd.Timestamp.now().strftime('%Y%m%d')}.csv")


# ── Excel export ──
@app.callback(
    Output({"type": "download-xlsx", "dataset": MATCH}, "data"),
    Input({"type": "dl-xlsx",        "dataset": MATCH}, "n_clicks"),
    State({"type": "dl-xlsx",        "dataset": MATCH}, "id"),
    prevent_initial_call=True,
)
def export_xlsx(n, btn_id):
    if not n:
        return no_update
    dataset = btn_id["dataset"]
    df = load(dataset)
    # Stringify datetimes for excel
    df2 = df.copy()
    for c in df2.columns:
        if pd.api.types.is_datetime64_any_dtype(df2[c]):
            df2[c] = df2[c].dt.strftime("%Y-%m-%d")
    label = LABEL_MAP.get(dataset, dataset).replace(" ", "_")
    xl_bytes = df_to_excel_bytes({label: df2.fillna("")})
    return dcc.send_bytes(xl_bytes, f"IAM_{label}_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx")


# ── Dynamic query export ──
@app.callback(
    Output("q-download", "data"),
    Input("q-csv",  "n_clicks"),
    Input("q-xlsx", "n_clicks"),
    State("q-dataset", "value"),
    State("q-col",     "value"),
    State("q-val",     "value"),
    prevent_initial_call=True,
)
def query_download(csv_n, xlsx_n, dataset, col, val):
    if not dataset:
        return no_update
    triggered = ctx.triggered_id
    df = load(dataset)
    if col and val and val != "ALL":
        df = df[df[col].astype(str) == val]
    df2 = df.copy()
    for c in df2.columns:
        if pd.api.types.is_datetime64_any_dtype(df2[c]):
            df2[c] = df2[c].dt.strftime("%Y-%m-%d")
    label = LABEL_MAP.get(dataset, dataset).replace(" ", "_")
    ts = pd.Timestamp.now().strftime("%Y%m%d")
    if triggered == "q-csv":
        return dcc.send_bytes(df_to_csv_bytes(df2), f"IAM_Query_{label}_{ts}.csv")
    xl_bytes = df_to_excel_bytes({label: df2.fillna("")})
    return dcc.send_bytes(xl_bytes, f"IAM_Query_{label}_{ts}.xlsx")


# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

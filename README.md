# IAM Compliance Dashboard

Production-grade IAM & PAM compliance reporting dashboard built with **Plotly Dash 4**.

## Architecture decision

| Framework | Why chosen |
|---|---|
| **Plotly Dash** | Python-native, zero JS required, reactive callbacks, built-in DataTable with filter/sort/export, enterprise-grade charting, open-source (MIT) |
| **Dash Bootstrap Components** | Production-quality layout, responsive grid, Bootstrap 5 |
| **Pandas** | Flat-file → DataFrame → DB-agnostic data layer |
| **openpyxl** | Styled Excel export with conditional formatting |

## Features

- **Role-based access**: Executive / Leadership / Operations / Admin — each sees a tailored UI
- **Field-level visibility**: Admins configure which columns each role sees via `data/field_config.json`
- **13 pages** covering all identity and asset domains
- **11 datasets** — 1,090 simulated records across Human, Privileged, Service, Bot, AI Agent, Windows, Linux, Network, Virtual/ESXi, Applications, Break-Glass
- **CyberArk onboarding & password compliance** tracking on every domain
- **Auth framework integration** status on every domain
- **Break-glass resource governance** dedicated page
- **Dynamic Query** — ad-hoc cross-domain exploration with grouping + charting
- **CSV & Excel export** with conditional colour-coding on every page
- **Swap data layer**: replace `utils/data_loader.py` `load()` with SQLAlchemy / CyberArk API / CMDB REST calls

## Quick start

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python utils/generate_data.py   # regenerate flat files
.venv/bin/python app.py                    # runs on http://localhost:8050
```

## Deploy on Render

This Dash app includes a `render.yaml` deployment configuration. To deploy it,
sign in to Render, choose **New > Blueprint**, connect the GitHub repository,
and select the `main` branch. Render will install the requirements and start
the app with Gunicorn. The generated `onrender.com` URL can be shared with
your office.

## Demo credentials

| Username | Password | Role |
|---|---|---|
| exec_admin | exec123 | Executive |
| leader_ops | lead123 | Leadership |
| ops_analyst | ops123 | Operations |
| rpt_admin | admin123 | Admin |

## Customising field visibility

Edit `data/field_config.json`. Set a role's value to `null` for full column access, or a JSON array of column names to restrict visibility.

## Replacing flat files with a database

In `utils/data_loader.py`, replace:
```python
df = pd.read_csv(path, ...)
```
with your SQLAlchemy / CyberArk REST / CMDB call:
```python
df = pd.read_sql("SELECT * FROM iam_records WHERE domain = ?", engine, params=[dataset])
```
No other code changes needed.

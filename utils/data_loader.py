"""
Central data access layer. Swap CSV reads for DB queries here in production.
"""
from __future__ import annotations

import pandas as pd
import json
import os
from functools import lru_cache

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

DATASETS = {
    "human_accounts":      "human_accounts.csv",
    "privileged_accounts": "privileged_accounts.csv",
    "service_accounts":    "service_accounts.csv",
    "bot_accounts":        "bot_accounts.csv",
    "ai_agents":           "ai_agents.csv",
    "windows_servers":     "windows_servers.csv",
    "linux_servers":       "linux_servers.csv",
    "network_devices":     "network_devices.csv",
    "virtual_assets":      "virtual_assets.csv",
    "applications":        "applications.csv",
    "breakglass":          "breakglass.csv",
}

LABEL_MAP = {
    "human_accounts":      "Human Accounts",
    "privileged_accounts": "Privileged Accounts",
    "service_accounts":    "Service Accounts",
    "bot_accounts":        "Bot Accounts",
    "ai_agents":           "AI Agents",
    "windows_servers":     "Windows Servers",
    "linux_servers":       "Linux Servers",
    "network_devices":     "Network Devices",
    "virtual_assets":      "Virtual / ESXi Assets",
    "applications":        "Applications",
    "breakglass":          "Break-Glass Resources",
}

STATUS_COLORS = {
    "Compliant":           "#0ca30c",
    "Non-Compliant":       "#d03b3b",
    "Partially Compliant": "#fab219",
    "Exception Approved":  "#6250d6",
    "Not Assessed":        "#888780",
    "Remediation In Progress": "#2a78d6",
    "Unknown":             "#b4b2a9",
}

RISK_COLORS = {
    "Critical": "#d03b3b",
    "High":     "#fab219",
    "Medium":   "#2a78d6",
    "Low":      "#0ca30c",
}

def load(dataset: str) -> pd.DataFrame:
    path = os.path.join(BASE, DATASETS[dataset])
    df = pd.read_csv(path, low_memory=False)
    # Normalize date columns for sorting
    for col in df.columns:
        if "Date" in col or "Due" in col or "Updated" in col or "Review" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    return df

def load_users() -> pd.DataFrame:
    return pd.read_csv(os.path.join(BASE, "users.csv"))

def load_field_config() -> dict:
    with open(os.path.join(BASE, "field_config.json")) as f:
        return json.load(f)

def get_visible_columns(dataset: str, role: str, field_config: dict) -> list | None:
    """Return column list for role, or None meaning show all."""
    cfg = field_config.get(dataset, {})
    cols = cfg.get(role)
    return cols  # None → show all

def compliance_summary(df: pd.DataFrame) -> dict:
    col = "Compliance_Status"
    if col not in df.columns:
        return {}
    vc = df[col].value_counts()
    total = len(df)
    pct_compliant = round(vc.get("Compliant", 0) / total * 100, 1) if total else 0
    return {
        "total": total,
        "compliant": int(vc.get("Compliant", 0)),
        "non_compliant": int(vc.get("Non-Compliant", 0)),
        "partial": int(vc.get("Partially Compliant", 0)),
        "exception": int(vc.get("Exception Approved", 0)),
        "not_assessed": int(vc.get("Not Assessed", 0)),
        "pct_compliant": pct_compliant,
        "breakdown": vc.to_dict(),
    }

def cyberark_summary(df: pd.DataFrame) -> dict:
    col = "PAM_Onboarded"
    if col not in df.columns:
        return {}
    vc = df[col].value_counts()
    total = len(df)
    return {
        "total": total,
        "onboarded": int(vc.get("Onboarded", 0)),
        "not_onboarded": int(vc.get("Not Onboarded", 0)),
        "pending": int(vc.get("Pending", 0)),
        "exempted": int(vc.get("Exempted", 0)),
        "pct_onboarded": round(vc.get("Onboarded", 0) / total * 100, 1) if total else 0,
    }

def pwd_mgmt_summary(df: pd.DataFrame) -> dict:
    col = "Password_Mgmt"
    if col not in df.columns:
        return {}
    vc = df[col].value_counts()
    total = len(df[df[col] != "Not Applicable"])
    return {
        "automatic": int(vc.get("Automatic", 0)),
        "manual": int(vc.get("Manual", 0)),
        "not_configured": int(vc.get("Not Configured", 0)),
        "exempted": int(vc.get("Exempted", 0)),
        "pct_automatic": round(vc.get("Automatic", 0) / total * 100, 1) if total else 0,
    }

def auth_summary(df: pd.DataFrame) -> dict:
    col = "Auth_Framework_Integration"
    if col not in df.columns:
        return {}
    vc = df[col].value_counts()
    total = len(df)
    return {
        "integrated": int(vc.get("Integrated", 0)),
        "not_integrated": int(vc.get("Not Integrated", 0)),
        "partial": int(vc.get("Partial", 0)),
        "exempted": int(vc.get("Exempted", 0)),
        "pct_integrated": round(vc.get("Integrated", 0) / total * 100, 1) if total else 0,
    }

def global_kpis() -> dict:
    """Aggregate KPIs across all datasets for executive view."""
    all_records = 0
    all_compliant = 0
    all_non_compliant = 0
    all_pam_onboarded = 0
    all_pam_total = 0
    all_pwd_auto = 0
    all_pwd_total = 0
    all_auth_int = 0
    all_auth_total = 0
    critical_findings = 0
    high_findings = 0

    for ds in DATASETS:
        try:
            df = load(ds)
        except Exception:
            continue
        all_records += len(df)
        if "Compliance_Status" in df.columns:
            all_compliant += (df["Compliance_Status"] == "Compliant").sum()
            all_non_compliant += (df["Compliance_Status"] == "Non-Compliant").sum()
        if "PAM_Onboarded" in df.columns:
            all_pam_onboarded += (df["PAM_Onboarded"] == "Onboarded").sum()
            all_pam_total += len(df)
        if "Password_Mgmt" in df.columns:
            sub = df[df["Password_Mgmt"] != "Not Applicable"]
            all_pwd_auto += (sub["Password_Mgmt"] == "Automatic").sum()
            all_pwd_total += len(sub)
        if "Auth_Framework_Integration" in df.columns:
            all_auth_int += (df["Auth_Framework_Integration"] == "Integrated").sum()
            all_auth_total += len(df)
        if "Critical_Vulnerability_Count" in df.columns:
            critical_findings += int(df["Critical_Vulnerability_Count"].fillna(0).sum())
        if "High_Vulnerability_Count" in df.columns:
            high_findings += int(df["High_Vulnerability_Count"].fillna(0).sum())

    return {
        "total_records": all_records,
        "compliant": all_compliant,
        "non_compliant": all_non_compliant,
        "pct_compliant": round(all_compliant / all_records * 100, 1) if all_records else 0,
        "pam_onboarded": all_pam_onboarded,
        "pam_total": all_pam_total,
        "pct_pam": round(all_pam_onboarded / all_pam_total * 100, 1) if all_pam_total else 0,
        "pwd_auto": all_pwd_auto,
        "pwd_total": all_pwd_total,
        "pct_pwd_auto": round(all_pwd_auto / all_pwd_total * 100, 1) if all_pwd_total else 0,
        "auth_integrated": all_auth_int,
        "auth_total": all_auth_total,
        "pct_auth": round(all_auth_int / all_auth_total * 100, 1) if all_auth_total else 0,
        "critical_findings": critical_findings,
        "high_findings": high_findings,
    }

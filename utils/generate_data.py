"""
Flat-file data generator for IAM Compliance Dashboard simulation.
Run once to produce CSV files in /data. Replace with DB queries later.
"""
import pandas as pd
import numpy as np
import random
import json
import os
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
os.makedirs(BASE, exist_ok=True)

NOW = datetime.now()

def rdate(days_back=365, days_fwd=90):
    delta = random.randint(-days_back, days_fwd)
    return (NOW + timedelta(days=delta)).strftime("%Y-%m-%d")

def past(days_back=180):
    return (NOW - timedelta(days=random.randint(1, days_back))).strftime("%Y-%m-%d")

def future(days_fwd=180):
    return (NOW + timedelta(days=random.randint(1, days_fwd))).strftime("%Y-%m-%d")

STATUS = ["Compliant", "Non-Compliant", "Partially Compliant", "Exception Approved", "Not Assessed"]
RISK   = ["Critical", "High", "Medium", "Low"]
ENVS   = ["Production", "DR", "UAT", "QA", "Development"]
BUS    = ["Finance", "Operations", "Engineering", "Security", "HR", "Legal", "Marketing"]
OWNERS = ["IAM Team", "Platform Ops", "AppSec", "SOC", "Network Ops", "DevOps", "DBA Team"]
CYBERARK_STATUS = ["Onboarded", "Not Onboarded", "Pending", "Exempted"]
PWD_MGMT = ["Automatic", "Manual", "Not Configured", "Exempted"]
AUTH_INT  = ["Integrated", "Not Integrated", "Partial", "Exempted"]
FRAMEWORKS = ["NIST 800-53", "PCI DSS", "SOX", "HIPAA", "ISO 27001"]


def weighted(choices, weights):
    return random.choices(choices, weights=weights, k=1)[0]

def cyberark_status():
    return weighted(CYBERARK_STATUS, [55, 25, 12, 8])

def pwd_mgmt():
    return weighted(PWD_MGMT, [50, 28, 14, 8])

def auth_int():
    return weighted(AUTH_INT, [60, 22, 12, 6])

def comp_status():
    return weighted(STATUS, [50, 22, 14, 8, 6])

def risk_level():
    return weighted(RISK, [10, 25, 40, 25])


# ─────────────────────────────────────────────
# 1. HUMAN ACCOUNTS
# ─────────────────────────────────────────────
def gen_human_accounts(n=200):
    rows = []
    for i in range(n):
        emp_type = weighted(["Employee","Contractor","Vendor","Partner","Intern"], [55,20,12,8,5])
        priv = weighted([True, False], [30, 70])
        ca_status = cyberark_status()
        rows.append({
            "Account_ID": f"USR-{i+1000:04d}",
            "Account_Name": f"user{i+1000}@corp.com",
            "Display_Name": f"User {i+1000}",
            "Employment_Type": emp_type,
            "Department": random.choice(BUS),
            "Business_Unit": random.choice(BUS),
            "Account_Status": weighted(["Enabled","Disabled","Locked","Expired"], [72,15,8,5]),
            "Account_Creation_Date": past(730),
            "Last_Login_Date": past(90),
            "Inactivity_Days": random.randint(0, 180),
            "MFA_Status": weighted(["Enforced","Enrolled","Exception","Not Applicable"], [60,20,12,8]),
            "Privileged_Access_Flag": priv,
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt() if priv else "Not Applicable",
            "Auth_Framework_Integration": auth_int(),
            "Access_Review_Status": weighted(["Certified","Pending","Overdue","Revoked"], [55,20,18,7]),
            "Last_Access_Review": past(180),
            "Next_Access_Review": future(180),
            "Deprovisioning_Status": weighted(["Not Applicable","Completed","Pending","Overdue"], [70,15,10,5]),
            "Remediation_Owner": random.choice(OWNERS),
            "Environment": random.choice(ENVS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Record_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 2. PRIVILEGED HUMAN ACCOUNTS
# ─────────────────────────────────────────────
def gen_privileged_accounts(n=100):
    tiers = ["Tier-0 Domain Admin","Tier-1 Server Admin","Tier-2 App Admin","Cloud Admin","DB Admin","Network Admin"]
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Account_ID": f"PADM-{i+500:04d}",
            "Account_Name": f"adm-user{i+500}",
            "Linked_Standard_ID": f"USR-{random.randint(1000,1199):04d}",
            "Privilege_Tier": random.choice(tiers),
            "Privilege_Scope": random.choice(["Domain","Server","Database","Cloud","Application","Network"]),
            "Department": random.choice(BUS),
            "Account_Status": weighted(["Enabled","Disabled","Locked"], [70,20,10]),
            "PAM_Onboarded": ca_status,
            "PAM_Safe": f"Safe-{random.choice(['Domain','Server','DB','Cloud'])}-{random.randint(1,5)}",
            "Password_Mgmt": pwd_mgmt(),
            "Last_Credential_Rotation": past(90),
            "Next_Rotation_Due": future(60),
            "Rotation_Status": weighted(["Compliant","Overdue","Failed","Exception"], [55,25,12,8]),
            "JIT_Enabled": weighted(["Yes","No","Partial"], [45,40,15]),
            "Session_Recording": weighted(["Enabled","Disabled","Exception"], [65,25,10]),
            "MFA_Status": weighted(["Enforced","Exception","Bypassed"], [70,20,10]),
            "Auth_Framework_Integration": auth_int(),
            "Access_Review_Status": weighted(["Certified","Overdue","Pending"], [50,30,20]),
            "Last_Access_Review": past(90),
            "Next_Access_Review": future(90),
            "Compliance_Status": comp_status(),
            "Risk_Rating": weighted(["Critical","High","Medium"], [20,45,35]),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 3. SERVICE ACCOUNTS
# ─────────────────────────────────────────────
def gen_service_accounts(n=150):
    acct_types = ["Service","Application","Batch","Integration","Database","API","System"]
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Account_ID": f"SVC-{i+2000:04d}",
            "Account_Name": f"svc-{random.choice(['app','db','int','batch','api'])}-{i:03d}",
            "Account_Type": random.choice(acct_types),
            "Service_Application": f"APP-{random.randint(100,199)}",
            "Business_Owner": random.choice(BUS),
            "Technical_Owner": random.choice(OWNERS),
            "Environment": random.choice(ENVS),
            "Account_Status": weighted(["Enabled","Disabled","Pending Retirement"], [70,20,10]),
            "Interactive_Logon_Allowed": weighted(["Yes","No"], [15,85]),
            "Privileged_Access_Flag": weighted([True, False], [55, 45]),
            "PAM_Onboarded": ca_status,
            "PAM_Safe": f"Safe-Svc-{random.randint(1,8)}" if ca_status == "Onboarded" else "N/A",
            "Password_Mgmt": pwd_mgmt(),
            "Last_Rotation_Date": past(90),
            "Next_Rotation_Due": future(60),
            "Rotation_Status": weighted(["Compliant","Overdue","Failed","Exception"], [50,28,12,10]),
            "Hardcoded_Secret_Status": weighted(["None Known","Suspected","Confirmed","Remediating"], [60,18,12,10]),
            "Auth_Framework_Integration": auth_int(),
            "Least_Privilege_Status": weighted(["Compliant","Excessive","Non-Compliant","Exception"], [52,25,15,8]),
            "Inactivity_Days": random.randint(0, 200),
            "Last_Access_Review": past(180),
            "Next_Access_Review": future(180),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 4. BOT ACCOUNTS
# ─────────────────────────────────────────────
def gen_bot_accounts(n=80):
    bot_types = ["RPA","CI/CD","Monitoring","Chat-Ops","Integration","Test Automation","Deployment"]
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Bot_Account_ID": f"BOT-{i+3000:04d}",
            "Bot_Name": f"bot-{random.choice(['rpa','cicd','mon','deploy','test'])}-{i:03d}",
            "Bot_Type": random.choice(bot_types),
            "Business_Process": f"Process-{random.randint(1,20)}",
            "Business_Owner": random.choice(BUS),
            "Technical_Owner": random.choice(OWNERS),
            "Environment": random.choice(ENVS),
            "Account_Status": weighted(["Active","Disabled","Paused","Pending Retirement"], [65,18,10,7]),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Auth_Framework_Integration": auth_int(),
            "Privilege_Scope": random.choice(["Read-Only","Limited Write","Write","Privileged","Administrative"]),
            "Human_Impersonation_Allowed": weighted(["Yes","No"], [10,90]),
            "Interactive_Login_Allowed": weighted(["Yes","No"], [15,85]),
            "Logging_Status": weighted(["Enabled","Disabled","Partial"], [65,20,15]),
            "Last_Execution_Date": past(30),
            "Last_Privilege_Review": past(180),
            "Next_Privilege_Review": future(90),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 5. AI AGENT ACCOUNTS
# ─────────────────────────────────────────────
def gen_ai_agents(n=40):
    agent_types = ["Chat Assistant","Coding Agent","Security Agent","Workflow Agent","RAG Agent","Autonomous Agent"]
    rows = []
    for i in range(n):
        rows.append({
            "Agent_ID": f"AI-{i+4000:04d}",
            "Agent_Name": f"ai-agent-{random.choice(['secops','coding','rag','workflow','chat'])}-{i:02d}",
            "Agent_Type": random.choice(agent_types),
            "Agent_Purpose": f"Approved workflow {random.randint(1,15)}",
            "Business_Owner": random.choice(BUS),
            "Technical_Owner": random.choice(OWNERS),
            "Model_Provider": random.choice(["Anthropic","OpenAI","Internal","Azure OpenAI"]),
            "Deployment_Model": random.choice(["On-Premises","Private Cloud","SaaS"]),
            "Environment": random.choice(["Production","Pilot","Sandbox","Development"]),
            "Agent_Status": weighted(["Active","Pilot","Disabled","Pending Approval"], [40,25,20,15]),
            "Authorization_Status": weighted(["Approved","Conditional","Expired","Pending"], [45,25,15,15]),
            "PAM_Onboarded": cyberark_status(),
            "Auth_Framework_Integration": auth_int(),
            "Human_Approval_Required": weighted(["Yes","No"], [75,25]),
            "Approval_Gate_Defined": weighted(["Yes","No","Partial"], [50,30,20]),
            "Stop_Condition_Defined": weighted(["Yes","No","Partial"], [55,25,20]),
            "Activity_Log_Reference": weighted(["Defined","Missing","Partial"], [55,25,20]),
            "Kill_Switch_Defined": weighted(["Yes","No"], [65,35]),
            "External_Network_Access": weighted(["Disabled","Restricted","Approved","Prohibited"], [45,30,15,10]),
            "Data_Classification_Authorized": random.choice(["Public","Internal","Confidential","Restricted"]),
            "Last_Security_Assessment": past(180),
            "Next_Access_Review": future(90),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 6. WINDOWS SERVERS
# ─────────────────────────────────────────────
def gen_windows_servers(n=120):
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Asset_ID": f"WIN-{i+100:04d}",
            "Asset_Name": f"WIN-{random.choice(['APP','DB','WEB','DC','FILE','RDS'])}-{random.choice(['PROD','DR','UAT'])}-{i:02d}",
            "FQDN": f"win-server-{i:03d}.corp.local",
            "IP_Address_v4": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "Operating_System": random.choice(["Windows Server 2019","Windows Server 2022","Windows Server 2016"]),
            "OS_Build": f"{random.choice(['17763','20348','14393'])}.{random.randint(3000,5000)}",
            "Environment": random.choice(ENVS),
            "Business_Unit": random.choice(BUS),
            "Criticality": weighted(["Critical","High","Medium","Low"], [20,35,30,15]),
            "Patch_Compliance_Status": weighted(["Compliant","Overdue","Failed","Exception"], [58,25,10,7]),
            "Last_Patch_Date": past(90),
            "Endpoint_Protection_Status": weighted(["Healthy","Unhealthy","Not Installed","Stale"], [65,18,10,7]),
            "Critical_Vulnerability_Count": random.randint(0, 12),
            "High_Vulnerability_Count": random.randint(0, 25),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Local_Admin_Count": random.randint(1, 8),
            "Shared_Admin_Account": weighted(["Controlled","Uncontrolled","Disabled"], [55,30,15]),
            "Auth_Framework_Integration": auth_int(),
            "Encryption_Status": weighted(["Enabled","Disabled","Partial"], [70,20,10]),
            "Backup_Status": weighted(["Successful","Failed","Overdue"], [72,15,13]),
            "Network_Zone": random.choice(["Internal","DMZ","Restricted","Management"]),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Record_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 7. LINUX SERVERS
# ─────────────────────────────────────────────
def gen_linux_servers(n=100):
    distros = ["RHEL 8","RHEL 9","Ubuntu 22.04","Ubuntu 24.04","Amazon Linux 2","SUSE 15"]
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Asset_ID": f"LNX-{i+200:04d}",
            "Asset_Name": f"LNX-{random.choice(['APP','DB','WEB','K8S','MON'])}-{random.choice(['PROD','DR','UAT'])}-{i:02d}",
            "FQDN": f"lnx-server-{i:03d}.corp.local",
            "IP_Address_v4": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "OS_Distribution": random.choice(distros),
            "Kernel_Version": f"{random.randint(5,6)}.{random.randint(10,19)}.{random.randint(0,50)}-generic",
            "Environment": random.choice(ENVS),
            "Business_Unit": random.choice(BUS),
            "Criticality": weighted(["Critical","High","Medium","Low"], [20,35,30,15]),
            "Patch_Compliance_Status": weighted(["Compliant","Overdue","Failed","Exception"], [55,28,10,7]),
            "Last_Patch_Date": past(90),
            "Root_Login_Status": weighted(["Disabled","Enabled","Conditional"], [60,25,15]),
            "SSH_Hardening_Status": weighted(["Compliant","Non-Compliant","Partial"], [55,28,17]),
            "Critical_Vulnerability_Count": random.randint(0, 15),
            "High_Vulnerability_Count": random.randint(0, 30),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Auth_Framework_Integration": auth_int(),
            "Audit_Logging_Status": weighted(["Enabled","Disabled","Partial"], [65,20,15]),
            "Disk_Encryption_Status": weighted(["Enabled","Disabled","Partial"], [60,28,12]),
            "Backup_Status": weighted(["Successful","Failed","Overdue"], [70,15,15]),
            "Network_Zone": random.choice(["Internal","DMZ","Restricted","Management"]),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Record_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 8. NETWORK DEVICES
# ─────────────────────────────────────────────
def gen_network_devices(n=80):
    device_types = ["Router","Switch","Firewall","Load Balancer","WAF","VPN Gateway","IDS/IPS","Wireless Controller"]
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "Asset_ID": f"NET-{i+300:04d}",
            "Device_Name": f"NET-{random.choice(['RTR','SWC','FW','LB','VPN'])}-{random.choice(['CORE','EDGE','DMZ'])}-{i:02d}",
            "Device_Type": random.choice(device_types),
            "Manufacturer": random.choice(["Cisco","Palo Alto","Fortinet","Juniper","F5","Aruba"]),
            "Firmware_Version": f"{random.randint(8,17)}.{random.randint(0,9)}.{random.randint(0,9)}",
            "Management_IP": f"10.{random.randint(1,10)}.{random.randint(1,20)}.{random.randint(1,254)}",
            "Environment": random.choice(ENVS),
            "Business_Unit": random.choice(BUS),
            "Criticality": weighted(["Critical","High","Medium","Low"], [25,40,25,10]),
            "Insecure_Protocol_Status": weighted(["None","Telnet Exposed","HTTP Exposed","SNMPv1"], [55,20,15,10]),
            "AAA_Integration_Status": auth_int(),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Auth_Framework_Integration": auth_int(),
            "Config_Backup_Status": weighted(["Successful","Failed","Overdue"], [68,18,14]),
            "Configuration_Compliance": weighted(["Compliant","Non-Compliant","Exception"], [60,28,12]),
            "Internet_Exposed": weighted(["Yes","No"], [25,75]),
            "Network_Zone": random.choice(["Core","DMZ","Edge","Management","OT"]),
            "Critical_Vulnerability_Count": random.randint(0, 8),
            "High_Vulnerability_Count": random.randint(0, 15),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Record_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 9. ESXI / VIRTUAL ASSETS
# ─────────────────────────────────────────────
def gen_virtual_assets(n=80):
    rows = []
    for i in range(n):
        is_vm = random.random() > 0.3
        ca_status = cyberark_status()
        rows.append({
            "Asset_ID": f"{'VM' if is_vm else 'ESX'}-{i+400:04d}",
            "Asset_Name": f"{'VM' if is_vm else 'ESXI'}-{random.choice(['PROD','DR','UAT'])}-{i:03d}",
            "Asset_Type": "Virtual Machine" if is_vm else "ESXi Host",
            "Hypervisor_Version": f"ESXi {random.choice(['7.0','8.0'])}.{random.randint(0,3)}",
            "vCenter_Managed": weighted(["Yes","No"], [80,20]),
            "IP_Address_v4": f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}",
            "Environment": random.choice(ENVS),
            "Business_Unit": random.choice(BUS),
            "Criticality": weighted(["Critical","High","Medium","Low"], [20,35,30,15]),
            "Patch_Compliance_Status": weighted(["Compliant","Overdue","Failed","Exception"], [58,25,10,7]),
            "Last_Patch_Date": past(90),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Auth_Framework_Integration": auth_int(),
            "Snapshot_Policy_Compliance": weighted(["Compliant","Non-Compliant","Exception"], [60,28,12]),
            "Backup_Status": weighted(["Successful","Failed","Overdue"], [70,15,15]),
            "Network_Zone": random.choice(["Internal","DMZ","Restricted","Management"]),
            "Critical_Vulnerability_Count": random.randint(0, 10),
            "High_Vulnerability_Count": random.randint(0, 20),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Record_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 10. APPLICATIONS (Regulatory / PAM-integrated)
# ─────────────────────────────────────────────
def gen_applications(n=80):
    rows = []
    for i in range(n):
        ca_status = cyberark_status()
        rows.append({
            "App_ID": f"APP-{i+100:03d}",
            "App_Name": f"App-{random.choice(['Billing','HR','Payroll','Vault','SIEM','ITSM','ERP','CRM'])}-{i:02d}",
            "Business_Owner": random.choice(BUS),
            "Technical_Owner": random.choice(OWNERS),
            "Environment": random.choice(ENVS),
            "Criticality": weighted(["Critical","High","Medium","Low"], [20,35,30,15]),
            "Internet_Exposed": weighted(["Yes","No"], [30,70]),
            "Hosting_Model": random.choice(["On-Premises","IaaS","PaaS","SaaS","Hybrid"]),
            "PAM_Onboarded": ca_status,
            "Password_Mgmt": pwd_mgmt(),
            "Auth_Framework_Integration": auth_int(),
            "SSO_Enabled": weighted(["Yes","No"], [65,35]),
            "MFA_Enforced": weighted(["Yes","No","Partial"], [60,25,15]),
            "JIT_Integration": weighted(["Integrated","Partial","Not Integrated","Not Applicable"], [40,20,30,10]),
            "SAST_Status": weighted(["Covered","Partial","Not Covered"], [55,25,20]),
            "SCA_Status": weighted(["Covered","Partial","Not Covered"], [52,25,23]),
            "Hardcoded_Secret_Count": random.randint(0, 8),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Compliance_Status": comp_status(),
            "Risk_Rating": risk_level(),
            "Remediation_Owner": random.choice(OWNERS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 11. CYBERARK BREAKGLASS / ONBOARDING
# ─────────────────────────────────────────────
def gen_breakglass(n=60):
    rows = []
    for i in range(n):
        rows.append({
            "BG_ID": f"BG-{i+5000:04d}",
            "Resource_Name": f"{'Server' if random.random()>0.5 else 'Account'}-BG-{i:03d}",
            "Resource_Type": random.choice(["Server","Domain Account","Service Account","Application"]),
            "Environment": random.choice(ENVS),
            "Business_Unit": random.choice(BUS),
            "CyberArk_Onboarding_Status": weighted(["Onboarded","Not Onboarded","Pending","Exempted"], [50,28,14,8]),
            "Safe_Name": f"Safe-BG-{random.randint(1,10)}",
            "Password_Mgmt": pwd_mgmt(),
            "Last_Used_Date": past(180),
            "Last_Rotation_Date": past(90),
            "Next_Rotation_Due": future(60),
            "Dual_Control_Required": weighted(["Yes","No"], [70,30]),
            "Post_Use_Review_Status": weighted(["Completed","Pending","Overdue","Not Required"], [55,20,15,10]),
            "Auth_Framework_Integration": auth_int(),
            "Compliance_Status": comp_status(),
            "Risk_Rating": weighted(["Critical","High","Medium"], [30,45,25]),
            "Remediation_Owner": random.choice(OWNERS),
            "Regulatory_Framework": random.choice(FRAMEWORKS),
            "Last_Updated": past(30),
        })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 12. USERS CONFIG (roles / field visibility)
# ─────────────────────────────────────────────
def gen_users_config():
    users = [
        {"username":"exec_admin",   "password_hash":"exec123",   "role":"Executive",  "display_name":"Executive Leader"},
        {"username":"leader_ops",   "password_hash":"lead123",   "role":"Leadership", "display_name":"Operations Leader"},
        {"username":"ops_analyst",  "password_hash":"ops123",    "role":"Operations", "display_name":"Ops Analyst"},
        {"username":"rpt_admin",    "password_hash":"admin123",  "role":"Admin",      "display_name":"Report Administrator"},
    ]
    return pd.DataFrame(users)


# ─────────────────────────────────────────────
# 13. FIELD CONFIG (admin-configurable visibility)
# ─────────────────────────────────────────────
def gen_field_config():
    config = {
        "human_accounts": {
            "Executive":  ["Account_ID","Department","Compliance_Status","Risk_Rating","PAM_Onboarded","MFA_Status"],
            "Leadership": ["Account_ID","Account_Name","Employment_Type","Department","Compliance_Status","Risk_Rating",
                           "PAM_Onboarded","MFA_Status","Access_Review_Status","Auth_Framework_Integration"],
            "Operations": None,
            "Admin":      None,
        },
        "privileged_accounts": {
            "Executive":  ["Account_ID","Privilege_Tier","Compliance_Status","Risk_Rating","PAM_Onboarded","Rotation_Status"],
            "Leadership": ["Account_ID","Account_Name","Privilege_Tier","Privilege_Scope","Compliance_Status","Risk_Rating",
                           "PAM_Onboarded","JIT_Enabled","Session_Recording","Auth_Framework_Integration"],
            "Operations": None,
            "Admin":      None,
        },
        "service_accounts": {
            "Executive":  ["Account_ID","Account_Type","Compliance_Status","Risk_Rating","PAM_Onboarded","Rotation_Status"],
            "Leadership": ["Account_ID","Account_Name","Account_Type","Environment","Compliance_Status","Risk_Rating",
                           "PAM_Onboarded","Hardcoded_Secret_Status","Auth_Framework_Integration"],
            "Operations": None,
            "Admin":      None,
        },
        "windows_servers": {
            "Executive":  ["Asset_ID","Environment","Criticality","Compliance_Status","Risk_Rating","PAM_Onboarded"],
            "Leadership": ["Asset_ID","Asset_Name","Operating_System","Environment","Criticality","Compliance_Status",
                           "Risk_Rating","PAM_Onboarded","Patch_Compliance_Status","Auth_Framework_Integration"],
            "Operations": None,
            "Admin":      None,
        },
    }
    return config


# ─────────────────────────────────────────────
# WRITE ALL FILES
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Generating data files...")
    gen_human_accounts(200).to_csv(f"{BASE}/human_accounts.csv", index=False)
    gen_privileged_accounts(100).to_csv(f"{BASE}/privileged_accounts.csv", index=False)
    gen_service_accounts(150).to_csv(f"{BASE}/service_accounts.csv", index=False)
    gen_bot_accounts(80).to_csv(f"{BASE}/bot_accounts.csv", index=False)
    gen_ai_agents(40).to_csv(f"{BASE}/ai_agents.csv", index=False)
    gen_windows_servers(120).to_csv(f"{BASE}/windows_servers.csv", index=False)
    gen_linux_servers(100).to_csv(f"{BASE}/linux_servers.csv", index=False)
    gen_network_devices(80).to_csv(f"{BASE}/network_devices.csv", index=False)
    gen_virtual_assets(80).to_csv(f"{BASE}/virtual_assets.csv", index=False)
    gen_applications(80).to_csv(f"{BASE}/applications.csv", index=False)
    gen_breakglass(60).to_csv(f"{BASE}/breakglass.csv", index=False)
    gen_users_config().to_csv(f"{BASE}/users.csv", index=False)
    with open(f"{BASE}/field_config.json","w") as f:
        json.dump(gen_field_config(), f, indent=2)
    print(f"Done. Files written to: {BASE}")
    for fn in os.listdir(BASE):
        fp = os.path.join(BASE, fn)
        if fn.endswith(".csv"):
            df = pd.read_csv(fp)
            print(f"  {fn}: {len(df)} rows")

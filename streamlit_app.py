"""
Platform Engineering Command Center (Streamlit)
Real-time incident response, API analytics, and K8s monitoring
"""

import asyncio
import json
import time
import streamlit as st
from datetime import datetime
from metrics_generator import get_k8s_metrics, get_api_gateway_metrics, get_active_alerts, get_cluster_logs
from incident_response import IncidentResponseAgent


st.set_page_config(
    page_title="Platform Engineering Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

agent = IncidentResponseAgent()


def render_json(value: object) -> None:
    """Render JSON safely for Streamlit."""
    try:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, (dict, list)):
                    st.json(parsed)
                else:
                    st.code(value)
            except json.JSONDecodeError:
                st.code(value)
            return

        safe_value = json.loads(json.dumps(value, default=str))
        if isinstance(safe_value, (dict, list)):
            st.json(safe_value)
        else:
            st.write(safe_value)
    except Exception:
        st.write(value)

st.markdown("""
<style>
:root {
    --ink: #0b1021;
    --muted: #8fa3c2;
    --accent: #7dd3fc;
    --accent-2: #f472b6;
    --bg: radial-gradient(circle at 15% 20%, #1f2937 0%, #0b1224 28%, transparent 35%),
          radial-gradient(circle at 85% 10%, #1f1b4d 0%, #0b1224 32%, transparent 40%),
          linear-gradient(135deg, #0a0f1f 0%, #0c142d 45%, #0f172a 100%);
    --card: rgba(17, 24, 39, 0.85);
    --border: rgba(255,255,255,0.14);
    --panel: rgba(15, 23, 42, 0.9);
}
html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: #f8fafc;
}
[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
    background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(12,18,32,0.95)) !important;
}
.block-container { padding-top: 1rem; }
.stMarkdown, .stText, .stHeading, h1, h2, h3, h4, h5, h6, p, span, label { color: #f8fafc; }
.hero { padding: 12px 0 10px; }
.hero h1 { margin: 0; font-size: 2.6rem; color: #ffffff; letter-spacing: 0.3px; }
.hero p { margin: 6px 0 0; color: #cbd5e1; }
.section-card {
    background: var(--panel);
    border-radius: 16px;
    padding: 18px;
    border: 1px solid var(--border);
    box-shadow: 0 24px 55px rgba(0,0,0,0.45);
    backdrop-filter: blur(14px);
}
.metric-block {
    background: linear-gradient(135deg, rgba(124,58,237,0.85), rgba(14,165,233,0.8));
    border-radius: 14px;
    padding: 16px;
    border: 1px solid rgba(255,255,255,0.2);
    color: #f8fafc;
}
.metric-label { color: #e0f2fe; font-size: 0.95rem; }
.metric-value { font-size: 1.7rem; font-weight: 850; color: #ffffff; }

div[data-testid="stDataFrame"] table {
    background: rgba(15,23,42,0.9);
    color: #e5e7eb;
}
div[data-testid="stDataFrame"] thead tr th {
    background: rgba(59,130,246,0.25);
    color: #ffffff;
    font-weight: 700;
}
div[data-testid="stDataFrame"] tbody tr td {
    border-color: rgba(148,163,184,0.25);
}
div[data-testid="stDataFrame"] tbody tr:nth-child(odd) td {
    background: rgba(255,255,255,0.02);
}
div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
    background: rgba(255,255,255,0.06);
}

button, .stButton>button {
    background: linear-gradient(135deg, #7c3aed, #0ea5e9) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}
button:hover, .stButton>button:hover { filter: brightness(1.1); }

.stAlert, .stInfo, .stWarning, .stSuccess, .stError {
    background: rgba(15,23,42,0.85) !important;
    color: #f8fafc !important;
}
div[data-testid="stExpander"] {
    background: rgba(15,23,42,0.92) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(255,255,255,0.14) !important;
    box-shadow: 0 18px 44px rgba(0,0,0,0.45);
}
div[data-testid="stJson"] {
    background: #f8fafc !important;
    color: #111827 !important;
    border: 1px solid rgba(0,0,0,0.08) !important;
    border-radius: 10px;
    padding: 8px;
}
div[data-testid="stJson"] * {
    color: #111827 !important;
}
div[data-testid="stJson"] pre, div[data-testid="stJson"] code {
    background: transparent !important;
    color: #111827 !important;
    border: none !important;
    border-radius: 0;
}
code, pre {
    color: #111827 !important;
    background: #f8fafc !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🤖 AI-Powered Infra & API Command Center</h1><p>Live SRE view with AI-assisted triage and runbooks</p></div>', unsafe_allow_html=True)

refresh = st.sidebar.slider("Refresh interval (seconds)", 2, 15, 5)
section = st.sidebar.radio("View", ["Incident Response", "API Gateway", "K8s Cluster", "Log Aggregation"])

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = 0.0

if time.time() - st.session_state.last_refresh > refresh:
    st.session_state.last_refresh = time.time()

# Fetch data
k8s = get_k8s_metrics("all")
api = get_api_gateway_metrics("5m")
alerts = get_active_alerts("all")

# Top KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown('<div class="metric-block"><div class="metric-label">Cluster Health</div><div class="metric-value">{}%</div></div>'.format(k8s['cluster']['health_score']), unsafe_allow_html=True)
with kpi2:
    st.markdown('<div class="metric-block"><div class="metric-label">Running Pods</div><div class="metric-value">{}</div></div>'.format(k8s['cluster']['running_pods']), unsafe_allow_html=True)
with kpi3:
    st.markdown('<div class="metric-block"><div class="metric-label">API Success Rate</div><div class="metric-value">{}%</div></div>'.format(api['summary']['overall_success_rate']), unsafe_allow_html=True)
with kpi4:
    st.markdown('<div class="metric-block"><div class="metric-label">Active Alerts</div><div class="metric-value">{}</div></div>'.format(alerts['total_alerts']), unsafe_allow_html=True)

st.divider()

if section == "Incident Response":
    st.subheader("🛠 Incident Response")
    st.caption("Live alerts with AI-driven root cause analysis and runbook execution.")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    if alerts["alerts"]:
        for alert in alerts["alerts"]:
            with st.expander(f"{alert['severity'].upper()} - {alert['message']}"):
                render_json(alert)
                if st.button(f"Analyze {alert['id']}", key=f"analyze_{alert['id']}"):
                    analysis = agent.analyze_incident_sync(alert, True)
                    st.session_state.analysis = analysis
                    if analysis is None:
                        st.error("Analysis returned no data. Please try again.")
                    else:
                        render_json({
                            "root_cause": analysis.get("root_cause"),
                            "recommendations": analysis.get("recommendations"),
                            "anomaly": analysis.get("anomaly"),
                            "alert": {
                                "id": analysis.get("alert_id"),
                                "type": analysis.get("type"),
                                "severity": analysis.get("severity"),
                                "resource": analysis.get("resource"),
                                "message": analysis.get("message"),
                            }
                        })
    else:
        st.info("No active alerts right now.")
    st.markdown("</div>", unsafe_allow_html=True)

elif section == "API Gateway":
    st.subheader("📈 API Gateway Analytics")
    st.caption("Real-time traffic, latency, and error analysis.")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.write(api["summary"])
    st.dataframe(api["endpoints"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif section == "K8s Cluster":
    st.subheader("☸ K8s Cluster Monitoring")
    st.caption("Pod health, node status, and resource usage.")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.dataframe(k8s["pods"], use_container_width=True)
    st.dataframe(k8s["nodes"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

else:
    st.subheader("📜 Log Aggregation")
    st.caption("Aggregated pod logs with anomaly detection.")

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    pod_name = st.selectbox("Pod", ["all"] + sorted({p["name"] for p in k8s["pods"]}))
    logs = get_cluster_logs(pod_name, lines=100, severity="all")
    st.write({
        "anomaly_detected": logs["anomaly_detected"],
        "error_count": logs["error_count"],
        "warning_count": logs["warning_count"]
    })
    st.dataframe(logs["logs"], use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

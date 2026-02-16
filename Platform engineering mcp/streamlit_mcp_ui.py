"""
Streamlit MCP Showcase UI
Allows calling MCP tools (via the in-process mcp_client facade) to demo MCP capabilities.
"""

import json
import streamlit as st
from mcp_client import list_tools, call_tool
from metrics_generator import get_active_alerts

st.set_page_config(page_title="MCP Tooling Showcase", page_icon="🧰", layout="wide")

st.markdown("""
<style>
:root {
    --ink: #0b1021;
    --muted: #a5b4c8;
    --accent: #7dd3fc;
    --accent-2: #f472b6;
    --bg: radial-gradient(circle at 12% 18%, #1f2937 0%, #0b1224 28%, transparent 35%),
          radial-gradient(circle at 82% 12%, #1f1b4d 0%, #0b1224 32%, transparent 40%),
          linear-gradient(135deg, #0a0f1f 0%, #0c142d 45%, #0f172a 100%);
    --card: rgba(17, 24, 39, 0.88);
    --border: rgba(255,255,255,0.14);
    --panel: rgba(15, 23, 42, 0.92);
}
html, body, .stApp, [data-testid="stAppViewContainer"] { background: var(--bg) !important; color: #f8fafc; }
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { background: linear-gradient(180deg, rgba(15,23,42,0.94), rgba(12,18,32,0.96)) !important; }
.hero h1 { margin: 0; font-size: 2.3rem; color: #ffffff; letter-spacing: 0.25px; }
.hero p { margin: 6px 0 0; color: var(--muted); }
.card { background: var(--panel); border-radius: 14px; padding: 16px; box-shadow: 0 18px 44px rgba(0,0,0,0.45); border: 1px solid var(--border); backdrop-filter: blur(12px); }
.stApp { background: transparent; }
.block-container { padding-top: 1rem; }
.stMarkdown, .stText, .stHeading, h1, h2, h3, h4, h5, h6, p, span, label { color: #f8fafc; }

div[data-testid="stDataFrame"] table { background: rgba(15,23,42,0.92); color: #e5e7eb; }
div[data-testid="stDataFrame"] thead tr th { background: rgba(59,130,246,0.25); color: #ffffff; font-weight: 700; }
div[data-testid="stDataFrame"] tbody tr td { border-color: rgba(148,163,184,0.25); }
div[data-testid="stDataFrame"] tbody tr:nth-child(odd) td { background: rgba(255,255,255,0.03); }
div[data-testid="stDataFrame"] tbody tr:nth-child(even) td { background: rgba(255,255,255,0.08); }
div[data-testid="stTable"] table { background: rgba(15,23,42,0.92); color: #e5e7eb; }
div[data-testid="stTable"] thead tr th { background: rgba(59,130,246,0.28); color: #ffffff; font-weight: 700; }
div[data-testid="stTable"] tbody tr td { border-color: rgba(148,163,184,0.28); }

button, .stButton>button {
    background: linear-gradient(135deg, #7c3aed, #0ea5e9) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}
button:hover, .stButton>button:hover { filter: brightness(1.1); }
div[data-testid="stExpander"] {
    background: rgba(15,23,42,0.94) !important;
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
div[data-testid="stJson"] * { color: #111827 !important; }
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

st.markdown('<div class="hero"><h1>🧰 AI-Powered MCP Tooling</h1><p>Drive platform automation and analysis through MCP tools.</p></div>', unsafe_allow_html=True)

# Tool list
with st.expander("Available MCP Tools", expanded=True):
    st.table(list_tools())

col1, col2 = st.columns(2)

with col1:
    st.subheader("Active Alerts")
    st.caption("Pull current simulated alerts exposed via MCP tools.")
    if st.button("Fetch Active Alerts"):
        alerts = call_tool("get_active_alerts", {"severity": "all"})
        st.json(alerts)

with col2:
    st.subheader("K8s Cluster Status")
    st.caption("Cluster and pod metrics via MCP.")

    if "mcp_k8s" not in st.session_state:
        st.session_state.mcp_k8s = None

    namespace_input = st.text_input(
        "Namespace",
        value="all",
        help="Use 'all' for all namespaces, or a specific namespace name.",
    )

    if st.button("Fetch K8s Status"):
        namespace = (namespace_input or "all").strip() or "all"
        st.session_state.mcp_k8s = call_tool("get_k8s_cluster_status", {"namespace": namespace})

    k8s = st.session_state.mcp_k8s
    if k8s:
        pods = k8s.get("pods", []) or []
        namespaces = sorted({p.get("namespace", "unknown") for p in pods})

        # If the user fetched 'all', allow local filtering; otherwise we already queried a single namespace.
        if (namespace_input or "all").strip() == "all" and namespaces:
            namespace_filter = st.selectbox("Filter namespace", options=["all"] + namespaces)
        else:
            namespace_filter = (namespace_input or "all").strip() or "all"

        pods_filtered = [
            p for p in pods
            if namespace_filter == "all" or p.get("namespace") == namespace_filter
        ]

        pod_names = sorted({p.get("name", "unknown") for p in pods_filtered})
        pod_filter = st.selectbox("Filter pod", options=["all"] + pod_names)

        final_pods = [
            p for p in pods_filtered
            if pod_filter == "all" or p.get("name") == pod_filter
        ]

        st.dataframe(final_pods, use_container_width=True)

        st.caption("Pod logs via MCP (optional drill-down)")
        log_col1, log_col2, log_col3 = st.columns(3)
        with log_col1:
            log_lines = st.number_input("Lines", min_value=10, max_value=500, value=120, step=10)
        with log_col2:
            log_sev = st.selectbox("Severity", options=["all", "ERROR", "WARN", "INFO"], index=0)
        with log_col3:
            fetch_logs = st.button("Fetch Pod Logs")

        if fetch_logs:
            pod_name = pod_filter if pod_filter != "all" else "all"
            logs = call_tool(
                "get_pod_logs",
                {"pod_name": pod_name, "lines": int(log_lines), "severity": log_sev},
            )
            st.json(logs)

st.divider()

st.subheader("Analyze Incident")
st.caption("Pick an alert and run AI analysis (same as MCP tool).")
alerts = get_active_alerts("all").get("alerts", [])
alert_options = {f"{a['id']} | {a['message']}": a for a in alerts}
selected = st.selectbox("Pick an alert to analyze", options=list(alert_options.keys()) or ["No alerts"])
if selected in alert_options:
    if st.button("Run Analysis"):
        analysis = call_tool("analyze_incident", {"alert": alert_options[selected], "include_recommendations": True})
        st.json(analysis)

st.divider()

st.subheader("API Gateway Metrics")
st.caption("Traffic, error rate, latency from the simulated gateway.")
if st.button("Fetch API Metrics"):
    api = call_tool("get_api_gateway_metrics", {"time_window": "5m"})
    st.json(api)

st.subheader("Performance Bottlenecks")
st.caption("Detect bottlenecks using the MCP tool call.")
if st.button("Detect Bottlenecks"):
    bottlenecks = call_tool("get_performance_bottlenecks", {"threshold": "medium"})
    try:
        st.json(bottlenecks)
    except Exception:
        st.write(bottlenecks)


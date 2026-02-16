"""
Automation Agent
Polls alerts, runs incident analysis, and triggers runbooks.
Uses the same simulated data and incident workflow as the MCP tools.
"""

import os
import time
from typing import Dict, Set
from dotenv import load_dotenv

from mcp_client import list_tools, call_tool

load_dotenv()

POLL_INTERVAL_SECS = 5
CRITICAL_ACTIONS = {"CrashLoop", "HighErrorRate", "HighLatency", "HighResourceUsage"}


def handle_alert(alert: Dict[str, str]) -> None:
    alert_id = alert.get("id")
    print("\n=== New Alert ===")
    print(f"id={alert_id} type={alert.get('type')} severity={alert.get('severity')} resource={alert.get('resource')}")

    # Enrich with quick context
    cluster = call_tool("get_k8s_cluster_status", {"namespace": "all"})
    logs = call_tool("get_pod_logs", {"pod_name": alert.get("resource", "all"), "lines": 120, "severity": "all"})
    print(f"cluster health={cluster['cluster']['health_score']} running_pods={cluster['cluster']['running_pods']}")
    print(f"logs: errors={logs['error_count']} warnings={logs['warning_count']} anomaly={logs['anomaly_detected']}")

    # Analyze incident (sync path returns concise summary)
    analysis = call_tool("analyze_incident", {"alert": alert, "include_recommendations": True})
    print("-- Root Cause --")
    print(analysis.get("root_cause", {}))

    print("-- Recommendations --")
    for rec in analysis.get("recommendations", []):
        print(f"- {rec}")

    # Auto-runbook for critical/high cases (simulated)
    if alert.get("severity") == "critical" or alert.get("type") in CRITICAL_ACTIONS:
        runbook_id = "restart-pod"
        result = call_tool("execute_runbook", {"runbook_id": runbook_id, "parameters": {"resource": alert.get("resource")}})
        print("-- Runbook executed --")
        print(result)


def main() -> None:
    seen: Set[str] = set()
    print("Automation agent started. Polling alerts...")
    while True:
        alerts = call_tool("get_active_alerts", {"severity": "all"}).get("alerts", [])
        for alert in alerts:
            alert_id = alert.get("id")
            if alert_id and alert_id not in seen:
                seen.add(alert_id)
                handle_alert(alert)
        time.sleep(POLL_INTERVAL_SECS)


if __name__ == "__main__":
    main()

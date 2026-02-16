"""
Lightweight MCP client facade (in-process) for demo.
Mirrors the MCP tool surface exposed by mcp_server.py but calls functions directly.
"""

from typing import Any, Dict, List
from metrics_generator import (
    get_k8s_metrics,
    get_api_gateway_metrics,
    get_cluster_logs,
    get_active_alerts,
    get_pod_details,
)
from incident_response import IncidentResponseAgent
import asyncio

agent = IncidentResponseAgent()


def list_tools() -> List[Dict[str, Any]]:
    return [
        {"name": "get_k8s_cluster_status", "description": "K8s metrics"},
        {"name": "get_api_gateway_metrics", "description": "API metrics"},
        {"name": "get_pod_logs", "description": "Pod logs"},
        {"name": "get_active_alerts", "description": "Active alerts"},
        {"name": "analyze_incident", "description": "AI incident analysis"},
        {"name": "execute_runbook", "description": "Runbook action"},
        {"name": "get_performance_bottlenecks", "description": "Perf bottlenecks"},
    ]


def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_k8s_cluster_status":
        namespace = arguments.get("namespace", "all")
        return get_k8s_metrics(namespace)
    if name == "get_api_gateway_metrics":
        window = arguments.get("time_window", "5m")
        return get_api_gateway_metrics(window)
    if name == "get_pod_logs":
        pod = arguments.get("pod_name", "all")
        lines = arguments.get("lines", 100)
        severity = arguments.get("severity", "all")
        return get_cluster_logs(pod, lines, severity)
    if name == "get_active_alerts":
        sev = arguments.get("severity", "all")
        return get_active_alerts(sev)
    if name == "analyze_incident":
        alert = arguments.get("alert")
        include_recs = arguments.get("include_recommendations", True)
        return agent.analyze_incident_sync(alert, include_recs)
    if name == "execute_runbook":
        runbook_id = arguments.get("runbook_id")
        params = arguments.get("parameters", {})
        return agent.execute_runbook(runbook_id, params)
    if name == "get_performance_bottlenecks":
        # Minimal stub using last metrics: we call API metrics and pass as history
        api_metrics = get_api_gateway_metrics("5m")
        history = {"api": [{"data": api_metrics}]}
        threshold = arguments.get("threshold", "medium")
        # detect_bottlenecks is async; run it synchronously here
        return asyncio.run(agent.detect_bottlenecks(history, threshold))
    return {"error": f"Unknown tool: {name}"}

"""
Incident Response Agent
LangGraph-powered workflow for alert analysis and runbook execution
"""

import os
from typing import Dict, Any, List
from datetime import datetime
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")
os.environ.setdefault("LANGCHAIN_ENDPOINT", "")
os.environ.setdefault("LANGCHAIN_API_KEY", "")

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from metrics_generator import get_cluster_logs, get_pod_details

load_dotenv()


class IncidentState(dict):
    """State container for incident analysis."""


class IncidentResponseAgent:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.llm = None
        if api_key:
            self.llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

        self.graph = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(IncidentState)

        graph.add_node("enrich_alert", self._enrich_alert)
        graph.add_node("analyze_logs", self._analyze_logs)
        graph.add_node("diagnose_root_cause", self._diagnose_root_cause)
        graph.add_node("recommend_actions", self._recommend_actions)

        graph.set_entry_point("enrich_alert")
        graph.add_edge("enrich_alert", "analyze_logs")
        graph.add_edge("analyze_logs", "diagnose_root_cause")
        graph.add_edge("diagnose_root_cause", "recommend_actions")
        graph.add_edge("recommend_actions", END)

        return graph

    async def analyze_incident(self, alert: Dict[str, Any], include_recommendations: bool = True) -> Dict[str, Any]:
        if not alert:
            return {"error": "Missing alert payload"}
        state = IncidentState({
            "alert": alert,
            "include_recommendations": include_recommendations
        })

        result = await self.graph.ainvoke(state)
        return result

    def analyze_incident_sync(self, alert: Dict[str, Any], include_recommendations: bool = True) -> Dict[str, Any]:
        if not alert:
            return {"error": "Missing alert payload"}
        state = IncidentState({
            "alert": alert,
            "include_recommendations": include_recommendations
        })

        # Run steps synchronously to ensure UI always shows results
        try:
            state = self._enrich_alert(state)
            state = self._analyze_logs(state)
            state = self._diagnose_root_cause(state)
            state = self._recommend_actions(state)
            # Return a concise summary for UI
            alert_basic = state.get("alert", {})
            logs = state.get("logs", {})
            return {
                "alert_id": alert_basic.get("id"),
                "type": alert_basic.get("type"),
                "severity": alert_basic.get("severity"),
                "resource": alert_basic.get("resource"),
                "message": alert_basic.get("message"),
                "anomaly": logs.get("anomaly_description"),
                "root_cause": state.get("root_cause"),
                "recommendations": state.get("recommendations", []),
            }
        except Exception as exc:  # Fallback if any step fails
            state["error"] = f"Analysis failed: {exc}"
            return state

    async def execute_runbook(self, runbook_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Simulated runbook execution
        return {
            "runbook_id": runbook_id,
            "status": "completed",
            "parameters": parameters,
            "executed_at": datetime.now().isoformat(),
            "result": "Runbook executed successfully (simulated)"
        }

    async def detect_bottlenecks(self, metrics_history: Dict[str, Any], threshold: str) -> Dict[str, Any]:
        # Simulated AI analysis
        findings = []
        if metrics_history.get("api"):
            latest = metrics_history["api"][-1]["data"]
            for endpoint in latest["endpoints"]:
                if endpoint["latency_p95_ms"] > 1000:
                    findings.append({
                        "type": "api_latency",
                        "resource": endpoint["path"],
                        "severity": "high",
                        "message": f"High p95 latency: {endpoint['latency_p95_ms']}ms"
                    })

        return {
            "threshold": threshold,
            "findings": findings,
            "summary": f"Detected {len(findings)} bottlenecks"
        }

    def _enrich_alert(self, state: IncidentState) -> IncidentState:
        alert = state.get("alert")
        if not alert:
            state["error"] = "Alert is missing from state"
            return state
        resource = alert.get("resource", "unknown")
        pod_details = get_pod_details(resource)

        state["pod_details"] = pod_details
        return state

    def _analyze_logs(self, state: IncidentState) -> IncidentState:
        alert = state.get("alert")
        if not alert:
            state["error"] = "Alert is missing from state"
            return state
        pod_name = alert.get("resource", "all")
        logs = get_cluster_logs(pod_name, lines=120, severity="all")

        state["logs"] = logs
        return state

    def _diagnose_root_cause(self, state: IncidentState) -> IncidentState:
        alert = state.get("alert")
        if not alert:
            state["root_cause"] = {
                "summary": "No alert available to analyze",
                "evidence": []
            }
            return state
        logs = state.get("logs", {})
        pod_details = state.get("pod_details", {})

        if not self.llm:
            state["root_cause"] = {
                "summary": "Likely resource saturation or error spike in service",
                "evidence": [
                    f"Alert type: {alert.get('type')}",
                    f"Error count: {logs.get('error_count', 0)}",
                    f"Pod status: {pod_details.get('status', 'unknown')}"
                ]
            }
            return state

        prompt = (
            "You are a site reliability engineer. Analyze the alert and logs to find root cause.\n"
            f"Alert: {alert}\n"
            f"Pod details: {pod_details}\n"
            f"Log summary: errors={logs.get('error_count')} warnings={logs.get('warning_count')}\n"
            "Provide a concise root cause summary and evidence list."
        )
        response = self.llm.invoke(prompt)
        state["root_cause"] = {
            "summary": response.content.strip(),
            "evidence": ["AI analysis based on alert and logs"]
        }
        return state

    def _recommend_actions(self, state: IncidentState) -> IncidentState:
        if not state.get("include_recommendations"):
            state["recommendations"] = []
            return state

        root_cause = state.get("root_cause", {}).get("summary", "")

        if not self.llm:
            state["recommendations"] = [
                "Restart affected pod",
                "Check downstream dependencies",
                "Scale deployment if CPU is saturated"
            ]
            return state

        prompt = (
            "Provide 3 remediation steps for this incident.\n"
            f"Root cause: {root_cause}\n"
            "Return a bullet list."
        )
        response = self.llm.invoke(prompt)
        steps = [line.strip("- ") for line in response.content.splitlines() if line.strip()]
        state["recommendations"] = steps[:3]
        return state

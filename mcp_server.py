"""
Platform Engineering MCP Server
Exposes monitoring tools for K8s, API Gateway, and Incident Response
Powered by OpenAI and LangGraph
"""

import os
import asyncio
import json
from typing import Any, Dict, List
from datetime import datetime
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

from metrics_generator import (
    get_k8s_metrics,
    get_api_gateway_metrics,
    get_cluster_logs,
    get_active_alerts,
    get_pod_details
)
from incident_response import IncidentResponseAgent

# Load environment variables
load_dotenv()

# Initialize MCP server
app = Server("platform-engineering-server")

# Initialize incident response agent
incident_agent = IncidentResponseAgent()

# Store metrics history for trending
metrics_history = {
    "k8s": [],
    "api": [],
    "alerts": []
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available monitoring and incident response tools."""
    return [
        Tool(
            name="get_k8s_cluster_status",
            description="Get real-time Kubernetes cluster metrics including pod status, CPU, memory, and node health",
            inputSchema={
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "Kubernetes namespace to query (default: all)",
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="get_api_gateway_metrics",
            description="Get API Gateway analytics including traffic patterns, latency percentiles, error rates, and performance bottlenecks",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_window": {
                        "type": "string",
                        "description": "Time window for metrics: 1m, 5m, 15m, 1h",
                        "default": "5m"
                    }
                }
            }
        ),
        Tool(
            name="get_pod_logs",
            description="Retrieve and analyze logs from Kubernetes pods with anomaly detection",
            inputSchema={
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "Name of the pod (or 'all' for aggregated logs)"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of log lines to retrieve",
                        "default": 100
                    },
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity: ERROR, WARN, INFO",
                        "default": "all"
                    }
                },
                "required": ["pod_name"]
            }
        ),
        Tool(
            name="get_active_alerts",
            description="Get all active alerts and incidents across the platform",
            inputSchema={
                "type": "object",
                "properties": {
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity: critical, warning, info",
                        "default": "all"
                    }
                }
            }
        ),
        Tool(
            name="analyze_incident",
            description="AI-powered root cause analysis for an incident or alert using LangGraph workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "alert_id": {
                        "type": "string",
                        "description": "Alert ID to analyze"
                    },
                    "include_recommendations": {
                        "type": "boolean",
                        "description": "Include remediation recommendations",
                        "default": True
                    }
                },
                "required": ["alert_id"]
            }
        ),
        Tool(
            name="execute_runbook",
            description="Execute an automated runbook for incident remediation",
            inputSchema={
                "type": "object",
                "properties": {
                    "runbook_id": {
                        "type": "string",
                        "description": "Runbook identifier (e.g., restart-pod, scale-deployment, clear-cache)"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Runbook-specific parameters",
                        "default": {}
                    }
                },
                "required": ["runbook_id"]
            }
        ),
        Tool(
            name="get_performance_bottlenecks",
            description="Identify performance bottlenecks across API Gateway and K8s cluster using AI analysis",
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "string",
                        "description": "Severity threshold: high, medium, low",
                        "default": "medium"
                    }
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls for platform engineering operations."""
    
    try:
        if name == "get_k8s_cluster_status":
            namespace = arguments.get("namespace", "all")
            metrics = get_k8s_metrics(namespace)
            metrics_history["k8s"].append({
                "timestamp": datetime.now().isoformat(),
                "data": metrics
            })
            # Keep only last 100 entries
            if len(metrics_history["k8s"]) > 100:
                metrics_history["k8s"] = metrics_history["k8s"][-100:]
            
            return [TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        
        elif name == "get_api_gateway_metrics":
            time_window = arguments.get("time_window", "5m")
            metrics = get_api_gateway_metrics(time_window)
            metrics_history["api"].append({
                "timestamp": datetime.now().isoformat(),
                "data": metrics
            })
            if len(metrics_history["api"]) > 100:
                metrics_history["api"] = metrics_history["api"][-100:]
            
            return [TextContent(
                type="text",
                text=json.dumps(metrics, indent=2)
            )]
        
        elif name == "get_pod_logs":
            pod_name = arguments.get("pod_name")
            lines = arguments.get("lines", 100)
            severity = arguments.get("severity", "all")
            
            logs = get_cluster_logs(pod_name, lines, severity)
            
            return [TextContent(
                type="text",
                text=json.dumps(logs, indent=2)
            )]
        
        elif name == "get_active_alerts":
            severity = arguments.get("severity", "all")
            alerts = get_active_alerts(severity)
            metrics_history["alerts"].append({
                "timestamp": datetime.now().isoformat(),
                "count": len(alerts["alerts"])
            })
            
            return [TextContent(
                type="text",
                text=json.dumps(alerts, indent=2)
            )]
        
        elif name == "analyze_incident":
            alert_id = arguments.get("alert_id")
            include_recommendations = arguments.get("include_recommendations", True)
            
            # Get alert details
            alerts = get_active_alerts("all")
            alert = next((a for a in alerts["alerts"] if a["id"] == alert_id), None)
            
            if not alert:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Alert {alert_id} not found"})
                )]
            
            # Run LangGraph incident analysis
            analysis = await incident_agent.analyze_incident(
                alert,
                include_recommendations
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(analysis, indent=2)
            )]
        
        elif name == "execute_runbook":
            runbook_id = arguments.get("runbook_id")
            parameters = arguments.get("parameters", {})
            
            result = await incident_agent.execute_runbook(runbook_id, parameters)
            
            return [TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "get_performance_bottlenecks":
            threshold = arguments.get("threshold", "medium")
            
            # Analyze recent metrics for bottlenecks
            bottlenecks = await incident_agent.detect_bottlenecks(
                metrics_history,
                threshold
            )
            
            return [TextContent(
                type="text",
                text=json.dumps(bottlenecks, indent=2)
            )]
        
        else:
            return [TextContent(
                type="text",
                text=json.dumps({"error": f"Unknown tool: {name}"})
            )]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({"error": f"Tool execution failed: {str(e)}"})
        )]


async def main():
    """Run the MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    print("🚀 Platform Engineering MCP Server starting...")
    print("📊 Monitoring: K8s | API Gateway | Incident Response")
    asyncio.run(main())

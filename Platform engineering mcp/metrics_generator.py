"""
Simulated Metrics Generator
Generates realistic K8s, API Gateway, and log data for demo purposes
"""

import random
from datetime import datetime, timedelta
from typing import Dict, Any
import uuid

# Simulated pod names
POD_NAMES = [
    "api-gateway-7d9f8b-xyz12",
    "auth-service-5c8a4f-abc34",
    "payment-service-9b2e1d-def56",
    "notification-service-4a7c3e-ghi78",
    "user-service-6f1b9a-jkl90",
    "inventory-service-3d8e2c-mno12",
    "frontend-app-8c4f7b-pqr34"
]

# Simulated namespaces
NAMESPACES = [
    "production",
    "staging",
    "dev",
]

# Simulated API endpoints
API_ENDPOINTS = [
    "/api/v1/users",
    "/api/v1/products",
    "/api/v1/orders",
    "/api/v1/auth/login",
    "/api/v1/payments",
    "/api/v1/inventory",
    "/api/v1/notifications"
]

# Alert storage
ACTIVE_ALERTS = []


def _generate_pod_status() -> str:
    statuses = ["Running", "Running", "Running", "Running", "Pending", "CrashLoopBackOff"]
    return random.choice(statuses)


def _generate_cpu_usage() -> float:
    base = random.uniform(20, 60)
    spike = random.uniform(0, 40) if random.random() > 0.8 else 0
    return min(100, base + spike)


def _generate_memory_usage() -> float:
    return random.uniform(30, 85)


def get_k8s_metrics(namespace: str = "all") -> Dict[str, Any]:
    """Generate K8s cluster metrics."""
    pods = []
    total_cpu = 0.0
    total_memory = 0.0

    for idx, pod_name in enumerate(POD_NAMES):
        status = _generate_pod_status()
        cpu = _generate_cpu_usage()
        memory = _generate_memory_usage()
        restart_count = random.randint(0, 3) if status == "CrashLoopBackOff" else 0

        pod_namespace = namespace
        if namespace == "all":
            pod_namespace = NAMESPACES[idx % len(NAMESPACES)]

        pod = {
            "name": pod_name,
            "namespace": pod_namespace,
            "status": status,
            "cpu_usage_percent": round(cpu, 2),
            "memory_usage_percent": round(memory, 2),
            "restart_count": restart_count,
            "age": f"{random.randint(1, 30)}d"
        }
        pods.append(pod)

        if status == "Running":
            total_cpu += cpu
            total_memory += memory

        # Generate alert for problematic pods
        if status == "CrashLoopBackOff" or cpu > 90 or memory > 90:
            alert_type = "CrashLoop" if status == "CrashLoopBackOff" else "HighResourceUsage"
            existing_alert = next((a for a in ACTIVE_ALERTS if a["resource"] == pod_name), None)
            if not existing_alert:
                ACTIVE_ALERTS.append({
                    "id": str(uuid.uuid4())[:8],
                    "type": alert_type,
                    "severity": "critical" if status == "CrashLoopBackOff" else "warning",
                    "resource": pod_name,
                    "message": f"{alert_type} detected on {pod_name}",
                    "timestamp": datetime.now().isoformat(),
                    "status": "firing"
                })

    num_running = len([p for p in pods if p["status"] == "Running"])

    return {
        "cluster": {
            "total_pods": len(pods),
            "running_pods": num_running,
            "pending_pods": len([p for p in pods if p["status"] == "Pending"]),
            "failed_pods": len([p for p in pods if p["status"] == "CrashLoopBackOff"]),
            "avg_cpu_usage": round(total_cpu / max(num_running, 1), 2),
            "avg_memory_usage": round(total_memory / max(num_running, 1), 2),
            "health_score": round((num_running / len(pods)) * 100, 2)
        },
        "nodes": [
            {
                "name": "node-1",
                "status": "Ready",
                "cpu_capacity": "8 cores",
                "memory_capacity": "32Gi",
                "cpu_usage": round(random.uniform(40, 70), 2),
                "memory_usage": round(random.uniform(50, 80), 2)
            },
            {
                "name": "node-2",
                "status": "Ready",
                "cpu_capacity": "8 cores",
                "memory_capacity": "32Gi",
                "cpu_usage": round(random.uniform(30, 60), 2),
                "memory_usage": round(random.uniform(45, 75), 2)
            }
        ],
        "pods": pods,
        "timestamp": datetime.now().isoformat()
    }


def get_api_gateway_metrics(time_window: str = "5m") -> Dict[str, Any]:
    """Generate API Gateway metrics."""
    endpoints = []
    total_requests = 0
    total_errors = 0

    for endpoint in API_ENDPOINTS:
        requests = random.randint(100, 5000)
        error_rate = random.uniform(0.1, 5.0)
        errors = int(requests * error_rate / 100)

        # Simulate occasional bottleneck
        is_bottleneck = random.random() > 0.85
        p50_latency = random.uniform(50, 200) if not is_bottleneck else random.uniform(800, 2000)
        p95_latency = p50_latency * random.uniform(2, 4)
        p99_latency = p95_latency * random.uniform(1.5, 3)

        endpoint_data = {
            "path": endpoint,
            "requests": requests,
            "success_rate": round(100 - error_rate, 2),
            "error_rate": round(error_rate, 2),
            "latency_p50_ms": round(p50_latency, 2),
            "latency_p95_ms": round(p95_latency, 2),
            "latency_p99_ms": round(p99_latency, 2),
            "throughput_rps": round(requests / 300, 2),
            "status_codes": {
                "200": requests - errors - int(errors * 0.2),
                "400": int(errors * 0.3),
                "500": int(errors * 0.5),
                "503": int(errors * 0.2)
            }
        }
        endpoints.append(endpoint_data)

        total_requests += requests
        total_errors += errors

        # Generate alert for high latency or error rate
        if p95_latency > 1000 or error_rate > 3:
            alert_type = "HighLatency" if p95_latency > 1000 else "HighErrorRate"
            existing_alert = next((a for a in ACTIVE_ALERTS if a["resource"] == endpoint), None)
            if not existing_alert:
                ACTIVE_ALERTS.append({
                    "id": str(uuid.uuid4())[:8],
                    "type": alert_type,
                    "severity": "warning",
                    "resource": endpoint,
                    "message": (
                        f"{alert_type} on {endpoint}: {round(p95_latency, 0)}ms p95"
                        if alert_type == "HighLatency"
                        else f"Error rate {round(error_rate, 2)}%"
                    ),
                    "timestamp": datetime.now().isoformat(),
                    "status": "firing"
                })

    return {
        "summary": {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_success_rate": round((total_requests - total_errors) / total_requests * 100, 2),
            "avg_latency_ms": round(sum(e["latency_p50_ms"] for e in endpoints) / len(endpoints), 2),
            "time_window": time_window
        },
        "endpoints": endpoints,
        "timestamp": datetime.now().isoformat()
    }


def get_cluster_logs(pod_name: str, lines: int = 100, severity: str = "all") -> Dict[str, Any]:
    """Generate simulated pod logs with anomalies."""
    log_entries = []
    severities = ["INFO", "WARN", "ERROR"]

    # Generate more errors for problematic pods
    is_problematic = "crash" in pod_name.lower() or random.random() > 0.7

    for i in range(lines):
        timestamp = datetime.now() - timedelta(seconds=lines - i)

        if is_problematic and random.random() > 0.6:
            log_severity = "ERROR"
            messages = [
                "Connection refused to database",
                "OutOfMemoryError: Java heap space",
                "Timeout waiting for response",
                "Failed to authenticate request",
                "Null pointer exception in handler"
            ]
        else:
            log_severity = random.choice(severities)
            messages = [
                "Request processed successfully",
                "Cache hit for user data",
                "Database query executed in 45ms",
                "Health check passed",
                "Metrics exported to Prometheus"
            ]

        if severity != "all" and log_severity != severity:
            continue

        log_entries.append({
            "timestamp": timestamp.isoformat(),
            "severity": log_severity,
            "pod": pod_name if pod_name != "all" else random.choice(POD_NAMES),
            "message": random.choice(messages)
        })

    # Detect anomalies
    error_count = len([l for l in log_entries if l["severity"] == "ERROR"])
    anomaly_detected = error_count > lines * 0.2

    return {
        "pod": pod_name,
        "total_lines": len(log_entries),
        "error_count": error_count,
        "warning_count": len([l for l in log_entries if l["severity"] == "WARN"]),
        "anomaly_detected": anomaly_detected,
        "anomaly_description": f"High error rate: {error_count}/{lines} errors" if anomaly_detected else None,
        "logs": log_entries[-50:]
    }


def get_active_alerts(severity: str = "all") -> Dict[str, Any]:
    """Get all active alerts."""
    global ACTIVE_ALERTS
    cutoff_time = datetime.now() - timedelta(minutes=5)
    ACTIVE_ALERTS = [
        a for a in ACTIVE_ALERTS
        if datetime.fromisoformat(a["timestamp"]) > cutoff_time
    ]

    if severity != "all":
        filtered = [a for a in ACTIVE_ALERTS if a["severity"] == severity]
    else:
        filtered = ACTIVE_ALERTS

    return {
        "total_alerts": len(filtered),
        "critical": len([a for a in filtered if a["severity"] == "critical"]),
        "warning": len([a for a in filtered if a["severity"] == "warning"]),
        "info": len([a for a in filtered if a["severity"] == "info"]),
        "alerts": filtered,
        "timestamp": datetime.now().isoformat()
    }


def get_pod_details(pod_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific pod."""
    return {
        "name": pod_name,
        "namespace": "production",
        "status": _generate_pod_status(),
        "cpu_usage": round(_generate_cpu_usage(), 2),
        "memory_usage": round(_generate_memory_usage(), 2),
        "restart_count": random.randint(0, 5),
        "containers": [
            {
                "name": "main",
                "image": "myapp:v1.2.3",
                "ready": True
            }
        ],
        "events": [
            {"type": "Normal", "reason": "Started", "message": "Container started"},
            {"type": "Normal", "reason": "Pulling", "message": "Pulling image"}
        ]
    }

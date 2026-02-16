"""
Prometheus Metrics Exporter
Exposes simulated platform metrics at /metrics
"""

import time
from prometheus_client import start_http_server, Gauge
from metrics_generator import get_k8s_metrics, get_api_gateway_metrics, get_active_alerts


K8S_HEALTH_SCORE = Gauge("k8s_cluster_health_score", "K8s cluster health score")
K8S_RUNNING_PODS = Gauge("k8s_running_pods", "Number of running pods")
K8S_FAILED_PODS = Gauge("k8s_failed_pods", "Number of failed pods")

# Namespace-level metrics (for Grafana templating/drilldown)
K8S_HEALTH_SCORE_BY_NAMESPACE = Gauge(
    "k8s_cluster_health_score_by_namespace",
    "K8s namespace health score (running_pods/total_pods * 100)",
    ["namespace"],
)
K8S_RUNNING_PODS_BY_NAMESPACE = Gauge(
    "k8s_running_pods_by_namespace",
    "Number of running pods by namespace",
    ["namespace"],
)
K8S_FAILED_PODS_BY_NAMESPACE = Gauge(
    "k8s_failed_pods_by_namespace",
    "Number of failed pods (CrashLoopBackOff) by namespace",
    ["namespace"],
)

# Pod-level metrics (for Grafana templating/drilldown)
K8S_POD_INFO = Gauge(
    "k8s_pod_info",
    "Pod info (value is always 1; labels carry namespace/pod/status)",
    ["namespace", "pod", "status"],
)
K8S_POD_CPU_USAGE_PERCENT = Gauge(
    "k8s_pod_cpu_usage_percent",
    "Pod CPU usage percent",
    ["namespace", "pod"],
)
K8S_POD_MEMORY_USAGE_PERCENT = Gauge(
    "k8s_pod_memory_usage_percent",
    "Pod memory usage percent",
    ["namespace", "pod"],
)
K8S_POD_RESTART_COUNT = Gauge(
    "k8s_pod_restart_count",
    "Pod restart count",
    ["namespace", "pod"],
)
API_TOTAL_REQUESTS = Gauge("api_total_requests", "API total requests")
API_ERROR_RATE = Gauge("api_error_rate", "API error rate (%)")
API_P95_LATENCY = Gauge("api_p95_latency_ms", "API p95 latency (ms)", ["endpoint"])
ALERTS_TOTAL = Gauge("alerts_total", "Total active alerts")
ALERTS_CRITICAL = Gauge("alerts_critical", "Critical alerts")
ALERTS_WARNING = Gauge("alerts_warning", "Warning alerts")


def update_metrics() -> None:
    k8s = get_k8s_metrics("all")
    api = get_api_gateway_metrics("5m")
    alerts = get_active_alerts("all")

    # Clear labeled metrics each refresh to avoid stale labelsets
    K8S_HEALTH_SCORE_BY_NAMESPACE.clear()
    K8S_RUNNING_PODS_BY_NAMESPACE.clear()
    K8S_FAILED_PODS_BY_NAMESPACE.clear()
    K8S_POD_INFO.clear()
    K8S_POD_CPU_USAGE_PERCENT.clear()
    K8S_POD_MEMORY_USAGE_PERCENT.clear()
    K8S_POD_RESTART_COUNT.clear()

    K8S_HEALTH_SCORE.set(k8s["cluster"]["health_score"])
    K8S_RUNNING_PODS.set(k8s["cluster"]["running_pods"])
    K8S_FAILED_PODS.set(k8s["cluster"]["failed_pods"])

    # Namespace and pod level metrics
    namespace_totals: dict[str, dict[str, int]] = {}
    for pod in k8s.get("pods", []):
        pod_namespace = pod.get("namespace", "unknown")
        pod_name = pod.get("name", "unknown")
        status = pod.get("status", "Unknown")

        namespace_totals.setdefault(pod_namespace, {"total": 0, "running": 0, "failed": 0})
        namespace_totals[pod_namespace]["total"] += 1
        if status == "Running":
            namespace_totals[pod_namespace]["running"] += 1
        if status == "CrashLoopBackOff":
            namespace_totals[pod_namespace]["failed"] += 1

        K8S_POD_INFO.labels(pod_namespace, pod_name, status).set(1)
        K8S_POD_CPU_USAGE_PERCENT.labels(pod_namespace, pod_name).set(float(pod.get("cpu_usage_percent", 0)))
        K8S_POD_MEMORY_USAGE_PERCENT.labels(pod_namespace, pod_name).set(float(pod.get("memory_usage_percent", 0)))
        K8S_POD_RESTART_COUNT.labels(pod_namespace, pod_name).set(float(pod.get("restart_count", 0)))

    for pod_namespace, counts in namespace_totals.items():
        total = max(counts["total"], 1)
        running = counts["running"]
        failed = counts["failed"]
        health_score = round((running / total) * 100, 2)

        K8S_HEALTH_SCORE_BY_NAMESPACE.labels(pod_namespace).set(health_score)
        K8S_RUNNING_PODS_BY_NAMESPACE.labels(pod_namespace).set(running)
        K8S_FAILED_PODS_BY_NAMESPACE.labels(pod_namespace).set(failed)

    API_TOTAL_REQUESTS.set(api["summary"]["total_requests"])
    API_ERROR_RATE.set(100 - api["summary"]["overall_success_rate"])

    for endpoint in api["endpoints"]:
        API_P95_LATENCY.labels(endpoint["path"]).set(endpoint["latency_p95_ms"])

    ALERTS_TOTAL.set(alerts["total_alerts"])
    ALERTS_CRITICAL.set(alerts["critical"])
    ALERTS_WARNING.set(alerts["warning"])


if __name__ == "__main__":
    start_http_server(8000)
    print("📈 Metrics exporter running on http://localhost:8000/metrics")
    while True:
        update_metrics()
        time.sleep(2)

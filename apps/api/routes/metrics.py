from fastapi import APIRouter, Response
from swaram.telemetry.prometheus import METRICS, HAS_PROMETHEUS
from apps.api.routes.ws import get_active_ws_count

router = APIRouter(prefix="/metrics", tags=["Observability"])

@router.get("", summary="Scrape Prometheus Metrics")
def scrape_metrics() -> Response:
    """
    Exposes metrics in Prometheus text format.
    If prometheus_client is installed, uses its official registry generator.
    Otherwise, falls back to custom text formatting.
    """
    # Dynamically update the active WebSocket connections gauge
    METRICS.ws_connections.set(get_active_ws_count())

    if HAS_PROMETHEUS:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Fallback text representation
    lines = []
    for metric in [
        METRICS.tick_count,
        METRICS.ws_connections,
        METRICS.order_count,
        METRICS.strategy_cycles,
        METRICS.anomaly_count
    ]:
        lines.append(f"# HELP {metric.name} {metric.description}")
        lines.append(f"# TYPE {metric.name} gauge")
        for labels_str, val in metric.collect().items():
            if labels_str == "default":
                lines.append(f"{metric.name} {val}")
            else:
                formatted_labels = labels_str.replace("=", '="').replace(",", '",') + '"'
                lines.append(f"{metric.name}{{{formatted_labels}}} {val}")
    
    # Simple histogram dump
    lines.append(f"# HELP swaram_api_latency_seconds API response latency")
    lines.append(f"# TYPE swaram_api_latency_seconds summary")
    lat_data = METRICS.api_latency.collect()
    lines.append(f'swaram_api_latency_seconds{{quantile="0.99"}} {lat_data["p99"]}')
    lines.append(f'swaram_api_latency_seconds_sum {lat_data["sum"]}')
    lines.append(f'swaram_api_latency_seconds_count {lat_data["count"]}')

    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")

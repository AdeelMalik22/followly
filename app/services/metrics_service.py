from collections import deque
from threading import Lock
from time import monotonic


_lock = Lock()
_requests = 0
_errors = 0
_latencies_ms = deque(maxlen=2000)
_status_counts: dict[str, int] = {}
_route_counts: dict[str, int] = {}


def record_request(path: str, status_code: int, started_at: float) -> None:
    global _requests, _errors
    elapsed_ms = round((monotonic() - started_at) * 1000, 2)
    route = path if len(path) <= 160 else path[:160]
    with _lock:
        _requests += 1
        if status_code >= 500:
            _errors += 1
        _latencies_ms.append(elapsed_ms)
        key = str(status_code)
        _status_counts[key] = _status_counts.get(key, 0) + 1
        _route_counts[route] = _route_counts.get(route, 0) + 1


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    values.sort()
    index = min(len(values) - 1, round((len(values) - 1) * percentile))
    return round(values[index], 2)


def metrics_report() -> dict:
    with _lock:
        latencies = list(_latencies_ms)
        requests = _requests
        errors = _errors
        status_counts = dict(_status_counts)
        route_counts = dict(_route_counts)
    return {
        "requests": requests,
        "errors_5xx": errors,
        "error_rate": round(errors / requests, 4) if requests else 0.0,
        "latency_ms": {
            "p50": _percentile(latencies, 0.50),
            "p95": _percentile(latencies, 0.95),
            "p99": _percentile(latencies, 0.99),
        },
        "status_counts": status_counts,
        "top_routes": sorted(route_counts.items(), key=lambda item: item[1], reverse=True)[:20],
        "sample_size": len(latencies),
    }


def reset_metrics() -> None:
    global _requests, _errors
    with _lock:
        _requests = 0
        _errors = 0
        _latencies_ms.clear()
        _status_counts.clear()
        _route_counts.clear()

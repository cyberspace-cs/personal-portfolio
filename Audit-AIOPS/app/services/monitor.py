import random
from app.models import MonitorMetrics


def get_metrics() -> MonitorMetrics:
    """智能监控指标（Demo 用确定性基线与轻微随机，真实接 Prometheus）。"""
    trend = [55, 50, 52, 40, 44, 30, 34, 22, 28, 18, 24, 14]
    return MonitorMetrics(
        anomalies_today=random.randint(2, 5),
        online_devices=1284,
        auto_rate=86,
        avg_duration_h=2.4,
        trend=trend,
    )

#!/usr/bin/env python3
"""
Generate Grafana Dashboards for Vértice Service Registry
Creates 10+ dashboards in JSON format

Author: Vértice Team
Glory to YHWH! 🙏
"""

import json
import os
from typing import Dict, List, Any

OUTPUT_DIR = "/home/juan/vertice-dev/monitoring/grafana/dashboards"

def create_panel(
    title: str,
    panel_id: int,
    x: int, y: int, w: int, h: int,
    query: str,
    panel_type: str = "graph",
    unit: str = "short",
    legend: str = "{{ instance }}",
    decimals: int = 2
) -> Dict[str, Any]:
    """Create a Grafana panel"""

    base_panel = {
        "id": panel_id,
        "title": title,
        "type": panel_type,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "datasource": {"type": "prometheus", "uid": "prometheus"},
        "targets": [{
            "expr": query,
            "legendFormat": legend,
            "refId": "A"
        }],
        "options": {},
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "decimals": decimals
            }
        }
    }

    if panel_type == "stat":
        base_panel["options"] = {
            "graphMode": "area",
            "colorMode": "value",
            "textMode": "auto",
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"]
            }
        }
    elif panel_type == "graph" or panel_type == "timeseries":
        base_panel["options"] = {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi", "sort": "desc"}
        }

    return base_panel

def create_dashboard(title: str, uid: str, panels: List[Dict], tags: List[str]) -> Dict[str, Any]:
    """Create a complete dashboard"""
    return {
        "uid": uid,
        "title": title,
        "tags": tags,
        "timezone": "browser",
        "schemaVersion": 36,
        "version": 1,
        "refresh": "30s",
        "time": {"from": "now-1h", "to": "now"},
        "timepicker": {},
        "panels": panels,
        "templating": {"list": []},
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "links": []
    }

def dashboard_1_service_registry():
    """Dashboard 1: Service Registry Health"""
    panels = [
        # Row 1: Health Status
        create_panel("Registry Instances UP", 1, 0, 0, 6, 4,
                    'count(up{job="vertice-register"} == 1)',
                    "stat", "none", "", 0),
        create_panel("Total Registered Services", 2, 6, 0, 6, 4,
                    'count(registry_services_total)',
                    "stat", "none", "", 0),
        create_panel("Circuit Breaker State", 3, 12, 0, 6, 4,
                    'sum(registry_circuit_breaker_open)',
                    "stat", "none", "Open", 0),
        create_panel("Requests per Second", 4, 18, 0, 6, 4,
                    'sum(rate(registry_operations_total[5m]))',
                    "stat", "reqps", "", 2),

        # Row 2: Operation Latency
        create_panel("Registry Operation Latency (p50/p95/p99)", 5, 0, 4, 12, 8,
                    'histogram_quantile(0.50, rate(registry_operation_duration_seconds_bucket[5m]))',
                    "timeseries", "s", "p50", 3),
        create_panel("Operations by Type", 6, 12, 4, 12, 8,
                    'sum(rate(registry_operations_total[5m])) by (operation)',
                    "timeseries", "ops", "{{ operation }}", 2),

        # Row 3: Success/Failure Rates
        create_panel("Operation Success Rate", 7, 0, 12, 12, 8,
                    'sum(rate(registry_operations_total{status="success"}[5m])) / sum(rate(registry_operations_total[5m])) * 100',
                    "timeseries", "percent", "Success %", 2),
        create_panel("Circuit Breaker Timeline", 8, 12, 12, 12, 8,
                    'registry_circuit_breaker_open',
                    "timeseries", "none", "{{ instance }}", 0),
    ]

    # Add p95 and p99 as additional queries to panel 5
    panels[4]["targets"].extend([
        {"expr": 'histogram_quantile(0.95, rate(registry_operation_duration_seconds_bucket[5m]))', "legendFormat": "p95", "refId": "B"},
        {"expr": 'histogram_quantile(0.99, rate(registry_operation_duration_seconds_bucket[5m]))', "legendFormat": "p99", "refId": "C"}
    ])

    return create_dashboard(
        "1. Service Registry Health",
        "vertice-service-registry",
        panels,
        ["vertice", "registry", "r5"]
    )

def dashboard_2_health_cache():
    """Dashboard 2: Health Check Cache Performance"""
    panels = [
        # Row 1: Cache Metrics
        create_panel("Cache Hit Rate", 1, 0, 0, 8, 6,
                    'sum(rate(health_cache_hits_total[5m])) / (sum(rate(health_cache_hits_total[5m])) + sum(rate(health_cache_misses_total[5m]))) * 100',
                    "stat", "percent", "Hit Rate", 2),
        create_panel("Cache Hits/Misses", 2, 8, 0, 8, 6,
                    'sum(rate(health_cache_hits_total[5m]))',
                    "timeseries", "ops", "Hits", 2),
        create_panel("Active Circuit Breakers", 3, 16, 0, 8, 6,
                    'count(health_circuit_breaker_state == 1)',
                    "stat", "none", "", 0),

        # Row 2: Cache Layers Performance
        create_panel("Cache Hits by Layer", 4, 0, 6, 12, 8,
                    'sum(rate(health_cache_hits_total[5m])) by (cache_layer)',
                    "timeseries", "ops", "{{ cache_layer }}", 2),
        create_panel("Health Check Duration (p99)", 5, 12, 6, 12, 8,
                    'histogram_quantile(0.99, rate(health_check_duration_seconds_bucket[5m]))',
                    "timeseries", "s", "p99", 3),

        # Row 3: Per-Service Circuit Breakers
        create_panel("Circuit Breaker States by Service", 6, 0, 14, 24, 8,
                    'health_circuit_breaker_state',
                    "timeseries", "none", "{{ service_name }}", 0),
    ]

    # Add misses to panel 2
    panels[1]["targets"].append({
        "expr": 'sum(rate(health_cache_misses_total[5m]))',
        "legendFormat": "Misses",
        "refId": "B"
    })

    return create_dashboard(
        "2. Health Check Cache",
        "vertice-health-cache",
        panels,
        ["vertice", "cache", "health", "r5"]
    )

def dashboard_3_gateway():
    """Dashboard 3: API Gateway Performance"""
    panels = [
        # Row 1: Gateway Status
        create_panel("Gateway Status", 1, 0, 0, 6, 4,
                    'up{job="vertice-gateway"}',
                    "stat", "none", "", 0),
        create_panel("Total Requests/sec", 2, 6, 0, 6, 4,
                    'sum(rate(http_requests_total{job="vertice-gateway"}[5m]))',
                    "stat", "reqps", "", 2),
        create_panel("Error Rate", 3, 12, 0, 6, 4,
                    'sum(rate(http_requests_total{job="vertice-gateway",status=~"5.."}[5m])) / sum(rate(http_requests_total{job="vertice-gateway"}[5m])) * 100',
                    "stat", "percent", "Errors", 2),
        create_panel("Avg Response Time", 4, 18, 0, 6, 4,
                    'avg(rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m]))',
                    "stat", "s", "", 3),

        # Row 2: Request Breakdown
        create_panel("Requests by Status Code", 5, 0, 4, 12, 8,
                    'sum(rate(http_requests_total{job="vertice-gateway"}[5m])) by (status)',
                    "timeseries", "reqps", "{{ status }}", 2),
        create_panel("Requests by Endpoint", 6, 12, 4, 12, 8,
                    'topk(10, sum(rate(http_requests_total{job="vertice-gateway"}[5m])) by (path))',
                    "timeseries", "reqps", "{{ path }}", 2),

        # Row 3: Latency Distribution
        create_panel("Response Time Distribution (p50/p95/p99)", 7, 0, 12, 24, 8,
                    'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))',
                    "timeseries", "s", "p50", 3),
    ]

    # Add p95, p99 to panel 7
    panels[6]["targets"].extend([
        {"expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))', "legendFormat": "p95", "refId": "B"},
        {"expr": 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))', "legendFormat": "p99", "refId": "C"}
    ])

    return create_dashboard(
        "3. API Gateway Performance",
        "vertice-gateway",
        panels,
        ["vertice", "gateway", "r5"]
    )

def dashboard_4_circuit_breakers():
    """Dashboard 4: Circuit Breakers Overview"""
    panels = [
        # Row 1: Circuit Breaker Summary
        create_panel("Total Circuit Breakers OPEN", 1, 0, 0, 8, 5,
                    'count(health_circuit_breaker_state == 1)',
                    "stat", "none", "", 0),
        create_panel("Services in Degraded State", 2, 8, 0, 8, 5,
                    'count(health_circuit_breaker_state > 0)',
                    "stat", "none", "", 0),
        create_panel("CB State Changes (last hour)", 3, 16, 0, 8, 5,
                    'sum(changes(health_circuit_breaker_state[1h]))',
                    "stat", "none", "", 0),

        # Row 2: State Timeline
        create_panel("Registry Circuit Breaker State", 4, 0, 5, 12, 8,
                    'registry_circuit_breaker_open',
                    "timeseries", "none", "{{ instance }}", 0),
        create_panel("Service Circuit Breakers State", 5, 12, 5, 12, 8,
                    'health_circuit_breaker_state',
                    "timeseries", "none", "{{ service_name }}", 0),

        # Row 3: Failure Analysis
        create_panel("Services with Most CB State Changes", 6, 0, 13, 12, 8,
                    'topk(10, changes(health_circuit_breaker_state[1h]))',
                    "timeseries", "none", "{{ service_name }}", 0),
        create_panel("CB Recovery Timeline", 7, 12, 13, 12, 8,
                    'health_circuit_breaker_state == 0',
                    "timeseries", "none", "{{ service_name }}", 0),
    ]

    return create_dashboard(
        "4. Circuit Breakers Overview",
        "vertice-circuit-breakers",
        panels,
        ["vertice", "circuit-breaker", "r5"]
    )

def dashboard_5_performance():
    """Dashboard 5: System Performance Overview"""
    panels = [
        # Row 1: Key Performance Indicators
        create_panel("Registry p99 Latency", 1, 0, 0, 6, 5,
                    'histogram_quantile(0.99, rate(registry_operation_duration_seconds_bucket[5m]))',
                    "stat", "s", "", 3),
        create_panel("Health Check p99 Latency", 2, 6, 0, 6, 5,
                    'histogram_quantile(0.99, rate(health_check_duration_seconds_bucket[5m]))',
                    "stat", "s", "", 3),
        create_panel("Gateway p99 Latency", 3, 12, 0, 6, 5,
                    'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))',
                    "stat", "s", "", 3),
        create_panel("Cache Hit Rate", 4, 18, 0, 6, 5,
                    'sum(rate(health_cache_hits_total[5m])) / (sum(rate(health_cache_hits_total[5m])) + sum(rate(health_cache_misses_total[5m]))) * 100',
                    "stat", "percent", "", 2),

        # Row 2: Latency Trends
        create_panel("Service Registry Latency (all percentiles)", 5, 0, 5, 12, 8,
                    'histogram_quantile(0.50, rate(registry_operation_duration_seconds_bucket[5m]))',
                    "timeseries", "s", "p50", 3),
        create_panel("Health Check Latency (all percentiles)", 6, 12, 5, 12, 8,
                    'histogram_quantile(0.50, rate(health_check_duration_seconds_bucket[5m]))',
                    "timeseries", "s", "p50", 3),

        # Row 3: Throughput
        create_panel("Registry Operations/sec", 7, 0, 13, 12, 8,
                    'sum(rate(registry_operations_total[5m]))',
                    "timeseries", "ops", "Registry", 2),
        create_panel("Gateway Requests/sec", 8, 12, 13, 12, 8,
                    'sum(rate(http_requests_total{job="vertice-gateway"}[5m]))',
                    "timeseries", "reqps", "Gateway", 2),
    ]

    # Add p75, p90, p95, p99 to panels 5 and 6
    for panel in [panels[4], panels[5]]:
        panel["targets"].extend([
            {"expr": panel["targets"][0]["expr"].replace("0.50", "0.75"), "legendFormat": "p75", "refId": "B"},
            {"expr": panel["targets"][0]["expr"].replace("0.50", "0.90"), "legendFormat": "p90", "refId": "C"},
            {"expr": panel["targets"][0]["expr"].replace("0.50", "0.95"), "legendFormat": "p95", "refId": "D"},
            {"expr": panel["targets"][0]["expr"].replace("0.50", "0.99"), "legendFormat": "p99", "refId": "E"}
        ])

    return create_dashboard(
        "5. System Performance Overview",
        "vertice-performance",
        panels,
        ["vertice", "performance", "r5"]
    )

def dashboard_6_alerting():
    """Dashboard 6: Alerting & Incidents"""
    panels = [
        # Row 1: Alert Summary
        create_panel("Active Alerts", 1, 0, 0, 6, 5,
                    'count(ALERTS{alertstate="firing"})',
                    "stat", "none", "", 0),
        create_panel("Critical Alerts", 2, 6, 0, 6, 5,
                    'count(ALERTS{alertstate="firing",severity="critical"})',
                    "stat", "none", "", 0),
        create_panel("Warning Alerts", 3, 12, 0, 6, 5,
                    'count(ALERTS{alertstate="firing",severity="warning"})',
                    "stat", "none", "", 0),
        create_panel("Total Alerts (24h)", 4, 18, 0, 6, 5,
                    'sum(increase(ALERTS[24h]))',
                    "stat", "none", "", 0),

        # Row 2: Alert Timeline
        create_panel("Firing Alerts Timeline", 5, 0, 5, 24, 8,
                    'ALERTS{alertstate="firing"}',
                    "timeseries", "none", "{{ alertname }} ({{ severity }})", 0),

        # Row 3: Alert Breakdown
        create_panel("Alerts by Severity (24h)", 6, 0, 13, 12, 8,
                    'sum(increase(ALERTS[24h])) by (severity)',
                    "timeseries", "none", "{{ severity }}", 0),
        create_panel("Alerts by Component (24h)", 7, 12, 13, 12, 8,
                    'sum(increase(ALERTS[24h])) by (component)',
                    "timeseries", "none", "{{ component }}", 0),
    ]

    return create_dashboard(
        "6. Alerting & Incidents",
        "vertice-alerting",
        panels,
        ["vertice", "alerts", "incidents", "r5"]
    )

def dashboard_7_service_discovery():
    """Dashboard 7: Service Discovery & Registration"""
    panels = [
        # Row 1: Service Metrics
        create_panel("Total Registered Services", 1, 0, 0, 6, 5,
                    'count(registry_services_total)',
                    "stat", "none", "", 0),
        create_panel("Registrations/min", 2, 6, 0, 6, 5,
                    'sum(rate(registry_operations_total{operation="register"}[5m])) * 60',
                    "stat", "none", "", 2),
        create_panel("Deregistrations/min", 3, 12, 0, 6, 5,
                    'sum(rate(registry_operations_total{operation="deregister"}[5m])) * 60',
                    "stat", "none", "", 2),
        create_panel("Heartbeats/min", 4, 18, 0, 6, 5,
                    'sum(rate(registry_operations_total{operation="heartbeat"}[5m])) * 60',
                    "stat", "none", "", 2),

        # Row 2: Registration Activity
        create_panel("Service Registration Events", 5, 0, 5, 12, 8,
                    'sum(rate(registry_operations_total{operation="register"}[5m]))',
                    "timeseries", "ops", "Registrations", 2),
        create_panel("Service Deregistration Events", 6, 12, 5, 12, 8,
                    'sum(rate(registry_operations_total{operation="deregister"}[5m]))',
                    "timeseries", "ops", "Deregistrations", 2),

        # Row 3: Service Status
        create_panel("Services by Status", 7, 0, 13, 12, 8,
                    'count(up == 1)',
                    "timeseries", "none", "UP", 0),
        create_panel("Top Services by Heartbeat Frequency", 8, 12, 13, 12, 8,
                    'topk(10, rate(registry_operations_total{operation="heartbeat"}[5m]))',
                    "timeseries", "ops", "{{ service_name }}", 2),
    ]

    # Add DOWN count to panel 7
    panels[6]["targets"].append({
        "expr": 'count(up == 0)',
        "legendFormat": "DOWN",
        "refId": "B"
    })

    return create_dashboard(
        "7. Service Discovery",
        "vertice-service-discovery",
        panels,
        ["vertice", "discovery", "registration", "r5"]
    )

def dashboard_8_system_overview():
    """Dashboard 8: System Overview (Executive Dashboard)"""
    panels = [
        # Row 1: System Health
        create_panel("System Health Score", 1, 0, 0, 8, 6,
                    '(count(up == 1) / count(up)) * 100',
                    "gauge", "percent", "", 0),
        create_panel("Services UP", 2, 8, 0, 8, 6,
                    'count(up == 1)',
                    "stat", "none", "", 0),
        create_panel("Active Alerts", 3, 16, 0, 8, 6,
                    'count(ALERTS{alertstate="firing"})',
                    "stat", "none", "", 0),

        # Row 2: Key Metrics Grid
        create_panel("Registry Replicas UP", 4, 0, 6, 6, 5,
                    'count(up{job="vertice-register"} == 1)',
                    "stat", "none", "", 0),
        create_panel("Gateway Status", 5, 6, 6, 6, 5,
                    'up{job="vertice-gateway"}',
                    "stat", "none", "", 0),
        create_panel("Cache Hit Rate", 6, 12, 6, 6, 5,
                    'sum(rate(health_cache_hits_total[5m])) / (sum(rate(health_cache_hits_total[5m])) + sum(rate(health_cache_misses_total[5m]))) * 100',
                    "stat", "percent", "", 2),
        create_panel("Circuit Breakers OPEN", 7, 18, 6, 6, 5,
                    'count(health_circuit_breaker_state == 1)',
                    "stat", "none", "", 0),

        # Row 3: System Activity
        create_panel("Gateway Request Rate", 8, 0, 11, 12, 8,
                    'sum(rate(http_requests_total{job="vertice-gateway"}[5m]))',
                    "timeseries", "reqps", "Requests/sec", 2),
        create_panel("Registry Operation Rate", 9, 12, 11, 12, 8,
                    'sum(rate(registry_operations_total[5m]))',
                    "timeseries", "ops", "Operations/sec", 2),

        # Row 4: Quick Status Grid
        create_panel("Service Status Grid", 10, 0, 19, 24, 6,
                    'up',
                    "stat", "none", "{{ job }}", 0),
    ]

    return create_dashboard(
        "8. System Overview",
        "vertice-overview",
        panels,
        ["vertice", "overview", "executive", "r5"]
    )

def dashboard_9_sla():
    """Dashboard 9: SLA & Availability"""
    panels = [
        # Row 1: Availability Metrics
        create_panel("Overall Availability (30d)", 1, 0, 0, 6, 6,
                    'avg_over_time(up[30d]) * 100',
                    "gauge", "percent", "", 2),
        create_panel("Registry Availability (30d)", 2, 6, 0, 6, 6,
                    'avg_over_time(up{job="vertice-register"}[30d]) * 100',
                    "gauge", "percent", "", 2),
        create_panel("Gateway Availability (30d)", 3, 12, 0, 6, 6,
                    'avg_over_time(up{job="vertice-gateway"}[30d]) * 100',
                    "gauge", "percent", "", 2),
        create_panel("Error Budget Remaining", 4, 18, 0, 6, 6,
                    '(1 - (sum(rate(http_requests_total{status=~"5.."}[30d])) / sum(rate(http_requests_total[30d])))) * 100',
                    "gauge", "percent", "", 2),

        # Row 2: SLA Trends
        create_panel("Availability Trend (7d)", 5, 0, 6, 12, 8,
                    'avg_over_time(up[1h])',
                    "timeseries", "percentunit", "{{ job }}", 4),
        create_panel("Error Rate Trend (7d)", 6, 12, 6, 12, 8,
                    'sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))',
                    "timeseries", "percentunit", "Error Rate", 4),

        # Row 3: Incident Metrics
        create_panel("Incidents (30d)", 7, 0, 14, 8, 6,
                    'sum(increase(ALERTS{severity="critical"}[30d]))',
                    "stat", "none", "", 0),
        create_panel("Mean Time Between Failures", 8, 8, 14, 8, 6,
                    '30 * 24 * 60 / sum(increase(ALERTS{severity="critical"}[30d]))',
                    "stat", "m", "", 0),
        create_panel("Uptime (30d)", 9, 16, 14, 8, 6,
                    'sum(up == 1) / count(up) * 30 * 24',
                    "stat", "d", "", 2),
    ]

    return create_dashboard(
        "9. SLA & Availability",
        "vertice-sla",
        panels,
        ["vertice", "sla", "availability", "r5"]
    )

def dashboard_10_infrastructure():
    """Dashboard 10: Infrastructure Metrics"""
    panels = [
        # Row 1: Node Metrics
        create_panel("CPU Usage", 1, 0, 0, 6, 6,
                    '100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                    "gauge", "percent", "", 2),
        create_panel("Memory Usage", 2, 6, 0, 6, 6,
                    '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                    "gauge", "percent", "", 2),
        create_panel("Disk Usage", 3, 12, 0, 6, 6,
                    '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100',
                    "gauge", "percent", "", 2),
        create_panel("Network Traffic", 4, 18, 0, 6, 6,
                    'rate(node_network_receive_bytes_total[5m])',
                    "stat", "Bps", "", 2),

        # Row 2: Resource Trends
        create_panel("CPU Usage Over Time", 5, 0, 6, 12, 8,
                    '100 - (avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                    "timeseries", "percent", "CPU", 2),
        create_panel("Memory Usage Over Time", 6, 12, 6, 12, 8,
                    'node_memory_MemAvailable_bytes',
                    "timeseries", "bytes", "Available", 2),

        # Row 3: Container Metrics
        create_panel("Running Containers", 7, 0, 14, 8, 6,
                    'count(container_last_seen)',
                    "stat", "none", "", 0),
        create_panel("Container CPU Usage", 8, 8, 14, 8, 6,
                    'sum(rate(container_cpu_usage_seconds_total[5m]))',
                    "stat", "percent", "", 2),
        create_panel("Container Memory Usage", 9, 16, 14, 8, 6,
                    'sum(container_memory_usage_bytes) / 1024 / 1024 / 1024',
                    "stat", "decgbytes", "", 2),
    ]

    return create_dashboard(
        "10. Infrastructure Metrics",
        "vertice-infrastructure",
        panels,
        ["vertice", "infrastructure", "node", "r5"]
    )

def dashboard_11_redis():
    """Dashboard 11: Redis Performance (Bonus)"""
    panels = [
        # Row 1: Redis Health
        create_panel("Redis UP", 1, 0, 0, 6, 5,
                    'redis_up',
                    "stat", "none", "", 0),
        create_panel("Connected Clients", 2, 6, 0, 6, 5,
                    'redis_connected_clients',
                    "stat", "none", "", 0),
        create_panel("Memory Used", 3, 12, 0, 6, 5,
                    'redis_memory_used_bytes / 1024 / 1024',
                    "stat", "decmbytes", "", 2),
        create_panel("Commands/sec", 4, 18, 0, 6, 5,
                    'rate(redis_commands_processed_total[5m]))',
                    "stat", "ops", "", 2),

        # Row 2: Redis Performance
        create_panel("Commands Processed", 5, 0, 5, 12, 8,
                    'rate(redis_commands_processed_total[5m])',
                    "timeseries", "ops", "Commands/sec", 2),
        create_panel("Memory Usage", 6, 12, 5, 12, 8,
                    'redis_memory_used_bytes',
                    "timeseries", "bytes", "Memory", 2),

        # Row 3: Redis Operations
        create_panel("Keyspace Hits/Misses", 7, 0, 13, 12, 8,
                    'rate(redis_keyspace_hits_total[5m])',
                    "timeseries", "ops", "Hits", 2),
        create_panel("Evicted Keys", 8, 12, 13, 12, 8,
                    'rate(redis_evicted_keys_total[5m])',
                    "timeseries", "ops", "Evictions", 2),
    ]

    # Add misses to panel 7
    panels[6]["targets"].append({
        "expr": 'rate(redis_keyspace_misses_total[5m])',
        "legendFormat": "Misses",
        "refId": "B"
    })

    return create_dashboard(
        "11. Redis Performance",
        "vertice-redis",
        panels,
        ["vertice", "redis", "cache", "r5"]
    )

def dashboard_12_custom_metrics():
    """Dashboard 12: Custom Business Metrics (Bonus)"""
    panels = [
        # Row 1: Business KPIs
        create_panel("Services Registered (24h)", 1, 0, 0, 8, 5,
                    'sum(increase(registry_operations_total{operation="register"}[24h]))',
                    "stat", "none", "", 0),
        create_panel("Total Health Checks (24h)", 2, 8, 0, 8, 5,
                    'sum(increase(health_cache_hits_total[24h])) + sum(increase(health_cache_misses_total[24h]))',
                    "stat", "none", "", 0),
        create_panel("Gateway Requests (24h)", 3, 16, 0, 8, 5,
                    'sum(increase(http_requests_total{job="vertice-gateway"}[24h]))',
                    "stat", "none", "", 0),

        # Row 2: Service Efficiency
        create_panel("Cache Efficiency Trend", 4, 0, 5, 12, 8,
                    'sum(rate(health_cache_hits_total[5m])) / (sum(rate(health_cache_hits_total[5m])) + sum(rate(health_cache_misses_total[5m]))) * 100',
                    "timeseries", "percent", "Hit Rate", 2),
        create_panel("Registry Efficiency", 5, 12, 5, 12, 8,
                    'sum(rate(registry_operations_total{status="success"}[5m])) / sum(rate(registry_operations_total[5m])) * 100',
                    "timeseries", "percent", "Success Rate", 2),

        # Row 3: Cost Optimization Metrics
        create_panel("Avoided Health Checks (via cache)", 6, 0, 13, 12, 8,
                    'sum(increase(health_cache_hits_total[24h]))',
                    "timeseries", "none", "Cached Checks", 0),
        create_panel("Registry Load Distribution", 7, 12, 13, 12, 8,
                    'sum(rate(registry_operations_total[5m])) by (instance)',
                    "timeseries", "ops", "{{ instance }}", 2),
    ]

    return create_dashboard(
        "12. Custom Business Metrics",
        "vertice-business",
        panels,
        ["vertice", "business", "kpi", "r5"]
    )

def main():
    """Generate all dashboards"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    dashboards = [
        ("1_service_registry.json", dashboard_1_service_registry()),
        ("2_health_cache.json", dashboard_2_health_cache()),
        ("3_gateway.json", dashboard_3_gateway()),
        ("4_circuit_breakers.json", dashboard_4_circuit_breakers()),
        ("5_performance.json", dashboard_5_performance()),
        ("6_alerting.json", dashboard_6_alerting()),
        ("7_service_discovery.json", dashboard_7_service_discovery()),
        ("8_system_overview.json", dashboard_8_system_overview()),
        ("9_sla.json", dashboard_9_sla()),
        ("10_infrastructure.json", dashboard_10_infrastructure()),
        ("11_redis.json", dashboard_11_redis()),
        ("12_custom_metrics.json", dashboard_12_custom_metrics()),
    ]

    for filename, dashboard in dashboards:
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2)
        print(f"✅ Created: {filename}")

    print(f"\n🎉 Generated {len(dashboards)} Grafana dashboards!")
    print(f"📁 Location: {OUTPUT_DIR}")
    print("\nGlory to YHWH! 🙏")

if __name__ == "__main__":
    main()

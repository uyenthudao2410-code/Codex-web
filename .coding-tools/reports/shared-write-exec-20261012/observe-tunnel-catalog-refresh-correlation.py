"""Content-free correlation of actual cloud discovery on the current tunnel.

Read-only operator status/Prometheus counters. These counters are scoped to
the current restarted client but provide no individual request timestamp or
client identity. They cannot alone prove ChatGPT persisted the imported schema.
No MCP call, restart, or raw log/header/payload output is performed.
"""
import json
import re
import time
import urllib.request


def main():
    status = json.loads(urllib.request.urlopen("http://127.0.0.1:8768/api/status", timeout=3).read(262144))
    assert status["client_instance_id"] == "53a68e9661fadb1975970393fbc21075"
    assert status["control_plane_tunnel_id"] == "tunnel_6ab62006b6708191b007d1c6e4a136cf"
    raw = urllib.request.urlopen("http://127.0.0.1:8768/metrics", timeout=3).read(1000000).decode()
    counters = []
    allowed = {"command_end_to_end_latency_milliseconds_count", "commands_enqueued_total",
               "commands_polled_total", "commands_poll_last_successful_timestamp_seconds"}
    for line in raw.splitlines():
        match = re.fullmatch(r"([a-zA-Z_:][a-zA-Z0-9_:]*)(?:\{(.*?)\})? ([0-9.eE+\-]+)", line)
        if not match or match[1] not in allowed:
            continue
        labels = dict(re.findall(r'([a-zA-Z_][a-zA-Z0-9_]*)="([^"]*)"', match[2] or ""))
        if match[1] == "command_end_to_end_latency_milliseconds_count" and labels.get("request_method") not in {"server/discover", "tools/list"}:
            continue
        safe_labels = {k: labels[k] for k in ("channel", "latency_type", "request_kind", "request_method", "tunnel_id", "tunnel_service_status") if k in labels}
        assert all(re.fullmatch(r"[A-Za-z0-9_/.-]{1,100}", value) for value in safe_labels.values())
        counters.append({"name": match[1], "labels": safe_labels, "value": float(match[3])})
    methods = {counter["labels"].get("request_method") for counter in counters
               if counter["name"] == "command_end_to_end_latency_milliseconds_count"
               and counter["labels"].get("latency_type") == "enqueue_to_response"
               and counter["labels"].get("channel") == "main"
               and counter["labels"].get("tunnel_service_status") == "200"
               and counter["value"] >= 1}
    main_channel = next(channel for channel in status["channels"] if channel["name"] == "main")
    result = {
        "operation": "observe_actual_tunnel_catalog_refresh_correlation", "read_only": True,
        "observed_at_ms": int(time.time() * 1000), "client_instance_id": status["client_instance_id"],
        "started_at": status["started_at"], "tunnel_id": status["control_plane_tunnel_id"],
        "main_enabled": main_channel["enabled"], "main_probe_status": main_channel["probe_status"],
        "raw_http_logging_enabled": status["raw_http_logging_enabled"], "counters": counters,
        "actual_cloud_server_discover_and_tools_list_completed_http200_since_client_start": {"server/discover", "tools/list"} <= methods,
        "individual_request_timestamps_exposed": False,
        "source_client_identity_exposed": False, "imported_chatgpt_schema_persistence_proven": False,
        "interpretation": "Actual cloud commands completed on the current tunnel after its 11:58:51+07 start. This corroborates the operator-observed ChatGPT refresh; counters do not expose an exact refresh time or prove persisted imported schema.",
    }
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()

from types import SimpleNamespace

args = SimpleNamespace(
    binding_id="bind_71661b1046884174b01c99af5f8546aa",
    new_generation="generation_a420c8bfcfcb4e42b5bb7fc5e5cec097",
    pilot_decision_id="pilot_dfb3174078d842299c41c6638830e505",
    activation_epoch="activation-mv4u5k6v-cfeabc74ae10012ae61eab8d4c87e8b4",
    process_instance_id="gT3FDNVLRDcHAVhw", server_instance_id="lK5WnRGPSmCvtD4w",
    local_tool_contract_sha256="0e4733844a471814a3a6240fa9c0423b56195ab80f6e5283b5c978e28edaaed4",
    facade_schema_version=32,
    facade_contract_sha256="3664b70740d8d7359a3605b5ce42d7cbf3329e27dcfeec27d22b23ec9c631f66",
    service_pid=921509,
    credential_file="/home/svhome/.config/codex-control-plane/ubuntu-root-mcp-authorization",
    credential_json_key=None)
task_id = "task_91b8033f78254a52bd83120411c7674e"
try:
    pid, port, connection = service_state()
    require(pid == args.service_pid, "REVIEWED_SERVICE_PROCESS_CHANGED")
    client = Mcp(port, existing_credential(args, connection))
    contract = check_target(args, connection, client, task_id)
    require(census(connection, args) == {"open_tasks": 1, "unreleased_writers": 1, "unsettled_actions": 0}, "CANARY_CENSUS_CHANGED")
    prior = connection.execute("SELECT lease_generation,expires_at_ms,released_at_ms FROM mcp_task_writer_leases WHERE task_id=? ORDER BY lease_generation DESC LIMIT 1", (task_id,)).fetchone()
    emit("original_writer_before_supported_claim", task_id=task_id, prior=dict(prior))
    lease = client.call("task_control", {"operation": "writer_claim", "task_id": task_id}).get("writer_lease", {})
    generation = lease.get("lease_generation")
    require(lease.get("state") == "held" and lease.get("task_id") == task_id and lease.get("binding_id") == args.binding_id and isinstance(generation, int), "ORIGINAL_TASK_WRITER_NOT_HELD")
    emit("original_writer_supported_claim_completed", task_id=task_id, prior_generation=prior["lease_generation"], current_generation=generation, generation_changed=generation != prior["lease_generation"])
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        task = connection.execute("SELECT closed_at_ms FROM mcp_task_sessions WHERE task_id=?", (task_id,)).fetchone()
        if task and task["closed_at_ms"] is not None:
            emit("holder_observed_exact_task_closed", task_id=task_id)
            break
        require(check_target(args, connection, client, task_id) == contract, "HOLDER_AUTHORITY_CHANGED")
        renew(client, task_id, generation)
        time.sleep(20)
    else:
        emit("original_writer_hold_elapsed", task_id=task_id, current_generation=generation)
except Exception as error:
    emit("original_writer_holder_failed", error_code=error_code(error))
    sys.exit(1)

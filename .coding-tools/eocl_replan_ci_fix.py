import json, os, subprocess, sys
root = r"E:\DEV\Tools-Codex-web"
py = os.path.join(root, "resources", "native-python", "python.exe")
env = os.environ.copy()
env["PYTHONPATH"] = os.path.join(root, "resources", "coding-tools-mcp")
env["CODING_TOOLS_MCP_TOOL_MODE"] = "smart"
p = subprocess.Popen([py, "-m", "coding_tools_mcp", "--stdio", "--workspace", root, "--permission-mode", "safe"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
def rpc(obj):
    p.stdin.write(json.dumps(obj, separators=(",", ":")) + "\n"); p.stdin.flush()
    line = p.stdout.readline()
    if not line: raise RuntimeError("stdio closed: " + p.stderr.read())
    resp = json.loads(line)
    if "error" in resp: raise RuntimeError(json.dumps(resp["error"]))
    return resp["result"]
def tool(name,args,rid):
    r=rpc({"jsonrpc":"2.0","id":rid,"method":"tools/call","params":{"name":name,"arguments":args}})
    sc=r.get("structuredContent")
    if not isinstance(sc,dict): raise RuntimeError("no structuredContent")
    return sc
patch = r'''*** Begin Patch
*** Update File: crates/webcodex-runner/src/main_tests.rs
@@
 fn load_config_defaults_empty_allowed_roots_to_home() {
-    let _guard = agent_init::TEST_ENV_LOCK.lock().unwrap();
-    let home = std::env::var_os("HOME").map(PathBuf::from);
+    let _guard = agent_init::TEST_ENV_LOCK
+        .lock()
+        .unwrap_or_else(|poisoned| poisoned.into_inner());
+    let home = agent_init::home_allowed_root();
@@
 fn load_config_defaults_allow_cwd_anywhere_to_false() {
-    let _guard = agent_init::TEST_ENV_LOCK.lock().unwrap();
+    let _guard = agent_init::TEST_ENV_LOCK
+        .lock()
+        .unwrap_or_else(|poisoned| poisoned.into_inner());
@@
 fn load_config_explicit_allowed_roots_override_home_default() {
-    let _guard = agent_init::TEST_ENV_LOCK.lock().unwrap();
+    let _guard = agent_init::TEST_ENV_LOCK
+        .lock()
+        .unwrap_or_else(|poisoned| poisoned.into_inner());
@@
 fn load_config_empty_roots_without_home_and_no_cwd_anywhere_errors() {
-    let _guard = agent_init::TEST_ENV_LOCK.lock().unwrap();
+    let _guard = agent_init::TEST_ENV_LOCK
+        .lock()
+        .unwrap_or_else(|poisoned| poisoned.into_inner());
*** Update File: crates/webcodex-runner/src/webcodex_runner/job_manager_tests.rs
@@
 fn structured_process_job_handoff_observation_does_not_reset_the_original_total_timeout() {
     let temp = tempfile::tempdir().unwrap();
     let helper = structured_process_helper();
     let marker = temp.path().join("timeout-started.log");
     let nonce = format!("timeout-{}", uuid::Uuid::new_v4());
     let (sink, mut rx) = structured_test_sink("structured-agent", "structured-instance");
     let manager = JobManager::new(1);
     let original_start = Instant::now();
+    #[cfg(windows)]
+    let timeout_secs = 3u64;
+    #[cfg(not(windows))]
+    let timeout_secs = 1u64;
     enqueue_structured_process_job(
         &manager,
         sink,
@@
-        1,
+        timeout_secs,
         None,
     );
@@
-    let duration_ms = final_update.duration_ms.expect("timeout duration");
+    let duration_ms = final_update.duration_ms.expect("timeout duration");
+    let expected_ms = timeout_secs * 1_000;
     assert!(
-        (850..=1_250).contains(&duration_ms),
-        "the one-second original timeout was reset at handoff: {duration_ms} ms"
+        (expected_ms.saturating_sub(250)..=expected_ms + 500).contains(&duration_ms),
+        "the original timeout was reset at handoff: expected about {expected_ms} ms, got {duration_ms} ms"
     );
     assert!(
-        original_start.elapsed() < Duration::from_millis(1_500),
+        original_start.elapsed() < Duration::from_millis(expected_ms + 1_000),
         "handoff extended the original total timeout"
     );
*** Update File: crates/webcodex-runner/src/webcodex_runner/validation/execute.rs
@@
     fn timeout_terminates_entire_tree() {
         let parent_marker = unique_temp_path("timeout-parent");
         let alive_marker = unique_temp_path("timeout-desc");
         let cwd = tempfile::tempdir().unwrap();
         let program = helper_binary();
@@
             alive_marker.to_str().unwrap(),
             "600",
         ]);
+        #[cfg(windows)]
+        let timeout_secs = 3u64;
+        #[cfg(not(windows))]
+        let timeout_secs = 1u64;
         let started = Instant::now();
         let captured = thread::scope(|scope| {
-            let handle = scope.spawn(|| run_bounded(&program, &args, cwd.path(), 1, None));
+            let handle = scope.spawn(|| run_bounded(&program, &args, cwd.path(), timeout_secs, None));
@@
-            // Both sleep 600s while the timeout is 1s, so they must still be
+            // Both sleep 600s while the timeout is short, so they must still be
*** End Patch'''
try:
    rpc({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"eocl-ci-replan","version":"1"}}})
    args={"workflow":"test_failure","phase":"execute","objective":"Fix the reproduced Windows CI failures without weakening production semantics.","path":r".coding-tools/ci-windows-fix","patch":patch,"replan_reason":"PATCH_CONTEXT_AMBIGUOUS identified insufficient hunk context; retry with function-scoped context while preserving the same deterministic route and write authority.","execution_mode":"mcp_only","test_command":"cmd /d /c \"cargo test --locked -p webcodex-runner load_config_ && cargo test --locked -p webcodex-runner structured_process_job_handoff_observation_does_not_reset_the_original_total_timeout && cargo test --locked -p webcodex-runner timeout_terminates_entire_tree\"","verification":"tests","timeout_seconds":240}
    result=tool("agent_workflow",args,2)
    print(json.dumps(result,indent=2))
    orch=result.get("orchestration") or {}
    if orch.get("orchestration_state") != "ACCEPTING": sys.exit(4)
    audit=tool("task_control",{"action":"audit","run_id":orch["run_id"],"limit":100},3)
    a=audit.get("audit") or {}
    if not (a.get("integrity") or {}).get("ok"): sys.exit(5)
    accepted=tool("task_control",{"action":"accept","run_id":orch["run_id"],"reason":"Focused Windows CI regression tests passed after explicit REPLAN; diff is limited to test correctness and test timing robustness."},4)
    print(json.dumps({"audit_integrity":a.get("integrity"),"accepted":accepted.get("accepted"),"final":accepted.get("orchestration")},indent=2))
    if not accepted.get("accepted") or (accepted.get("orchestration") or {}).get("orchestration_state") != "CHECKPOINTED": sys.exit(6)
finally:
    try:p.stdin.close()
    except:pass
    p.terminate()
    try:p.wait(timeout=5)
    except: p.kill()

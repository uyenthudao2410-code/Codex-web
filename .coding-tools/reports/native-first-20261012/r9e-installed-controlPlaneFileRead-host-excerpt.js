async controlPlaneBoundedFileRead(request = {}) {
    // File content has a distinct policy and cannot inherit the compact
    // metadata bridge's admission merely because both originate at the same
    // central node/workspace binding.
    const policy = loadFileReadBridgePolicy(this.paths);
    const admitted = admitFileReadBridgeRequest(policy, request);
    if (admitted.device_id !== this.deviceIdentity.device_id) {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_DEVICE_MISMATCH',
        'control-plane file-read action targets another local device.'
      );
    }
    const workspaceRoot = resolveRegisteredWorkspaceRoot(this.paths, policy);
    resolveDirectRegisteredFile(workspaceRoot, admitted.path);
    const admission = Object.freeze({ ...admitted, workspace_root: workspaceRoot });

    const runtime = await this.orchestrator.lightweightSnapshot();
    if (!strictControlPlaneBridgeRuntime(runtime)) {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_RUNTIME_UNREADY',
        'control-plane file-read bridge requires strict current-process runtime evidence.'
      );
    }
    const identity = await this.mcpIdentityObservation();
    if (identity.mcp_ready !== true || identity.identity_current !== true) {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_IDENTITY_UNPROVEN',
        'control-plane file-read bridge requires an exact current MCP identity.'
      );
    }
    if (typeof this.orchestrator.controlPlaneBoundedFileRead !== 'function') {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_UNAVAILABLE',
        'control-plane file-read bridge is unavailable in this runtime.'
      );
    }
    const result = await this.orchestrator.controlPlaneBoundedFileRead(admission);
    const runtimeIdentity = result?.runtime_identity;
    if (!runtimeIdentity
      || runtimeIdentity.activation_epoch_id !== identity.activation_epoch_id
      || runtimeIdentity.process_instance_id !== identity.mcp_process_instance_id
      || runtimeIdentity.server_instance_id !== identity.mcp_server_instance_id
      || runtimeIdentity.tool_contract_sha256 !== identity.tool_contract_sha256) {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_IDENTITY_CHANGED',
        'control-plane file-read bridge identity changed while the action was in flight.'
      );
    }
    let normalized;
    try {
      normalized = normaliseFileReadResult(result, admission);
    } catch (error) {
      throw controlPlaneBridgeError(
        error?.code || 'CONTROL_PLANE_FILE_READ_RESULT_INVALID',
        'control-plane file-read bridge returned an invalid or sensitive result.'
      );
    }
    if (normalized.facade_contract.schema_version !== admission.facade_contract.schema_version
      || normalized.facade_contract.profile !== admission.facade_contract.profile
      || normalized.facade_contract.sha256 !== admission.facade_contract.sha256) {
      throw controlPlaneBridgeError(
        'CONTROL_PLANE_FILE_READ_CONTRACT_CHANGED',
        'control-plane file-read bridge facade contract changed while the action was in flight.'
      );
    }
    resolveDirectRegisteredFile(workspaceRoot, admitted.path);
    return normalized;
  }

async controlPlaneBoundedFileRead(admission = {}) {
    // This local method owns the Coding MCP token and connector attestation.
    // The central action supplies only an already-sealed relative path/range;
    // it never receives this token, the absolute workspace root, or raw MCP
    // response fields that are not in the bounded receipt projection.
    const actionId = String(admission.action_id || '').trim();
    const attemptId = String(admission.attempt_id || '').trim();
    const policySha256 = String(admission.policy_sha256 || '').trim().toLowerCase();
    const facadeContract = admission.facade_contract;
    const expectedWorkspace = normalizeWorkspacePath(admission.workspace_root);
    if (!/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/.test(actionId)
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{7,255}$/.test(attemptId)
      || !/^[a-f0-9]{64}$/.test(policySha256)
      || admission.tool_name !== FILE_READ_ACTION_TOOL_NAME
      || admission.operation !== 'read_file'
      || !expectedWorkspace
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/.test(String(admission.workspace_id || '').trim())
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/.test(String(admission.workspace_generation || '').trim())
      || !facadeContract
      || typeof facadeContract !== 'object'
      || Array.isArray(facadeContract)
      || Object.keys(facadeContract).sort().join(',') !== 'profile,schema_version,sha256'
      || !Number.isSafeInteger(facadeContract.schema_version)
      || facadeContract.schema_version < 1
      || typeof facadeContract.profile !== 'string'
      || !/^[A-Za-z0-9][A-Za-z0-9_.:-]{2,255}$/.test(facadeContract.profile)
      || typeof facadeContract.sha256 !== 'string'
      || !/^[a-f0-9]{64}$/.test(facadeContract.sha256)
      || typeof admission.path !== 'string'
      || !Number.isSafeInteger(admission.start_line)
      || !Number.isSafeInteger(admission.max_lines)
      || !Number.isSafeInteger(admission.max_bytes)) {
      throw Object.assign(new Error('Control-plane bounded file-read admission is invalid.'), {
        code: 'CONTROL_PLANE_FILE_READ_ADMISSION_INVALID'
      });
    }
    const settings = this.settingsStore.load();
    // Do not use settings.workspace as the authority for a remote task. The
    // current UI selection is global and can change while another task is in
    // flight. Instead, seed an opaque, action-specific MCP-2026 task context
    // with the locally resolved registered root, then reuse that same binding
    // for the read. The absolute root remains inside this local request only.
    const localTaskContextId = `cpfr_${controlPlaneBridgeDigest({
      action_id: actionId,
      attempt_id: attemptId,
      policy_sha256: policySha256,
      workspace_id: String(admission.workspace_id).trim(),
      workspace_generation: String(admission.workspace_generation).trim(),
      facade_contract: facadeContract
    }).slice(0, 56)}`;
    const token = this.secrets.get('mcpAuthToken');
    if (!token) {
      throw Object.assign(new Error('Coding Tools MCP authentication is unavailable.'), {
        code: 'MCP_AUTH_UNAVAILABLE'
      });
    }
    const health = await this.currentMcpHealth({ timeoutMs: CONTROL_PLANE_READ_ONLY_TIMEOUT_MS });
    if (!health?.ready || !health?.tool_contract?.sha256) {
      throw Object.assign(new Error('Coding Tools MCP is not ready for the control-plane file-read bridge.'), {
        code: 'CONTROL_PLANE_FILE_READ_RUNTIME_UNREADY'
      });
    }
    const attestation = this.connectorAttestationForHealth(health);
    const attestationValue = connectorAttestationHeader({
      secret: attestation.secret,
      clientId: FILE_READ_BRIDGE_CLIENT_ID,
      clientType: FILE_READ_BRIDGE_CLIENT_TYPE,
      activationEpochId: attestation.activationEpochId,
      processInstanceId: attestation.processInstanceId,
      serverInstanceId: attestation.serverInstanceId,
      contractSha256: attestation.contractSha256
    });
    const requestFingerprint = controlPlaneBridgeDigest({
      action_id: actionId,
      attempt_id: attemptId,
      policy_sha256: policySha256,
      path: admission.path,
      start_line: admission.start_line,
      max_lines: admission.max_lines,
      max_bytes: admission.max_bytes,
      facade_contract: facadeContract
    });
    const callLocalTool = (name, toolArguments, idSuffix) => new Promise((resolve, reject) => {
      const body = JSON.stringify({
        jsonrpc: '2.0',
        id: `control-plane-file-read-${idSuffix}-${requestFingerprint.slice(0, 24)}`,
        method: 'tools/call',
        params: {
          name,
          arguments: toolArguments,
          _meta: {
            'io.modelcontextprotocol/protocolVersion': '2026-07-28',
            'io.modelcontextprotocol/clientCapabilities': {},
            'io.modelcontextprotocol/clientInfo': {
              name: 'coding-tools-control-plane-file-read-bridge',
              version: '1'
            }
          }
        }
      });
      const request = http.request({
        host: '127.0.0.1',
        port: settings.mcpPort,
        path: '/mcp',
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(body),
          'MCP-Protocol-Version': '2026-07-28',
          'Mcp-Method': 'tools/call',
          'Mcp-Name': name,
          'X-Coding-Tools-Client-Id': FILE_READ_BRIDGE_CLIENT_ID,
          'X-Coding-Tools-Client-Type': FILE_READ_BRIDGE_CLIENT_TYPE,
          [CONNECTOR_ATTESTATION_HEADER]: attestationValue
        },
        timeout: CONTROL_PLANE_FILE_READ_TIMEOUT_MS
      }, (response) => {
        let responseBody = '';
        let responseBytes = 0;
        let responseTooLarge = false;
        response.setEncoding('utf8');
        response.on('data', (chunk) => {
          responseBytes += Buffer.byteLength(chunk, 'utf8');
          if (responseBytes <= MAX_FILE_READ_RESPONSE_BYTES) responseBody += chunk;
          else responseTooLarge = true;
        });
        response.on('end', () => {
          if (responseTooLarge) {
            reject(Object.assign(new Error('Coding Tools MCP file-read response exceeded its local cap.'), {
              code: 'CONTROL_PLANE_FILE_READ_RESPONSE_TOO_LARGE'
            }));
            return;
          }
          let parsed;
          try { parsed = responseBody ? JSON.parse(responseBody) : {}; }
          catch {
            reject(Object.assign(new Error('Coding Tools MCP returned invalid JSON for the file-read bridge.'), {
              code: 'CONTROL_PLANE_FILE_READ_RESPONSE_INVALID'
            }));
            return;
          }
          const structured = parsed?.result?.structuredContent || parsed?.result || null;
          const errorMessage = parsed?.error?.message
            || (parsed?.result?.isError ? structured?.error?.message || parsed?.result?.content?.[0]?.text : '');
          if (Number(response.statusCode || 0) !== 200 || errorMessage || !structured || typeof structured !== 'object') {
            reject(Object.assign(new Error(String(errorMessage || `Coding Tools MCP rejected the file-read bridge (HTTP ${response.statusCode}).`)), {
              code: 'CONTROL_PLANE_FILE_READ_MCP_REJECTED'
            }));
            return;
          }
          resolve(structured);
        });
      });
      request.on('timeout', () => request.destroy(Object.assign(
        new Error('Control-plane file-read bridge timed out.'),
        { code: 'CONTROL_PLANE_FILE_READ_TIMEOUT' }
      )));
      request.on('error', (error) => reject(Object.assign(error, {
        code: error.code || 'CONTROL_PLANE_FILE_READ_TRANSPORT_FAILED'
      })));
      request.end(body);
    });

    const bootstrapArguments = {
      task_context_id: localTaskContextId,
      path: expectedWorkspace,
      detail: 'compact',
      max_entries: 1
    };
    const readArguments = {
      task_context_id: localTaskContextId,
      path: admission.path,
      start_line: admission.start_line,
      max_lines: admission.max_lines,
      max_bytes: admission.max_bytes,
      encoding: 'utf-8'
    };
    const bootstrap = await callLocalTool(FILE_READ_ACTION_TOOL_NAME, bootstrapArguments, 'bind');
    const boundWorkspace = normalizeWorkspacePath(bootstrap.workspace);
    if (!boundWorkspace || workspaceKey(boundWorkspace) !== workspaceKey(expectedWorkspace)) {
      throw Object.assign(new Error('Coding Tools MCP did not bind the requested local workspace.'), {
        code: 'CONTROL_PLANE_FILE_READ_WORKSPACE_MISMATCH'
      });
    }
    const structured = await callLocalTool(FILE_READ_LOCAL_TOOL_NAME, readArguments, 'read');
    let projectedPath = structured.path;
    if (typeof projectedPath === 'string' && path.isAbsolute(projectedPath)) {
      // Native read_file displays paths outside its primary root as absolute,
      // even when this request is bound to another authorized workspace. Only
      // project that exact canonical registered file back to the sealed path.
      const expectedFile = resolveDirectRegisteredFile(expectedWorkspace, admission.path);
      let returnedFile;
      try { returnedFile = fs.realpathSync.native(projectedPath); }
      catch {
        throw Object.assign(new Error('Coding Tools MCP returned an unavailable file path.'), {
          code: 'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID'
        });
      }
      if (workspaceKey(projectedPath) !== workspaceKey(expectedFile)
        || workspaceKey(returnedFile) !== workspaceKey(expectedFile)) {
        throw Object.assign(new Error('Coding Tools MCP returned a different file path.'), {
          code: 'CONTROL_PLANE_FILE_READ_RESULT_FILE_INVALID'
        });
      }
      projectedPath = admission.path;
    }
    const localHandle = `cp_fr_${controlPlaneBridgeDigest({
      policy_sha256: policySha256,
      action_id: actionId,
      attempt_id: attemptId,
      process_instance_id: attestation.processInstanceId,
      server_instance_id: attestation.serverInstanceId,
      contract_sha256: attestation.contractSha256,
      path: admission.path,
      facade_contract: facadeContract
    }).slice(0, 48)}`;
    const fileProjection = {
      path: projectedPath,
      content: structured.content,
      content_sha256: typeof structured.content === 'string' ? fileContentDigest(structured.content) : '',
      encoding: structured.encoding,
      start_line: structured.start_line,
      end_line: structured.end_line,
      total_lines: structured.total_lines,
      total_bytes: structured.total_bytes,
      bytes_read: structured.bytes_read,
      truncated: structured.truncated,
      next_start_line: structured.next_start_line == null ? null : structured.next_start_line
    };
    const candidate = {
      schema_version: 1,
      operation_kind: FILE_READ_OPERATION_KIND,
      local_handle: localHandle,
      action_id: actionId,
      attempt_id: attemptId,
      file_accessed: true,
      actor: { client_id: FILE_READ_BRIDGE_CLIENT_ID, client_type: FILE_READ_BRIDGE_CLIENT_TYPE },
      policy_sha256: policySha256,
      facade_contract: {
        schema_version: facadeContract.schema_version,
        profile: facadeContract.profile,
        sha256: facadeContract.sha256
      },
      runtime_identity: {
        process_instance_id: attestation.processInstanceId,
        server_instance_id: attestation.serverInstanceId,
        activation_epoch_id: attestation.activationEpochId,
        tool_contract_sha256: attestation.contractSha256
      },
      file: fileProjection,
      response_sha256: fileReadProjectionDigest(fileProjection)
    };
    try {
      // Run content/path/identity validation before any bytes leave the local
      // MCP process boundary. In particular, detected secrets are rejected
      // without becoming a node receipt or a central payload.
      return normaliseFileReadResult(candidate, admission);
    } catch (error) {
      throw Object.assign(error, { code: error?.code || 'CONTROL_PLANE_FILE_READ_RESULT_INVALID' });
    }
  }

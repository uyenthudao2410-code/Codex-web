# Orchestration Wave 3

- Run: `72616aa5d7a3409a83098d2243f48c48`
- Wave: `da847ca77d7a4d19bc4af6e1377b3e3d`
- Objective: Implement P0 Project Finance Overview KPI coverage in the HR repository only. Fix the pfm-management -> visual model/adapter -> ExecutiveFinancialCommandCenter flow so existing authoritative PFM totals are not dropped. Preserve and surface managementRevenue, retentionReceivable, releasedRetentionReceivable, cashConversionRate, collectibleCollectionRate, overdueReceivable, dueSoonReceivable, currentlyPayable, directProjectCost, allocatedCommonCost and existing exact totals where the UI model supports them. Derive only mathematically and semantically valid executive KPIs from exact totals: revenue/contract, collected/revenue, total receivable/revenue, total receivable/contract, project-attributed cost/contract, operating profit/revenue, and unrecognized contract value. Align pfm-management with finance-read presentation where semantics are identical, while preserving source provenance/coverage/fallback behavior. Do not invent values, do not derive ambiguous indirect cost, and do not modify Prisma/DB schema or ingestion. Add focused regression tests proving PFM values no longer fall back to 'Chưa có dữ liệu' when source fields exist, and that missing/zero denominators remain safe. Keep UI changes compact and consistent with the existing Tổng quan design.
- Mode: `mcp_only`
- Base HEAD: `db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc`
- Worktree fingerprint: `083b4fd5b3aa009c536d25cef57f40cb7a3e5ff3e0b49328be88e5fbcb3f64d8`
- Contract fingerprint: ``
- Status: **accepted**

## Delegations

| ID | Owner | Requested | Resolved | Model | Effort | Status |
|---|---|---|---|---|---|---|
| - | - | - | - | - | - | - |

## State / event timeline

| Seq | Time | Event | From | To | Key evidence |
|---:|---|---|---|---|---|
| 15009 | 2026-08-17T17:43:54.920Z | wave_replanned |  | PREFLIGHT | reason=Previous P1.6 wave performed no source mutation and its proof command ran from the repository root, so Python resolved two test-module imports as errors. Replan with the correct resources/coding-tools-mcp working directory and an explicit source patch strategy; do not reuse the failed proof as implementation evidence. |
| 15010 | 2026-08-17T17:44:02.349Z | context_prepared | PREFLIGHT | PREFLIGHT |  |
| 15011 | 2026-08-17T17:44:22.697Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15012 | 2026-08-17T17:44:22.943Z | managed_process_started |  |  | owner=chatweb-hr |
| 15013 | 2026-08-17T17:44:23.431Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15014 | 2026-08-17T17:44:33.147Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15015 | 2026-08-17T17:44:33.477Z | managed_process_started |  |  | owner=chatweb-hr |
| 15016 | 2026-08-17T17:44:34.024Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15017 | 2026-08-17T17:44:55.334Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15018 | 2026-08-17T17:44:55.575Z | managed_process_started |  |  | owner=chatweb-hr |
| 15019 | 2026-08-17T17:44:55.973Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15020 | 2026-08-17T17:45:08.018Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15021 | 2026-08-17T17:45:08.250Z | managed_process_started |  |  | owner=chatweb-hr |
| 15022 | 2026-08-17T17:45:08.723Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15023 | 2026-08-17T17:45:15.170Z | managed_process_admitted |  |  | owner=default |
| 15024 | 2026-08-17T17:45:15.400Z | managed_process_started |  |  | owner=default |
| 15025 | 2026-08-17T17:45:15.864Z | managed_process_terminal |  |  | owner=default |
| 15026 | 2026-08-17T17:45:21.223Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15027 | 2026-08-17T17:45:21.492Z | managed_process_started |  |  | owner=chatweb-hr |
| 15028 | 2026-08-17T17:45:21.972Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15029 | 2026-08-17T17:46:02.413Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15030 | 2026-08-17T17:46:02.650Z | managed_process_started |  |  | owner=chatweb-hr |
| 15031 | 2026-08-17T17:46:03.054Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15032 | 2026-08-17T17:46:10.830Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15033 | 2026-08-17T17:46:11.057Z | managed_process_started |  |  | owner=chatweb-hr |
| 15034 | 2026-08-17T17:46:11.447Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15035 | 2026-08-17T17:46:18.926Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15036 | 2026-08-17T17:46:19.140Z | managed_process_started |  |  | owner=chatweb-hr |
| 15037 | 2026-08-17T17:46:19.563Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15038 | 2026-08-17T17:46:26.754Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15039 | 2026-08-17T17:46:26.957Z | managed_process_started |  |  | owner=chatweb-hr |
| 15040 | 2026-08-17T17:46:27.329Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15041 | 2026-08-17T17:46:43.929Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15042 | 2026-08-17T17:46:44.190Z | managed_process_started |  |  | owner=chatweb-hr |
| 15043 | 2026-08-17T17:46:44.570Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15044 | 2026-08-17T17:46:46.582Z | readiness_checked | PREFLIGHT | PREFLIGHT |  |
| 15045 | 2026-08-17T17:46:46.718Z | state_transition | PREFLIGHT | READY | reason=preflight_ready |
| 15046 | 2026-08-17T17:46:46.837Z | route_selected | READY | READY | reason=caller_supplied_change_set; requested=deterministic; resolved=deterministic |
| 15047 | 2026-08-17T17:46:46.954Z | state_transition | READY | ROUTED | reason=route_selected |
| 15048 | 2026-08-17T17:46:47.598Z | write_lease_acquired | ROUTED | ROUTED | owner=MCP; lease_id=67662fa03457497a8fce5b39ff38846c |
| 15049 | 2026-08-17T17:46:47.729Z | state_transition | ROUTED | EXECUTING | reason=write_authority_acquired |
| 15050 | 2026-08-17T17:46:48.540Z | write_lease_revoked | EXECUTING | EXECUTING | reason=execution_complete; owner=MCP; lease_id=67662fa03457497a8fce5b39ff38846c |
| 15051 | 2026-08-17T17:46:48.663Z | state_transition | EXECUTING | PROVING | reason=execution_complete |
| 15052 | 2026-08-17T17:46:49.212Z | proof_cache_miss |  |  | reason=input_fingerprint_changed; stage_id=verify:tests; input_fingerprint=f60df6993555d80b9b76b9b748ecf110ae0fdb21fa5099f5f0d5a70c6db92ab8 |
| 15053 | 2026-08-17T17:46:49.487Z | managed_process_admitted |  |  | owner=default |
| 15054 | 2026-08-17T17:46:49.732Z | managed_process_started |  |  | owner=default |
| 15055 | 2026-08-17T17:46:58.029Z | managed_process_terminal |  |  | owner=default |
| 15056 | 2026-08-17T17:47:06.362Z | proof_recorded |  |  | stage_id=verify:tests; status=passed; cache_hit=False; input_fingerprint=f60df6993555d80b9b76b9b748ecf110ae0fdb21fa5099f5f0d5a70c6db92ab8 |
| 15057 | 2026-08-17T17:47:07.253Z | state_transition | PROVING | ACCEPTING | reason=required_proof_green |
| 15058 | 2026-08-17T17:47:10.995Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15059 | 2026-08-17T17:47:11.216Z | managed_process_started |  |  | owner=chatweb-hr |
| 15060 | 2026-08-17T17:47:11.662Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15061 | 2026-08-17T17:47:30.240Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15062 | 2026-08-17T17:47:30.487Z | managed_process_started |  |  | owner=chatweb-hr |
| 15063 | 2026-08-17T17:47:30.895Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15064 | 2026-08-17T17:48:26.069Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15065 | 2026-08-17T17:48:26.275Z | managed_process_started |  |  | owner=chatweb-hr |
| 15066 | 2026-08-17T17:48:27.168Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15067 | 2026-08-17T17:48:38.988Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15068 | 2026-08-17T17:48:39.181Z | managed_process_started |  |  | owner=chatweb-hr |
| 15069 | 2026-08-17T17:48:39.677Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15070 | 2026-08-17T17:48:51.439Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15071 | 2026-08-17T17:48:51.689Z | managed_process_started |  |  | owner=chatweb-hr |
| 15072 | 2026-08-17T17:48:52.127Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15073 | 2026-08-17T17:49:00.963Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15074 | 2026-08-17T17:49:01.222Z | managed_process_started |  |  | owner=chatweb-hr |
| 15075 | 2026-08-17T17:49:01.726Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15076 | 2026-08-17T17:49:12.309Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15077 | 2026-08-17T17:49:12.559Z | managed_process_started |  |  | owner=chatweb-hr |
| 15078 | 2026-08-17T17:49:13.035Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15079 | 2026-08-17T17:49:18.935Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15080 | 2026-08-17T17:49:19.184Z | managed_process_started |  |  | owner=chatweb-hr |
| 15081 | 2026-08-17T17:49:19.642Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15082 | 2026-08-17T17:49:27.455Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15083 | 2026-08-17T17:49:27.822Z | managed_process_started |  |  | owner=chatweb-hr |
| 15084 | 2026-08-17T17:49:28.418Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15085 | 2026-08-17T17:49:35.563Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15086 | 2026-08-17T17:49:35.851Z | managed_process_started |  |  | owner=chatweb-hr |
| 15087 | 2026-08-17T17:49:36.384Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15088 | 2026-08-17T17:49:45.700Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15089 | 2026-08-17T17:49:46.034Z | managed_process_started |  |  | owner=chatweb-hr |
| 15090 | 2026-08-17T17:49:46.570Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15091 | 2026-08-17T17:49:56.946Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15092 | 2026-08-17T17:49:57.237Z | managed_process_started |  |  | owner=chatweb-hr |
| 15093 | 2026-08-17T17:49:57.718Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15094 | 2026-08-17T17:50:04.421Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15095 | 2026-08-17T17:50:04.779Z | managed_process_started |  |  | owner=chatweb-hr |
| 15096 | 2026-08-17T17:50:05.241Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15097 | 2026-08-17T17:50:13.262Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15098 | 2026-08-17T17:50:13.586Z | managed_process_started |  |  | owner=chatweb-hr |
| 15099 | 2026-08-17T17:50:14.067Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15100 | 2026-08-17T17:50:39.185Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15101 | 2026-08-17T17:50:39.420Z | managed_process_started |  |  | owner=chatweb-hr |
| 15102 | 2026-08-17T17:50:39.853Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15103 | 2026-08-17T17:51:01.804Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15104 | 2026-08-17T17:51:02.035Z | managed_process_started |  |  | owner=chatweb-hr |
| 15105 | 2026-08-17T17:51:02.457Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15106 | 2026-08-17T17:51:16.319Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15107 | 2026-08-17T17:51:16.587Z | managed_process_started |  |  | owner=chatweb-hr |
| 15108 | 2026-08-17T17:51:17.116Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15109 | 2026-08-17T17:51:25.049Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15110 | 2026-08-17T17:51:25.286Z | managed_process_started |  |  | owner=chatweb-hr |
| 15111 | 2026-08-17T17:51:25.724Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15112 | 2026-08-17T17:51:42.432Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15113 | 2026-08-17T17:51:42.662Z | managed_process_started |  |  | owner=chatweb-hr |
| 15114 | 2026-08-17T17:51:43.074Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15115 | 2026-08-17T17:51:51.670Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15116 | 2026-08-17T17:51:51.936Z | managed_process_started |  |  | owner=chatweb-hr |
| 15117 | 2026-08-17T17:51:52.415Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15118 | 2026-08-17T17:52:00.048Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15119 | 2026-08-17T17:52:00.303Z | managed_process_started |  |  | owner=chatweb-hr |
| 15120 | 2026-08-17T17:52:00.732Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15121 | 2026-08-17T17:52:15.873Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15122 | 2026-08-17T17:52:16.073Z | managed_process_started |  |  | owner=chatweb-hr |
| 15123 | 2026-08-17T17:52:16.456Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15124 | 2026-08-17T17:52:28.551Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15125 | 2026-08-17T17:52:28.802Z | managed_process_started |  |  | owner=chatweb-hr |
| 15126 | 2026-08-17T17:52:29.373Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15127 | 2026-08-17T17:52:37.817Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15128 | 2026-08-17T17:52:38.061Z | managed_process_started |  |  | owner=chatweb-hr |
| 15129 | 2026-08-17T17:52:38.506Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15131 | 2026-08-17T17:52:48.934Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15132 | 2026-08-17T17:52:49.167Z | managed_process_started |  |  | owner=chatweb-hr |
| 15133 | 2026-08-17T17:52:49.684Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15134 | 2026-08-17T17:52:56.477Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15135 | 2026-08-17T17:52:56.722Z | managed_process_started |  |  | owner=chatweb-hr |
| 15136 | 2026-08-17T17:52:57.075Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15137 | 2026-08-17T17:53:07.236Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15138 | 2026-08-17T17:53:07.475Z | managed_process_started |  |  | owner=chatweb-hr |
| 15139 | 2026-08-17T17:53:07.992Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15140 | 2026-08-17T17:53:16.308Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15141 | 2026-08-17T17:53:16.533Z | managed_process_started |  |  | owner=chatweb-hr |
| 15142 | 2026-08-17T17:53:16.967Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15143 | 2026-08-17T17:53:25.555Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15144 | 2026-08-17T17:53:25.791Z | managed_process_started |  |  | owner=chatweb-hr |
| 15145 | 2026-08-17T17:53:26.297Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15146 | 2026-08-17T17:53:37.049Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15147 | 2026-08-17T17:53:37.325Z | managed_process_started |  |  | owner=chatweb-hr |
| 15148 | 2026-08-17T17:53:37.741Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15149 | 2026-08-17T17:53:48.716Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15150 | 2026-08-17T17:53:48.957Z | managed_process_started |  |  | owner=chatweb-hr |
| 15151 | 2026-08-17T17:53:49.421Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15152 | 2026-08-17T17:54:02.890Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15153 | 2026-08-17T17:54:03.166Z | managed_process_started |  |  | owner=chatweb-hr |
| 15154 | 2026-08-17T17:54:03.621Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15155 | 2026-08-17T17:54:11.491Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15156 | 2026-08-17T17:54:11.757Z | managed_process_started |  |  | owner=chatweb-hr |
| 15157 | 2026-08-17T17:54:12.166Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15158 | 2026-08-17T17:54:23.210Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15159 | 2026-08-17T17:54:23.454Z | managed_process_started |  |  | owner=chatweb-hr |
| 15160 | 2026-08-17T17:54:23.874Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15161 | 2026-08-17T17:54:32.556Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15162 | 2026-08-17T17:54:32.815Z | managed_process_started |  |  | owner=chatweb-hr |
| 15163 | 2026-08-17T17:54:33.315Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15164 | 2026-08-17T17:54:43.323Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15165 | 2026-08-17T17:54:43.556Z | managed_process_started |  |  | owner=chatweb-hr |
| 15166 | 2026-08-17T17:54:44.012Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15167 | 2026-08-17T17:54:53.100Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15168 | 2026-08-17T17:54:53.357Z | managed_process_started |  |  | owner=chatweb-hr |
| 15169 | 2026-08-17T17:54:53.798Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15170 | 2026-08-17T17:54:59.794Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15171 | 2026-08-17T17:55:00.039Z | managed_process_started |  |  | owner=chatweb-hr |
| 15172 | 2026-08-17T17:55:00.598Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15173 | 2026-08-17T17:55:09.772Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15174 | 2026-08-17T17:55:09.998Z | managed_process_started |  |  | owner=chatweb-hr |
| 15175 | 2026-08-17T17:55:10.436Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15176 | 2026-08-17T17:55:18.315Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15177 | 2026-08-17T17:55:18.564Z | managed_process_started |  |  | owner=chatweb-hr |
| 15178 | 2026-08-17T17:55:18.948Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15179 | 2026-08-17T17:55:34.205Z | managed_process_admitted |  |  | owner=chatweb-p16-accept |
| 15180 | 2026-08-17T17:55:34.464Z | managed_process_started |  |  | owner=chatweb-p16-accept |
| 15181 | 2026-08-17T17:55:35.014Z | managed_process_terminal |  |  | owner=chatweb-p16-accept |
| 15182 | 2026-08-17T17:55:38.589Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15183 | 2026-08-17T17:55:38.864Z | managed_process_started |  |  | owner=chatweb-hr |
| 15184 | 2026-08-17T17:55:39.281Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15185 | 2026-08-17T17:55:47.789Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15186 | 2026-08-17T17:55:48.024Z | managed_process_started |  |  | owner=chatweb-hr |
| 15187 | 2026-08-17T17:55:48.568Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15188 | 2026-08-17T17:55:59.510Z | managed_process_admitted |  |  | owner=chatweb-p16-accept |
| 15189 | 2026-08-17T17:55:59.701Z | managed_process_started |  |  | owner=chatweb-p16-accept |
| 15190 | 2026-08-17T17:56:00.826Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15191 | 2026-08-17T17:56:01.090Z | managed_process_started |  |  | owner=chatweb-hr |
| 15192 | 2026-08-17T17:56:01.526Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15193 | 2026-08-17T17:56:07.138Z | managed_process_terminal |  |  | owner=chatweb-p16-accept |
| 15194 | 2026-08-17T17:56:12.338Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15195 | 2026-08-17T17:56:12.574Z | managed_process_started |  |  | owner=chatweb-hr |
| 15196 | 2026-08-17T17:56:12.996Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15197 | 2026-08-17T17:56:22.891Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15198 | 2026-08-17T17:56:23.115Z | managed_process_started |  |  | owner=chatweb-hr |
| 15199 | 2026-08-17T17:56:23.584Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15200 | 2026-08-17T17:56:32.063Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15201 | 2026-08-17T17:56:32.240Z | managed_process_started |  |  | owner=chatweb-hr |
| 15202 | 2026-08-17T17:56:32.618Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15203 | 2026-08-17T17:56:39.742Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15204 | 2026-08-17T17:56:39.976Z | managed_process_started |  |  | owner=chatweb-hr |
| 15205 | 2026-08-17T17:56:40.376Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15206 | 2026-08-17T17:56:57.860Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15207 | 2026-08-17T17:56:58.072Z | managed_process_started |  |  | owner=chatweb-hr |
| 15208 | 2026-08-17T17:56:58.543Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15209 | 2026-08-17T17:57:10.767Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15210 | 2026-08-17T17:57:11.001Z | managed_process_started |  |  | owner=chatweb-hr |
| 15211 | 2026-08-17T17:57:11.467Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15212 | 2026-08-17T17:57:27.231Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15213 | 2026-08-17T17:57:27.455Z | managed_process_started |  |  | owner=chatweb-hr |
| 15214 | 2026-08-17T17:57:27.858Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15215 | 2026-08-17T17:57:29.775Z | managed_process_admitted |  |  | owner=chatweb-p16-accept |
| 15216 | 2026-08-17T17:57:29.989Z | managed_process_started |  |  | owner=chatweb-p16-accept |
| 15217 | 2026-08-17T17:57:30.420Z | managed_process_terminal |  |  | owner=chatweb-p16-accept |
| 15218 | 2026-08-17T17:57:34.971Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15219 | 2026-08-17T17:57:35.189Z | managed_process_started |  |  | owner=chatweb-hr |
| 15220 | 2026-08-17T17:57:35.600Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15221 | 2026-08-17T17:57:50.476Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15222 | 2026-08-17T17:57:50.739Z | managed_process_started |  |  | owner=chatweb-hr |
| 15223 | 2026-08-17T17:57:51.333Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15224 | 2026-08-17T17:58:02.939Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15225 | 2026-08-17T17:58:03.578Z | managed_process_started |  |  | owner=chatweb-hr |
| 15226 | 2026-08-17T17:58:04.402Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15227 | 2026-08-17T17:58:11.691Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15228 | 2026-08-17T17:58:11.958Z | managed_process_started |  |  | owner=chatweb-hr |
| 15229 | 2026-08-17T17:58:12.405Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15230 | 2026-08-17T17:58:19.080Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15231 | 2026-08-17T17:58:19.313Z | managed_process_started |  |  | owner=chatweb-hr |
| 15232 | 2026-08-17T17:58:19.755Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15233 | 2026-08-17T17:58:29.240Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15234 | 2026-08-17T17:58:29.454Z | managed_process_started |  |  | owner=chatweb-hr |
| 15235 | 2026-08-17T17:58:29.882Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15236 | 2026-08-17T17:58:32.134Z | managed_process_admitted |  |  | owner=chatweb-p16-accept |
| 15237 | 2026-08-17T17:58:32.329Z | managed_process_started |  |  | owner=chatweb-p16-accept |
| 15238 | 2026-08-17T17:58:32.707Z | managed_process_terminal |  |  | owner=chatweb-p16-accept |
| 15239 | 2026-08-17T17:58:37.898Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15240 | 2026-08-17T17:58:38.104Z | managed_process_started |  |  | owner=chatweb-hr |
| 15241 | 2026-08-17T17:58:38.649Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15242 | 2026-08-17T17:58:48.223Z | managed_process_admitted |  |  | owner=chatweb-p16-accept |
| 15243 | 2026-08-17T17:58:48.599Z | managed_process_started |  |  | owner=chatweb-p16-accept |
| 15244 | 2026-08-17T17:58:49.365Z | managed_process_terminal |  |  | owner=chatweb-p16-accept |
| 15245 | 2026-08-17T17:58:51.823Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15246 | 2026-08-17T17:58:52.233Z | managed_process_started |  |  | owner=chatweb-hr |
| 15247 | 2026-08-17T17:58:53.169Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15248 | 2026-08-17T17:59:01.198Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15249 | 2026-08-17T17:59:01.422Z | managed_process_started |  |  | owner=chatweb-hr |
| 15250 | 2026-08-17T17:59:01.841Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15251 | 2026-08-17T17:59:08.965Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15252 | 2026-08-17T17:59:09.205Z | managed_process_started |  |  | owner=chatweb-hr |
| 15253 | 2026-08-17T18:00:04.267Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15254 | 2026-08-17T18:00:22.628Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15255 | 2026-08-17T18:00:22.854Z | managed_process_started |  |  | owner=chatweb-hr |
| 15256 | 2026-08-17T18:00:23.280Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15257 | 2026-08-17T18:00:47.446Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15258 | 2026-08-17T18:00:47.670Z | managed_process_started |  |  | owner=chatweb-hr |
| 15259 | 2026-08-17T18:00:48.229Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15260 | 2026-08-17T18:01:02.730Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15261 | 2026-08-17T18:01:02.921Z | managed_process_started |  |  | owner=chatweb-hr |
| 15262 | 2026-08-17T18:01:03.320Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15263 | 2026-08-17T18:01:11.320Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15264 | 2026-08-17T18:01:11.537Z | managed_process_started |  |  | owner=chatweb-hr |
| 15265 | 2026-08-17T18:01:12.019Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15266 | 2026-08-17T18:01:19.171Z | managed_process_admitted |  |  | owner=chatweb-p16 |
| 15267 | 2026-08-17T18:01:19.386Z | managed_process_started |  |  | owner=chatweb-p16 |
| 15268 | 2026-08-17T18:01:19.804Z | managed_process_terminal |  |  | owner=chatweb-p16 |
| 15269 | 2026-08-17T18:01:26.995Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15270 | 2026-08-17T18:01:27.195Z | managed_process_started |  |  | owner=chatweb-hr |
| 15271 | 2026-08-17T18:01:27.628Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15272 | 2026-08-17T18:01:40.878Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15273 | 2026-08-17T18:01:41.095Z | managed_process_started |  |  | owner=chatweb-hr |
| 15274 | 2026-08-17T18:01:41.511Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15275 | 2026-08-17T18:01:49.170Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15276 | 2026-08-17T18:01:49.419Z | managed_process_started |  |  | owner=chatweb-hr |
| 15277 | 2026-08-17T18:01:49.848Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15278 | 2026-08-17T18:01:58.678Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15279 | 2026-08-17T18:01:58.924Z | managed_process_started |  |  | owner=chatweb-hr |
| 15280 | 2026-08-17T18:01:59.353Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15281 | 2026-08-17T18:02:10.387Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15282 | 2026-08-17T18:02:10.611Z | managed_process_started |  |  | owner=chatweb-hr |
| 15283 | 2026-08-17T18:02:11.011Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15284 | 2026-08-17T18:02:19.262Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15285 | 2026-08-17T18:02:19.468Z | managed_process_started |  |  | owner=chatweb-hr |
| 15286 | 2026-08-17T18:02:19.928Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15287 | 2026-08-17T18:02:26.195Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15288 | 2026-08-17T18:02:26.410Z | managed_process_started |  |  | owner=chatweb-hr |
| 15289 | 2026-08-17T18:02:26.903Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15290 | 2026-08-17T18:02:41.127Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15291 | 2026-08-17T18:02:41.368Z | managed_process_started |  |  | owner=chatweb-hr |
| 15292 | 2026-08-17T18:03:32.101Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15293 | 2026-08-17T18:03:32.568Z | managed_process_started |  |  | owner=chatweb-hr |
| 15294 | 2026-08-17T18:03:33.105Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15295 | 2026-08-17T18:04:24.092Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15296 | 2026-08-17T18:04:36.384Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15297 | 2026-08-17T18:04:36.600Z | managed_process_started |  |  | owner=chatweb-hr |
| 15298 | 2026-08-17T18:04:37.078Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15299 | 2026-08-17T18:04:50.832Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15300 | 2026-08-17T18:04:51.125Z | managed_process_started |  |  | owner=chatweb-hr |
| 15301 | 2026-08-17T18:04:51.892Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15302 | 2026-08-17T18:05:02.400Z | managed_process_admitted |  |  | owner=chatweb-hr |
| 15303 | 2026-08-17T18:05:03.044Z | managed_process_started |  |  | owner=chatweb-hr |
| 15304 | 2026-08-17T18:05:04.042Z | managed_process_terminal |  |  | owner=chatweb-hr |
| 15305 | 2026-08-17T18:05:07.261Z | state_transition | ACCEPTING | CHECKPOINTED | reason=controller_acceptance |
| 15306 | 2026-08-17T18:05:07.805Z | wave_processes_quiesced |  |  | reason=orchestration_state:checkpointed |

## Proof

| Stage | Status | Fingerprint | Cache | Duration ms | Exit |
|---|---|---|---:|---:|---:|
| verify:tests | passed | f60df6993555d80b9b76b9b748ecf110ae0fdb21fa5099f5f0d5a70c6db92ab8 | False | 16765 |  |

## Acceptance checkpoints

| Checkpoint | Status | Git HEAD | Proof fingerprint | Accepted by |
|---|---|---|---|---|
| d9b8b78cc7664979b9fff549a26a9a4e | accepted | db4e295cdd2cf71c0a4d0b91f1e5dcb5f9e6e4dc | 4f405f745b6a2e0c5b942aecb560471ce4226d76beff71819993297bfb64d9a0 | chatweb |

## Audit integrity

- Hash chain valid: **True**
- Events checked: `353`
- Chain head: `c45cb4c5c1574d27ddf326ee8e08179e21b092600857f4900bc38479c110ec30`

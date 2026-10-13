#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    BYTE *data;
    DWORD size;
    DWORD error;
} QueryBuffer;

static QueryBuffer query_token(HANDLE token, TOKEN_INFORMATION_CLASS kind) {
    QueryBuffer result = {0};
    GetTokenInformation(token, kind, NULL, 0, &result.size);
    if (result.size == 0 || result.size > 65536) {
        result.error = result.size > 65536 ? ERROR_INSUFFICIENT_BUFFER : GetLastError();
        return result;
    }
    result.data = (BYTE *)HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, result.size);
    if (result.data == NULL) {
        result.error = ERROR_NOT_ENOUGH_MEMORY;
        result.size = 0;
        return result;
    }
    if (!GetTokenInformation(token, kind, result.data, result.size, &result.size)) {
        result.error = GetLastError();
        HeapFree(GetProcessHeap(), 0, result.data);
        result.data = NULL;
    }
    return result;
}

static void free_query(QueryBuffer *query) {
    if (query->data != NULL) HeapFree(GetProcessHeap(), 0, query->data);
    query->data = NULL;
}

static int same_luid(const LUID *left, const LUID *right) {
    return left->LowPart == right->LowPart && left->HighPart == right->HighPart;
}

int main(void) {
    HANDLE token = NULL;
    DWORD open_error = 0;
    if (!OpenProcessToken(GetCurrentProcess(), TOKEN_QUERY, &token)) {
        open_error = GetLastError();
        printf("{\"schema_version\":1,\"complete\":false,\"open_process_token\":false,\"open_error\":%lu}\n", (unsigned long)open_error);
        return 2;
    }

    QueryBuffer elevation = query_token(token, TokenElevation);
    QueryBuffer app_container = query_token(token, TokenIsAppContainer);
    QueryBuffer integrity = query_token(token, TokenIntegrityLevel);
    QueryBuffer groups = query_token(token, TokenGroups);
    QueryBuffer privileges = query_token(token, TokenPrivileges);
    int complete = elevation.data != NULL && app_container.data != NULL && integrity.data != NULL
        && groups.data != NULL && privileges.data != NULL;
    DWORD elevation_error = elevation.data ? 0 : elevation.error;
    DWORD app_container_error = app_container.data ? 0 : app_container.error;
    DWORD integrity_error = integrity.data ? 0 : integrity.error;
    DWORD groups_error = groups.data ? 0 : groups.error;
    DWORD privileges_error = privileges.data ? 0 : privileges.error;
    int elevated = elevation.data ? (((TOKEN_ELEVATION *)elevation.data)->TokenIsElevated != 0) : 0;
    int app = app_container.data ? (*(DWORD *)app_container.data != 0) : 0;
    DWORD integrity_rid = 0;
    int integrity_sid_valid = 0;
    if (integrity.data) {
        TOKEN_MANDATORY_LABEL *label = (TOKEN_MANDATORY_LABEL *)integrity.data;
        UCHAR count = IsValidSid(label->Label.Sid) ? *GetSidSubAuthorityCount(label->Label.Sid) : 0;
        if (count == 0) {
            complete = 0;
            integrity_error = ERROR_INVALID_SID;
        } else {
            integrity_sid_valid = 1;
            integrity_rid = *GetSidSubAuthority(label->Label.Sid, count - 1);
        }
    }

    int administrator_present = 0;
    int administrator_enabled = 0;
    int administrator_deny_only = 0;
    int admin_sid_query_ok = 0;
    if (groups.data) {
        TOKEN_GROUPS *token_groups = (TOKEN_GROUPS *)groups.data;
        BYTE admin_sid[SECURITY_MAX_SID_SIZE];
        DWORD admin_sid_size = sizeof(admin_sid);
        if (CreateWellKnownSid(WinBuiltinAdministratorsSid, NULL, admin_sid, &admin_sid_size)) {
            admin_sid_query_ok = 1;
            for (DWORD index = 0; index < token_groups->GroupCount; ++index) {
                SID_AND_ATTRIBUTES *item = &token_groups->Groups[index];
                if (!EqualSid(item->Sid, admin_sid)) continue;
                administrator_present = 1;
                if ((item->Attributes & SE_GROUP_ENABLED) != 0 && (item->Attributes & SE_GROUP_USE_FOR_DENY_ONLY) == 0)
                    administrator_enabled = 1;
                if ((item->Attributes & SE_GROUP_USE_FOR_DENY_ONLY) != 0)
                    administrator_deny_only = 1;
            }
        } else {
            complete = 0;
            groups_error = GetLastError();
        }
    }

    /* Match only sensitive privilege LUIDs; do not emit account/group names or privilege names. */
    const wchar_t *sensitive_names[] = {
        L"SeDebugPrivilege", L"SeImpersonatePrivilege", L"SeAssignPrimaryTokenPrivilege",
        L"SeTcbPrivilege", L"SeBackupPrivilege", L"SeRestorePrivilege", L"SeTakeOwnershipPrivilege",
        L"SeLoadDriverPrivilege", L"SeCreateTokenPrivilege", L"SeSecurityPrivilege", L"SeSystemEnvironmentPrivilege"
    };
    unsigned int sensitive_enabled = 0;
    LUID sensitive_luids[sizeof(sensitive_names) / sizeof(sensitive_names[0])];
    int sensitive_lookups_complete = 1;
    unsigned int sensitive_luid_lookup_success_count = 0;
    for (size_t name_index = 0; name_index < sizeof(sensitive_names) / sizeof(sensitive_names[0]); ++name_index) {
        if (!LookupPrivilegeValueW(NULL, sensitive_names[name_index], &sensitive_luids[name_index])) {
            sensitive_lookups_complete = 0;
            complete = 0;
            privileges_error = GetLastError();
        } else sensitive_luid_lookup_success_count++;
    }
    if (privileges.data) {
        TOKEN_PRIVILEGES *token_privileges = (TOKEN_PRIVILEGES *)privileges.data;
        for (DWORD index = 0; index < token_privileges->PrivilegeCount; ++index) {
            for (size_t name_index = 0; name_index < sizeof(sensitive_names) / sizeof(sensitive_names[0]); ++name_index) {
                if (sensitive_lookups_complete
                    && same_luid(&token_privileges->Privileges[index].Luid, &sensitive_luids[name_index])
                    && (token_privileges->Privileges[index].Attributes & SE_PRIVILEGE_ENABLED) != 0) {
                    sensitive_enabled++;
                    break;
                }
            }
        }
    }

    if (!integrity_sid_valid || !admin_sid_query_ok || sensitive_luid_lookup_success_count != 11)
        complete = 0;

    printf("{\"schema_version\":1,\"complete\":%s,\"open_process_token\":true,\"elevated\":%s,\"app_container\":%s,\"integrity_rid\":%lu,\"integrity_sid_valid\":%s,\"high_or_system_integrity\":%s,\"admin_sid_query_ok\":%s,\"administrator_group_present\":%s,\"administrator_group_enabled\":%s,\"administrator_group_deny_only\":%s,\"sensitive_privileges_enabled\":%u,\"sensitive_luid_lookup_success_count\":%u,\"query_errors\":{\"elevation\":%lu,\"app_container\":%lu,\"integrity\":%lu,\"groups\":%lu,\"privileges\":%lu}}\n",
        complete ? "true" : "false", elevated ? "true" : "false", app ? "true" : "false",
        (unsigned long)integrity_rid, integrity_sid_valid ? "true" : "false", integrity_rid >= 12288 ? "true" : "false",
        admin_sid_query_ok ? "true" : "false",
        administrator_present ? "true" : "false", administrator_enabled ? "true" : "false",
        administrator_deny_only ? "true" : "false", sensitive_enabled, sensitive_luid_lookup_success_count,
        (unsigned long)elevation_error, (unsigned long)app_container_error, (unsigned long)integrity_error,
        (unsigned long)groups_error, (unsigned long)privileges_error);

    free_query(&elevation);
    free_query(&app_container);
    free_query(&integrity);
    free_query(&groups);
    free_query(&privileges);
    CloseHandle(token);
    return complete ? 0 : 3;
}

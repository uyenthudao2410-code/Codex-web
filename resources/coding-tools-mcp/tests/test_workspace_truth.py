from __future__ import annotations

from pathlib import Path

import pytest

from coding_tools_mcp import server
from coding_tools_mcp.errors import ToolFailure
from coding_tools_mcp.workspace_truth import install_workspace_truth_guard


def _guarded_workspace(root: Path, authorized_roots: list[Path] | None = None):
    install_workspace_truth_guard(server)
    return server.Workspace(root, authorized_roots or [])


def test_active_workspace_is_authoritative_for_absolute_paths(tmp_path: Path) -> None:
    root = tmp_path / "current-workspace"
    child = root / "child"
    stale = tmp_path / "old-workspace"
    authorized = tmp_path / "authorized-external"
    for path in (child, stale, authorized):
        path.mkdir(parents=True)

    workspace = _guarded_workspace(root, [authorized])

    assert workspace.root == root.resolve()
    assert workspace.resolve_existing(".").path == root.resolve()
    assert workspace.resolve_existing(str(root)).path == root.resolve()
    assert workspace.resolve_existing(str(child)).path == child.resolve()
    assert workspace.resolve_existing(str(authorized)).path == authorized.resolve()

    with pytest.raises(ToolFailure) as failure:
        workspace.resolve_existing(str(stale))
    assert failure.value.code == "STALE_WORKSPACE_CONTEXT"
    assert failure.value.category == "security"
    assert failure.value.retryable is False
    assert failure.value.details["active_workspace"] == str(root.resolve())
    assert failure.value.details["requested_path"] == str(stale)


def test_workspace_truth_guard_preserves_existing_escape_checks(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    stale = tmp_path / "outside"
    stale.mkdir()
    workspace = _guarded_workspace(root)

    with pytest.raises(ToolFailure) as relative_escape:
        workspace.resolve_existing("../outside")
    assert relative_escape.value.code == "PATH_OUTSIDE_WORKSPACE"

    link = root / "escape-link"
    try:
        link.symlink_to(stale, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this test host")

    with pytest.raises(ToolFailure) as symlink_escape:
        workspace.resolve_existing(str(link))
    assert symlink_escape.value.code == "SYMLINK_ESCAPE"


def test_canonical_alias_into_active_workspace_remains_valid(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    alias = tmp_path / "workspace-alias"
    try:
        alias.symlink_to(root, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this test host")

    workspace = _guarded_workspace(root)
    assert workspace.resolve_existing(str(alias)).path == root.resolve()


def test_workspace_truth_guard_installation_is_idempotent() -> None:
    install_workspace_truth_guard(server)
    guarded = server.Workspace
    install_workspace_truth_guard(server)
    assert server.Workspace is guarded

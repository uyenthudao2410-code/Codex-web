"""Run tunnel-client's fixed Codex app-server child without a Windows console."""

from __future__ import annotations

import os
import subprocess
import sys


CREATE_NO_WINDOW = 0x08000000


def _binary_stream(name: str):
    stream = getattr(sys, name, None)
    binary = getattr(stream, "buffer", None)
    if binary is None:
        raise RuntimeError(f"{name} pipe is unavailable")
    return binary


def main() -> int:
    command_processor = os.environ.get("COMSPEC") or os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"), "System32", "cmd.exe"
    )
    process = subprocess.Popen(
        [command_processor, "/d", "/s", "/c", "codex app-server"],
        stdin=_binary_stream("stdin"),
        stdout=_binary_stream("stdout"),
        stderr=_binary_stream("stderr"),
        shell=False,
        creationflags=CREATE_NO_WINDOW,
    )
    return process.wait()


if __name__ == "__main__":
    raise SystemExit(main())

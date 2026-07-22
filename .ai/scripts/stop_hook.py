#!/usr/bin/env python3
"""Read-only Claude Code Stop hook; never runs repository tests or writes files."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".ai" / "scripts"))
import agentctl


def hook_input() -> dict:
    try:
        payload = json.load(sys.stdin)
        return payload if isinstance(payload, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def should_skip_stop_hook(payload: dict) -> bool:
    return payload.get("stop_hook_active") is True


if __name__ == "__main__":
    try:
        payload = hook_input()
        if should_skip_stop_hook(payload):
            sys.exit(0)
        exit_code = agentctl.doctor(quick=True)
        if exit_code:
            print("Project Brain chưa đạt kiểm tra an toàn. Hãy chạy `./ai doctor` để xem chi tiết.", file=sys.stderr)
            sys.exit(2)
        sys.exit(0)
    except Exception as exc:
        print(f"Stop hook không thể kiểm tra an toàn: {exc}", file=sys.stderr)
        sys.exit(2)

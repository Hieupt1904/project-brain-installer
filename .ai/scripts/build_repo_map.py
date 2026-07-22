#!/usr/bin/env python3
"""Generate the filtered repository map from the canonical Project Brain config."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".ai" / "scripts"))
import agentctl

if __name__ == "__main__":
    print(agentctl.build_repo_map())

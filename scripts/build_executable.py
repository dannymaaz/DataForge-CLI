#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    cli_file = project_root / "scripts" / "data_toolkit_cli.py"
    dist_dir = project_root / "dist"

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "dataforge_cli",
        str(cli_file),
    ]

    print("[INFO] Ejecutando:", " ".join(command))
    subprocess.run(command, cwd=project_root, check=True)
    print(f"[OK] Ejecutable generado en: {dist_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

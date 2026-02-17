from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .common import TEMP_CSV_DIRNAME, TEMP_SQL_DIRNAME


def cleanup_temp_folders(base_path: Path) -> list[Path]:
    if not base_path.exists() or not base_path.is_dir():
        raise FileNotFoundError(f"No existe la carpeta base: {base_path}")

    removed: list[Path] = []
    for pattern in (TEMP_CSV_DIRNAME, TEMP_SQL_DIRNAME):
        for folder in base_path.rglob(pattern):
            if folder.is_dir():
                shutil.rmtree(folder)
                removed.append(folder)
    return removed


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eliminar carpetas temporales de salida")
    parser.add_argument("--base-path", required=True, help="Ruta base donde buscar carpetas temporales")
    args = parser.parse_args(argv)

    base_path = Path(args.base_path).expanduser().resolve()
    removed = cleanup_temp_folders(base_path)
    if removed:
        print("[OK] Carpetas eliminadas:")
        for item in removed:
            print(f" - {item}")
    else:
        print("[OK] No se encontraron carpetas temporales para eliminar")
    return 0

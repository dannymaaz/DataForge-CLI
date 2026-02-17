from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .excel_csv import detect_header_row


def inspect_excel_structure(excel_path: Path) -> list[dict[str, object]]:
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe el archivo: {excel_path}")

    workbook = pd.ExcelFile(excel_path)
    report: list[dict[str, object]] = []

    for sheet in workbook.sheet_names:
        raw = pd.read_excel(excel_path, sheet_name=sheet, header=None, dtype=object)
        header_row = detect_header_row(raw) if not raw.empty else 0
        non_empty_rows = int(raw.dropna(axis=0, how="all").shape[0])
        non_empty_cols = int(raw.dropna(axis=1, how="all").shape[1])

        report.append(
            {
                "hoja": sheet,
                "filas_no_vacias": non_empty_rows,
                "columnas_no_vacias": non_empty_cols,
                "fila_header_detectada": header_row + 1,
            }
        )

    return report


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspeccionar estructura de Excel")
    parser.add_argument("--excel-path", required=True, help="Ruta del archivo Excel")
    args = parser.parse_args(argv)

    excel_path = Path(args.excel_path).expanduser().resolve()
    report = inspect_excel_structure(excel_path)

    print(f"[OK] Analisis de: {excel_path}")
    for item in report:
        print(
            f" - {item['hoja']}: filas={item['filas_no_vacias']}, "
            f"columnas={item['columnas_no_vacias']}, "
            f"header_sugerido=fila {item['fila_header_detectada']}"
        )

    return 0

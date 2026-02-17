from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from .csv_sql import detect_delimiter


def validate_csv_folder(folder_path: Path, encoding: str = "utf-8") -> list[dict[str, object]]:
    if not folder_path.exists() or not folder_path.is_dir():
        raise FileNotFoundError(f"No existe la carpeta: {folder_path}")

    csv_files = sorted(folder_path.glob("*.csv"))
    if not csv_files:
        raise ValueError("No hay CSV para validar")

    report: list[dict[str, object]] = []
    for csv_file in csv_files:
        delimiter = detect_delimiter(csv_file)
        try:
            df = pd.read_csv(csv_file, dtype=object, sep=delimiter, encoding=encoding, engine="python")
        except EmptyDataError:
            report.append(
                {
                    "archivo": csv_file.name,
                    "filas": 0,
                    "columnas": 0,
                    "delimitador": delimiter,
                    "columnas_duplicadas": 0,
                    "columnas_vacias": 0,
                    "filas_vacias": 0,
                }
            )
            continue

        duplicated_columns = int(df.columns.duplicated().sum())
        empty_columns = int(df.isna().all(axis=0).sum())
        empty_rows = int(df.isna().all(axis=1).sum())

        report.append(
            {
                "archivo": csv_file.name,
                "filas": int(df.shape[0]),
                "columnas": int(df.shape[1]),
                "delimitador": delimiter,
                "columnas_duplicadas": duplicated_columns,
                "columnas_vacias": empty_columns,
                "filas_vacias": empty_rows,
            }
        )

    return report


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validar archivos CSV de una carpeta")
    parser.add_argument("--folder-path", required=True, help="Carpeta con CSV")
    parser.add_argument("--encoding", default="utf-8", help="Encoding de lectura")
    args = parser.parse_args(argv)

    folder_path = Path(args.folder_path).expanduser().resolve()
    report = validate_csv_folder(folder_path, encoding=args.encoding)

    print(f"[OK] Validacion de carpeta: {folder_path}")
    for item in report:
        print(
            f" - {item['archivo']}: filas={item['filas']}, cols={item['columnas']}, "
            f"delim='{item['delimitador']}', dup_cols={item['columnas_duplicadas']}, "
            f"cols_vacias={item['columnas_vacias']}, filas_vacias={item['filas_vacias']}"
        )

    return 0

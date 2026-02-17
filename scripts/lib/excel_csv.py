from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .common import TEMP_CSV_DIRNAME, sanitize_name, unique_column_names

SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".xlsm")


def detect_header_row(raw_df: pd.DataFrame, scan_limit: int = 30) -> int:
    best_row = 0
    best_score = -1.0

    max_row = min(scan_limit, len(raw_df.index))
    for row_idx in range(max_row):
        row = raw_df.iloc[row_idx]
        values = [str(v).strip() for v in row.tolist() if pd.notna(v) and str(v).strip()]
        if len(values) < 2:
            continue

        unique_ratio = len(set(value.lower() for value in values)) / len(values)
        numeric_ratio = sum(1 for value in values if value.replace(".", "", 1).isdigit()) / len(values)
        score = len(values) + (2 * unique_ratio) - numeric_ratio

        if score > best_score:
            best_score = score
            best_row = row_idx

    return best_row


def normalize_date_columns(df: pd.DataFrame, date_keywords: list[str]) -> None:
    keys = [key.lower().strip() for key in date_keywords if key.strip()]
    if not keys:
        return

    for column in df.columns:
        name = str(column).lower()
        if not any(key in name for key in keys):
            continue

        converted = pd.to_datetime(df[column], errors="coerce")
        if converted.notna().any():
            df[column] = converted.dt.strftime("%Y-%m-%d")
            df.loc[converted.isna(), column] = ""


def read_excel_sheet_adaptive(excel_path: Path, sheet_name: str) -> pd.DataFrame:
    raw = pd.read_excel(excel_path, sheet_name=sheet_name, header=None, dtype=object)
    if raw.empty:
        return pd.DataFrame()

    header_row = detect_header_row(raw)
    header_values = [str(v).strip() if pd.notna(v) else "" for v in raw.iloc[header_row].tolist()]
    header_values = [value if value else f"columna_{idx + 1}" for idx, value in enumerate(header_values)]
    header_values = unique_column_names(header_values)

    body = raw.iloc[header_row + 1 :].copy()
    body.columns = header_values
    body.dropna(axis=1, how="all", inplace=True)
    body.dropna(axis=0, how="all", inplace=True)
    body.reset_index(drop=True, inplace=True)
    return body


def convert_excel_to_csv(
    excel_path: Path,
    output_dir: Path | None = None,
    sheets: list[str] | None = None,
    delimiter: str = ",",
    encoding: str = "utf-8",
    date_keywords: list[str] | None = None,
    drop_empty_rows: bool = True,
) -> dict[str, int]:
    if not excel_path.exists():
        raise FileNotFoundError(f"No existe el archivo Excel: {excel_path}")
    if excel_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError("Archivo no soportado. Usa .xlsx, .xls o .xlsm")

    if output_dir is None:
        output_dir = excel_path.parent / TEMP_CSV_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    workbook = pd.ExcelFile(excel_path)
    available_sheets = workbook.sheet_names
    selected_sheets = sheets if sheets else available_sheets

    missing = [sheet for sheet in selected_sheets if sheet not in available_sheets]
    if missing:
        raise ValueError(f"Estas hojas no existen: {', '.join(missing)}")

    keywords = date_keywords if date_keywords else ["fecha", "date"]
    result: dict[str, int] = {}

    for sheet_name in selected_sheets:
        df = read_excel_sheet_adaptive(excel_path, sheet_name)
        if not df.empty:
            df.columns = unique_column_names([sanitize_name(str(col), "columna") for col in df.columns.tolist()])
            if drop_empty_rows:
                df.dropna(axis=0, how="all", inplace=True)
            normalize_date_columns(df, keywords)

        output_file = output_dir / f"{sanitize_name(sheet_name, fallback='hoja')}.csv"
        df.to_csv(output_file, index=False, encoding=encoding, sep=delimiter)
        result[output_file.name] = len(df)

    return result


def _parse_csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extraer hojas de Excel a CSV")
    parser.add_argument("--excel-path", required=True, help="Ruta del archivo Excel")
    parser.add_argument("--output-dir", help="Carpeta de salida para CSV")
    parser.add_argument("--sheets", help="Hojas separadas por coma")
    parser.add_argument("--delimiter", default=",", help="Delimitador CSV")
    parser.add_argument("--encoding", default="utf-8", help="Encoding del CSV")
    parser.add_argument("--date-keywords", default="fecha,date", help="Keywords de fecha separadas por coma")
    parser.add_argument("--keep-empty-rows", action="store_true", help="Conservar filas completamente vacias")
    args = parser.parse_args(argv)

    excel_path = Path(args.excel_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None

    results = convert_excel_to_csv(
        excel_path=excel_path,
        output_dir=output_dir,
        sheets=_parse_csv_list(args.sheets),
        delimiter=args.delimiter,
        encoding=args.encoding,
        date_keywords=_parse_csv_list(args.date_keywords),
        drop_empty_rows=not args.keep_empty_rows,
    )

    destination = output_dir if output_dir else excel_path.parent / TEMP_CSV_DIRNAME
    print(f"[OK] CSV generados en: {destination}")
    for csv_name, rows in results.items():
        print(f" - {csv_name}: {rows} filas")
    return 0

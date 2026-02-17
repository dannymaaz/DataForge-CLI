from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from .csv_sql import detect_delimiter


def merge_csv_folder(
    folder_path: Path,
    output_file: Path | None = None,
    encoding: str = "utf-8",
    include_source_column: bool = True,
) -> Path:
    if not folder_path.exists() or not folder_path.is_dir():
        raise FileNotFoundError(f"No existe la carpeta: {folder_path}")

    csv_files = sorted(folder_path.glob("*.csv"))
    if not csv_files:
        raise ValueError("No hay CSV para combinar")

    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        delimiter = detect_delimiter(csv_file)
        try:
            df = pd.read_csv(csv_file, dtype=object, sep=delimiter, encoding=encoding, engine="python")
        except EmptyDataError:
            df = pd.DataFrame()
        if include_source_column:
            df["source_file"] = csv_file.name
        frames.append(df)

    merged = pd.concat(frames, axis=0, ignore_index=True, sort=False)
    if output_file is None:
        output_file = folder_path / "merged_all.csv"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_file, index=False, encoding="utf-8")
    return output_file


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Combinar CSV de una carpeta en uno solo")
    parser.add_argument("--folder-path", required=True, help="Carpeta con CSV")
    parser.add_argument("--output-file", help="Archivo CSV de salida")
    parser.add_argument("--encoding", default="utf-8", help="Encoding de lectura")
    parser.add_argument("--no-source-column", action="store_true", help="No agregar columna source_file")
    args = parser.parse_args(argv)

    folder_path = Path(args.folder_path).expanduser().resolve()
    output_file = Path(args.output_file).expanduser().resolve() if args.output_file else None

    generated = merge_csv_folder(
        folder_path=folder_path,
        output_file=output_file,
        encoding=args.encoding,
        include_source_column=not args.no_source_column,
    )
    print(f"[OK] CSV combinado generado en: {generated}")
    return 0

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from .common import TEMP_SQL_DIRNAME, sanitize_name, unique_column_names


CSV_TABLE_MAP_STAGING_V2 = {
    "terapia": "stg_terapias",
    "consejeria": "stg_terapias",
    "consejeria_por_llamada": "stg_terapias",
    "bloques": "stg_chat",
    "capacitacion": "stg_capacitaciones",
    "viaticos": "stg_viaticos",
    "contabilidad": "stg_viaticos",
    "organizaciones": "stg_organizaciones",
    "usuarioterapia": "stg_profesionales",
    "users": "stg_profesionales",
    "report": "stg_report",
    "terapias": "stg_terapias",
    "chat": "stg_chat",
    "capacitaciones": "stg_capacitaciones",
    "profesionales": "stg_profesionales",
}

ALLOWED_COLUMNS_STAGING_V2 = {
    "stg_terapias": [
        "appsheet_row_id",
        "fecha",
        "mes",
        "organizacion",
        "tipo",
        "profesional",
        "paciente",
        "servicio",
        "modalidad",
        "idioma",
        "pareja",
        "motivo_consulta",
        "motivo_consulta_otro",
        "honorarios",
        "precio",
        "sesiones",
        "estado",
        "moneda",
        "observaciones",
        "fec",
        "usuarix",
        "usuariochatname",
        "tipoconsulta",
        "tipollamada",
        "tipoterapia",
        "tipopda",
        "horario",
        "propietario",
        "comentario",
        "comentarios",
        "duracion",
        "org_name_raw",
    ],
    "stg_chat": [
        "appsheet_row_id",
        "fecha",
        "mes",
        "organizacion",
        "tipo",
        "profesional",
        "paciente",
        "servicio",
        "modalidad",
        "idioma",
        "motivo_consulta",
        "honorarios",
        "precio",
        "bloques_horas",
        "estado",
        "moneda",
        "observaciones",
        "org_name_raw",
    ],
    "stg_capacitaciones": [
        "appsheet_row_id",
        "fecha",
        "mes",
        "organizacion",
        "servicio",
        "modalidad",
        "participantes",
        "precio",
        "estado",
        "observaciones",
        "org_name_raw",
    ],
    "stg_viaticos": [
        "appsheet_row_id",
        "fecha",
        "organizacion",
        "tipo",
        "profesional",
        "concepto",
        "monto",
        "moneda",
        "estado",
        "receipt_url",
        "observaciones",
        "ordenpagoid",
        "fechapago",
        "fechadeposito",
        "total",
        "org_name_raw",
        "comprobantedeposito",
    ],
    "stg_organizaciones": [
        "appsheet_row_id",
        "organizacion",
        "tipo",
        "canal",
        "nameorg",
        "org_name_raw",
    ],
    "stg_profesionales": [
        "appsheet_row_id",
        "profesional",
        "correo",
        "telefono",
        "usuarix",
        "name",
        "email",
        "propietario",
    ],
}

RENAME_MAP_STAGING_V2_RAW = {
    "id": "appsheet_row_id",
    "userid": "appsheet_row_id",
    "_row_number": "appsheet_row_id",
    "ordenpagoid": "appsheet_row_id",
    "organizaciÃ³n": "org_name_raw",
    "nameorg": "org_name_raw",
    "date": "fecha",
    "fecservicio": "fecha",
    "useremail": "correo",
    "username": "name",
}

IGNORE_FILE_KEYWORDS_STAGING_V2 = ("grafica", "filtro", "documents", "mettings")


@dataclass
class SqlGenerationReport:
    profile: str
    output_path: Path
    items: dict[str, int] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def normalize_column_name(value: object) -> str:
    name = str(value).strip().lower().replace(" ", "_").replace("/", "_").replace(".", "")
    name = name.replace("-", "_")
    name = re.sub(r"[^a-z0-9_]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "columna"


def normalized_rename_map() -> dict[str, str]:
    return {normalize_column_name(key): value for key, value in RENAME_MAP_STAGING_V2_RAW.items()}


def detect_delimiter(file_path: Path) -> str:
    sample = file_path.read_text(encoding="utf-8", errors="ignore")[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def read_csv_flexible(file_path: Path, preferred_encoding: str = "utf-8") -> tuple[pd.DataFrame, str]:
    delimiter = detect_delimiter(file_path)
    candidates = [preferred_encoding, "utf-8-sig", "utf-8", "latin-1"]
    tried: list[str] = []

    for encoding in candidates:
        if encoding in tried:
            continue
        tried.append(encoding)
        try:
            frame = pd.read_csv(file_path, dtype=object, sep=delimiter, encoding=encoding, engine="python")
            return frame, encoding
        except UnicodeDecodeError:
            continue
        except EmptyDataError:
            return pd.DataFrame(), encoding

    raise ValueError(f"No se pudo leer {file_path.name} con encodings: {', '.join(tried)}")


def sql_literal(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "NULL"

    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return "NULL"
        escaped = trimmed.replace("'", "''")
        return f"'{escaped}'"

    if isinstance(value, (int, float)) and not pd.isna(value):
        return str(value)

    if isinstance(value, (pd.Timestamp, datetime)):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"

    text = str(value).strip()
    if not text:
        return "NULL"

    escaped = text.replace("'", "''")
    return f"'{escaped}'"


def build_insert_statements(df: pd.DataFrame, table_name: str, chunk_size: int = 500) -> str:
    columns = unique_column_names([sanitize_name(str(col), fallback="columna") for col in df.columns.tolist()])
    df = df.copy()
    df.columns = columns

    statement_blocks: list[str] = []
    column_sql = ", ".join(columns)

    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start : start + chunk_size]
        rows_sql = []
        for row in chunk.itertuples(index=False, name=None):
            values_sql = ", ".join(sql_literal(value) for value in row)
            rows_sql.append(f"({values_sql})")

        if rows_sql:
            statement = (
                f"INSERT INTO {table_name} ({column_sql}) VALUES\n"
                + ",\n".join(rows_sql)
                + ";\n"
            )
            statement_blocks.append(statement)

    if not statement_blocks:
        return f"-- No hay filas para insertar en {table_name}\n"
    return "\n".join(statement_blocks)


def csv_to_insert_sql_generic(
    source_path: Path,
    output_dir: Path | None = None,
    table_prefix: str = "",
    encoding: str = "utf-8",
    chunk_size: int = 500,
) -> SqlGenerationReport:
    if not source_path.exists():
        raise FileNotFoundError(f"No existe la ruta: {source_path}")

    csv_files: list[Path]
    if source_path.is_file():
        csv_files = [source_path]
    else:
        csv_files = sorted(source_path.glob("*.csv"))

    if not csv_files:
        raise ValueError("No se encontraron archivos CSV")

    if output_dir is None:
        output_dir = source_path.parent / TEMP_SQL_DIRNAME if source_path.is_file() else source_path / TEMP_SQL_DIRNAME
    output_dir.mkdir(parents=True, exist_ok=True)

    report = SqlGenerationReport(profile="generic", output_path=output_dir)
    for csv_file in csv_files:
        table_name = sanitize_name(f"{table_prefix}{csv_file.stem}", fallback="tabla")
        try:
            df, used_encoding = read_csv_flexible(csv_file, preferred_encoding=encoding)
            df.dropna(axis=0, how="all", inplace=True)
            sql_content = build_insert_statements(df, table_name=table_name, chunk_size=chunk_size)
            row_count = len(df)
            if used_encoding.lower() != encoding.lower():
                report.notes.append(f"{csv_file.name}: encoding detectado '{used_encoding}'")
        except EmptyDataError:
            sql_content = f"-- CSV vacio: {csv_file.name}\n-- No hay filas para insertar en {table_name}\n"
            row_count = 0

        sql_file = output_dir / f"{table_name}.sql"
        sql_file.write_text(sql_content, encoding="utf-8")
        report.items[sql_file.name] = row_count

    return report


def resolve_target_table(base_name: str) -> str | None:
    if base_name in CSV_TABLE_MAP_STAGING_V2:
        return CSV_TABLE_MAP_STAGING_V2[base_name]

    for key, value in CSV_TABLE_MAP_STAGING_V2.items():
        if key in base_name:
            return value

    return None


def csv_to_insert_sql_warehouse_clean(
    source_path: Path,
    output_file: Path | None = None,
    encoding: str = "utf-8",
    wrap_transaction: bool = True,
) -> SqlGenerationReport:
    if not source_path.exists():
        raise FileNotFoundError(f"No existe la ruta: {source_path}")

    if source_path.is_file():
        csv_files = [source_path]
        default_output_file = source_path.parent / TEMP_SQL_DIRNAME / "warehouse_seed.sql"
    else:
        csv_files = sorted(source_path.glob("*.csv"))
        default_output_file = source_path / TEMP_SQL_DIRNAME / "warehouse_seed.sql"

    if not csv_files:
        raise ValueError("No se encontraron archivos CSV")

    output_file = output_file or default_output_file
    output_file.parent.mkdir(parents=True, exist_ok=True)

    rename_map = normalized_rename_map()
    report = SqlGenerationReport(profile="warehouse_clean", output_path=output_file)

    with output_file.open("w", encoding="utf-8") as handle:
        handle.write("-- CARGA DE DATOS PARA SCHEMA V2\n")
        if wrap_transaction:
            handle.write("BEGIN;\n\n")

        for csv_file in csv_files:
            base_name = sanitize_name(csv_file.stem, fallback="archivo")
            target_table = resolve_target_table(base_name)

            if not target_table:
                if not any(keyword in base_name for keyword in IGNORE_FILE_KEYWORDS_STAGING_V2):
                    note = f"Ignorado sin mapeo: {csv_file.name}"
                    report.notes.append(note)
                    handle.write(f"-- WARNING: {note}\n")
                continue

            try:
                df, used_encoding = read_csv_flexible(csv_file, preferred_encoding=encoding)
                if used_encoding.lower() != encoding.lower():
                    report.notes.append(f"{csv_file.name}: encoding detectado '{used_encoding}'")
            except EmptyDataError:
                df = pd.DataFrame()

            if df.empty and len(df.columns) == 0:
                handle.write(f"-- INFO: CSV vacio {csv_file.name}\n")
                report.items[f"{csv_file.name} -> {target_table}"] = 0
                continue

            normalized_columns = [normalize_column_name(col) for col in df.columns.tolist()]
            df = df.copy()
            df.columns = normalized_columns

            for source_col, target_col in rename_map.items():
                if source_col in df.columns and target_col not in df.columns:
                    df[target_col] = df[source_col]

            if "organizacion" in df.columns and "org_name_raw" not in df.columns:
                df["org_name_raw"] = df["organizacion"]

            if "email" in df.columns and "correo" not in df.columns:
                df["correo"] = df["email"]

            df = df.loc[:, ~df.columns.duplicated(keep="first")]
            df.dropna(axis=0, how="all", inplace=True)

            allowed = ALLOWED_COLUMNS_STAGING_V2.get(target_table)
            if allowed:
                final_cols = [column for column in allowed if column in df.columns]
            else:
                final_cols = [column for column in df.columns if column]

            if not final_cols:
                warning = f"{csv_file.name} sin columnas validas para {target_table}"
                report.notes.append(warning)
                handle.write(f"-- WARNING: {warning}\n")
                continue

            col_sql = ", ".join(final_cols)
            inserted_rows = 0
            for row in df[final_cols].itertuples(index=False, name=None):
                values = ", ".join(sql_literal(value) for value in row)
                handle.write(f"INSERT INTO {target_table} ({col_sql}) VALUES ({values});\n")
                inserted_rows += 1

            report.items[f"{csv_file.name} -> {target_table}"] = inserted_rows

        if wrap_transaction:
            handle.write("\nCOMMIT;\n")

    return report


def csv_to_insert_sql(
    source_path: Path,
    profile: str = "warehouse_clean",
    output_dir: Path | None = None,
    output_file: Path | None = None,
    table_prefix: str = "",
    encoding: str = "utf-8",
    chunk_size: int = 500,
    wrap_transaction: bool = True,
) -> SqlGenerationReport:
    if profile == "generic":
        return csv_to_insert_sql_generic(
            source_path=source_path,
            output_dir=output_dir,
            table_prefix=table_prefix,
            encoding=encoding,
            chunk_size=chunk_size,
        )

    if profile == "warehouse_clean":
        return csv_to_insert_sql_warehouse_clean(
            source_path=source_path,
            output_file=output_file,
            encoding=encoding,
            wrap_transaction=wrap_transaction,
        )

    raise ValueError(f"Perfil SQL no soportado: {profile}")


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generar SQL INSERT desde CSV")
    parser.add_argument("--source-path", required=True, help="Archivo CSV o carpeta de CSV")
    parser.add_argument(
        "--profile",
        default="warehouse_clean",
        help="Perfil de generacion SQL: warehouse_clean o generic",
    )
    parser.add_argument("--output-dir", help="Carpeta de salida para SQL")
    parser.add_argument("--output-file", help="Archivo SQL final (solo perfil warehouse_clean)")
    parser.add_argument("--table-prefix", default="", help="Prefijo para nombre de tabla")
    parser.add_argument("--encoding", default="utf-8", help="Encoding de lectura de CSV")
    parser.add_argument("--chunk-size", type=int, default=500, help="Cantidad de filas por INSERT")
    parser.add_argument(
        "--no-transaction",
        action="store_true",
        help="No envolver salida con BEGIN/COMMIT (warehouse_clean)",
    )
    args = parser.parse_args(argv)

    source_path = Path(args.source_path).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else None
    output_file = Path(args.output_file).expanduser().resolve() if args.output_file else None
    profile = (args.profile or "warehouse_clean").strip().lower()
    if profile not in {"warehouse_clean", "generic"}:
        raise ValueError("Perfil invalido. Usa 'warehouse_clean' o 'generic'")

    report = csv_to_insert_sql(
        source_path=source_path,
        profile=profile,
        output_dir=output_dir,
        output_file=output_file,
        table_prefix=args.table_prefix,
        encoding=args.encoding,
        chunk_size=max(1, args.chunk_size),
        wrap_transaction=not args.no_transaction,
    )

    print(f"[OK] Perfil usado: {report.profile}")
    print(f"[OK] SQL generado en: {report.output_path}")
    for item_name, rows in report.items.items():
        print(f" - {item_name}: {rows} filas convertidas")
    for note in report.notes:
        print(f" - NOTE: {note}")
    return 0

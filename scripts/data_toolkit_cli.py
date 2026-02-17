#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from lib.cleanup import cleanup_temp_folders
from lib.common import (
    TEMP_CSV_DIRNAME,
    TEMP_SQL_DIRNAME,
    ask_input,
    ask_yes_no,
    print_banner,
    print_panel,
    print_section_header,
    to_path,
)
from lib.csv_sql import csv_to_insert_sql
from lib.excel_csv import convert_excel_to_csv
from lib.inspect_excel import inspect_excel_structure
from lib.merge_csv import merge_csv_folder
from lib.validate_csv import validate_csv_folder


def print_usage_guide() -> None:
    print_section_header("Guia Rapida")
    print_panel(
        "FLUJO RECOMENDADO",
        [
            "1) Usa opcion 1 para extraer Excel -> CSV.",
            "2) Usa opcion 2 para convertir CSV -> SQL INSERT.",
            "3) Perfil SQL: warehouse_clean (staging) o generic (dinamico).",
            "4) Opciones 3-6: inspeccionar, validar, unir y limpiar.",
            "5) Salidas por defecto: csv_exports_local / sql_exports_local.",
        ],
        accent="light",
    )
    print_panel(
        "COMO INGRESAR RUTAS",
        [
            "- Puedes pegar ruta absoluta o relativa.",
            "- Windows ejemplo: C:\\Users\\TuUsuario\\Documents\\archivo.xlsx",
            "- Linux/macOS ejemplo: /home/usuario/archivo.xlsx",
            "- Tip: arrastra el archivo/carpeta a la terminal para pegar su ruta.",
            "- Si una ruta tiene espacios, puedes pegarla con o sin comillas.",
        ],
        accent="light",
    )


def run_excel_to_csv() -> None:
    excel_raw = ask_input("Ruta del Excel (.xlsx/.xls/.xlsm)")
    excel_path = to_path(excel_raw).expanduser().resolve()
    output_default = str(excel_path.parent / TEMP_CSV_DIRNAME)
    output_raw = ask_input("Carpeta salida CSV (ENTER para default)", output_default)
    output_dir = to_path(output_raw).expanduser().resolve()

    sheets_raw = ask_input("Hojas (separadas por coma, vacio=todas)", "")
    date_raw = ask_input("Keywords fecha (coma)", "fecha,date")
    delimiter = ask_input("Delimitador CSV", ",")
    encoding = ask_input("Encoding CSV", "utf-8")
    keep_empty = ask_yes_no("Conservar filas completamente vacias", default_yes=False)

    sheets = [item.strip() for item in sheets_raw.split(",") if item.strip()]
    date_keywords = [item.strip() for item in date_raw.split(",") if item.strip()]

    results = convert_excel_to_csv(
        excel_path=excel_path,
        output_dir=output_dir,
        sheets=sheets,
        delimiter=delimiter,
        encoding=encoding,
        date_keywords=date_keywords,
        drop_empty_rows=not keep_empty,
    )

    print(f"\n[OK] CSV generados en: {output_dir}")
    for csv_name, rows in results.items():
        print(f" - {csv_name}: {rows} filas")


def run_csv_to_sql() -> None:
    source_raw = ask_input("Ruta CSV (archivo .csv o carpeta con CSV)")
    source_path = to_path(source_raw).expanduser().resolve()
    profile_raw = ask_input("Perfil SQL (warehouse_clean/generic)", "warehouse_clean").strip().lower()
    if profile_raw == "generic":
        profile = "generic"
    elif profile_raw == "warehouse_clean":
        profile = "warehouse_clean"
    else:
        raise ValueError("Perfil invalido. Usa warehouse_clean o generic")
    encoding = ask_input("Encoding CSV", "utf-8")

    if profile == "warehouse_clean":
        if source_path.is_file():
            output_default = str(source_path.parent / TEMP_SQL_DIRNAME / "warehouse_seed.sql")
        else:
            output_default = str(source_path / TEMP_SQL_DIRNAME / "warehouse_seed.sql")

        output_raw = ask_input("Archivo SQL final", output_default)
        output_file = to_path(output_raw).expanduser().resolve()
        wrap_transaction = ask_yes_no("Envolver salida con BEGIN/COMMIT", default_yes=True)

        report = csv_to_insert_sql(
            source_path=source_path,
            profile=profile,
            output_file=output_file,
            encoding=encoding,
            wrap_transaction=wrap_transaction,
        )
    else:
        if source_path.is_file():
            output_default = str(source_path.parent / TEMP_SQL_DIRNAME)
        else:
            output_default = str(source_path / TEMP_SQL_DIRNAME)

        output_raw = ask_input("Carpeta salida SQL", output_default)
        output_dir = to_path(output_raw).expanduser().resolve()
        prefix = ask_input("Prefijo de tablas SQL", "")
        chunk_size_raw = ask_input("Filas por bloque INSERT", "500")
        chunk_size = max(1, int(chunk_size_raw))

        report = csv_to_insert_sql(
            source_path=source_path,
            profile=profile,
            output_dir=output_dir,
            table_prefix=prefix,
            encoding=encoding,
            chunk_size=chunk_size,
        )

    print(f"\n[OK] Perfil usado: {report.profile}")
    print(f"[OK] SQL generado en: {report.output_path}")
    for item_name, rows in report.items.items():
        print(f" - {item_name}: {rows} filas convertidas")
    for note in report.notes:
        print(f" - NOTE: {note}")


def run_inspect_excel() -> None:
    excel_raw = ask_input("Ruta del Excel para inspeccionar")
    excel_path = to_path(excel_raw).expanduser().resolve()
    report = inspect_excel_structure(excel_path)

    print(f"\n[OK] Estructura detectada en: {excel_path}")
    for item in report:
        print(
            f" - {item['hoja']}: filas={item['filas_no_vacias']}, "
            f"columnas={item['columnas_no_vacias']}, header_sugerido=fila {item['fila_header_detectada']}"
        )


def run_validate_csv() -> None:
    folder_raw = ask_input("Carpeta con CSV a validar")
    folder_path = to_path(folder_raw).expanduser().resolve()
    encoding = ask_input("Encoding CSV", "utf-8")
    report = validate_csv_folder(folder_path, encoding=encoding)

    print(f"\n[OK] Reporte de validacion: {folder_path}")
    for item in report:
        print(
            f" - {item['archivo']}: filas={item['filas']}, cols={item['columnas']}, "
            f"delim='{item['delimitador']}', dup_cols={item['columnas_duplicadas']}, "
            f"cols_vacias={item['columnas_vacias']}, filas_vacias={item['filas_vacias']}"
        )


def run_merge_csv() -> None:
    folder_raw = ask_input("Carpeta con CSV para unir")
    folder_path = to_path(folder_raw).expanduser().resolve()
    output_default = str(folder_path / "merged_all.csv")
    output_raw = ask_input("Archivo CSV de salida", output_default)
    output_file = to_path(output_raw).expanduser().resolve()
    encoding = ask_input("Encoding CSV", "utf-8")
    include_source = ask_yes_no("Agregar columna source_file", default_yes=True)

    generated = merge_csv_folder(
        folder_path=folder_path,
        output_file=output_file,
        encoding=encoding,
        include_source_column=include_source,
    )
    print(f"\n[OK] CSV combinado: {generated}")


def run_cleanup() -> None:
    base_raw = ask_input("Ruta base para limpiar temporales", str(Path.cwd()))
    base_path = to_path(base_raw).expanduser().resolve()
    confirm = ask_yes_no(
        f"Eliminar carpetas '{TEMP_CSV_DIRNAME}' y '{TEMP_SQL_DIRNAME}' dentro de {base_path}",
        default_yes=False,
    )
    if not confirm:
        print("[INFO] Limpieza cancelada por usuario")
        return

    removed = cleanup_temp_folders(base_path)
    if removed:
        print("[OK] Carpetas eliminadas:")
        for item in removed:
            print(f" - {item}")
    else:
        print("[OK] No se encontraron carpetas temporales")


def print_menu() -> None:
    print_section_header("Menu Principal")
    print_panel(
        "DATAFORGE CLI - ACCIONES",
        [
            "[1] Extraer hojas Excel a CSV",
            "[2] Generar SQL INSERT desde CSV (warehouse_clean/generic)",
            "[3] Inspeccionar estructura de Excel",
            "[4] Validar calidad de CSV",
            "[5] Unir multiples CSV en uno",
            "[6] Limpiar carpetas temporales",
            "[7] Ver guia de uso",
            "[0] Salir",
        ],
        accent="light",
    )


def main() -> int:
    print_banner()
    print_usage_guide()

    while True:
        print_menu()
        option = ask_input("Selecciona una opcion", "1")

        try:
            if option == "1":
                run_excel_to_csv()
            elif option == "2":
                run_csv_to_sql()
            elif option == "3":
                run_inspect_excel()
            elif option == "4":
                run_validate_csv()
            elif option == "5":
                run_merge_csv()
            elif option == "6":
                run_cleanup()
            elif option == "7":
                print_usage_guide()
            elif option == "0":
                print("Hasta luego.")
                return 0
            else:
                print("[ERROR] Opcion invalida")
        except Exception as exc:
            print(f"[ERROR] {exc}")

        input("\nPresiona ENTER para volver al menu...")


if __name__ == "__main__":
    raise SystemExit(main())

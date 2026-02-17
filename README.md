# DataForge CLI

Un toolkit de consola para convertir datos de Excel a CSV y despues a SQL INSERT,
pensado para equipos donde cada usuario trae archivos con estructuras distintas.

Incluye menu interactivo estilo clasico con banner en azul oscuro, firma `BY DANNY MAAZ`
y layout responsive para terminales anchas, medianas y compactas.

## Arranque rapido

1) Instala dependencias:

```bash
pip install -r requirements.txt
```

2) Abre el menu principal:

- Windows:

```bat
run-tool.bat
```

- Linux/macOS:

```bash
sh run-tool.sh
```

- Universal (cualquier SO):

```bash
python scripts/data_toolkit_cli.py
```

3) Flujo recomendado:

- Opcion `1`: Excel -> CSV.
- Opcion `2`: CSV -> SQL INSERT con perfil `warehouse_clean` o `generic`.

## Como ingresar rutas (Excel, CSV y salidas)

En el menu, el programa te pedira rutas en cada paso. Puedes usar:

- Ruta absoluta (recomendada para usuarios nuevos).
- Ruta relativa (desde la carpeta donde ejecutaste el proyecto).
- Ruta pegada con arrastrar y soltar (archivo/carpeta hacia la terminal).

Ejemplos:

- Windows: `C:\Users\TuUsuario\Documents\datos\archivo.xlsx`
- Linux: `/home/tuusuario/datos/archivo.xlsx`
- macOS: `/Users/tuusuario/Documents/datos/archivo.xlsx`

Notas:

- Si la ruta tiene espacios, puedes pegarla con o sin comillas.
- En opcion `1` pide ruta de Excel y luego carpeta de salida CSV.
- En opcion `2` pide archivo CSV o carpeta con CSV y luego la salida SQL.

## Capturas

Vista menu en terminal ancha:

![DataForge CLI wide](docs/screenshots/menu-wide.png)

Vista menu en terminal compacta:

![DataForge CLI compact](docs/screenshots/menu-compact.png)

Vista de generacion SQL (`warehouse_clean`):

![DataForge SQL run](docs/screenshots/sql-run.png)

## Menu principal

1. `Extraer hojas Excel a CSV`
2. `Generar SQL INSERT desde CSV (warehouse_clean/generic)`
3. `Inspeccionar estructura de Excel`
4. `Validar calidad de CSV`
5. `Unir multiples CSV en uno`
6. `Limpiar carpetas temporales`
7. `Ver guia de uso`
0. `Salir`

## Que hace especial este toolkit

- Detecta una fila de encabezado probable por hoja (no asume formato fijo).
- Limpia filas/columnas vacias para exportes mas limpios.
- Normaliza nombres de columnas para evitar roturas en SQL.
- Detecta delimitador en CSV de forma automatica.
- Soporta `utf-8` y `latin-1` para casos reales de archivos heredados.

## Perfil SQL `warehouse_clean`

Este perfil implementa tu estrategia CLEAN INSERT para staging:

- Mapeo de nombres CSV -> tablas `stg_*` por coincidencia exacta y parcial.
- Filtro de columnas permitidas por tabla para mantener consistencia de carga.
- Aliases de columnas frecuentes (`id -> appsheet_row_id`, `date -> fecha`, etc.).
- Manejo de CSV vacios y archivos no mapeados con notas en la salida.
- Salida por defecto en un solo archivo: `warehouse_seed.sql`.
- `BEGIN/COMMIT` configurable (`--no-transaction` para desactivarlo).

Ejemplo:

```bash
python scripts/csv_to_sql_insert.py --source-path "ruta/a/csvs" --profile warehouse_clean
```

## Perfil SQL `generic`

Para cualquier proyecto no acoplado a staging fijo:

- Toma columnas dinamicamente desde cada CSV.
- Genera un `.sql` por archivo CSV.
- Permite prefijo de tablas con `--table-prefix`.

Ejemplo:

```bash
python scripts/csv_to_sql_insert.py --source-path "ruta/a/csvs" --profile generic --table-prefix stg_
```

## Carpetas de salida por defecto

- CSV: `csv_exports_local`
- SQL: `sql_exports_local`

Ambas estan ignoradas en `.gitignore` para evitar subir archivos temporales.

## Ejecutable local (opcional)

```bash
pip install -r requirements-dev.txt
python scripts/build_executable.py
```

Se genera en `dist/`.

## Compatibilidad

- Windows: `run-tool.bat`
- Linux/macOS: `sh run-tool.sh`
- Universal: `python scripts/data_toolkit_cli.py`

Ademas, la CI en `.github/workflows/python-ci.yml` esta en matriz multiplataforma
(`ubuntu`, `windows`, `macos`) para validar scripts y comandos en los 3 sistemas.

## Scripts disponibles

- `scripts/data_toolkit_cli.py` -> menu interactivo principal.
- `scripts/convert_excel_to_csv.py` -> conversion por parametros.
- `scripts/csv_to_sql_insert.py` -> SQL por perfiles (`warehouse_clean`/`generic`).
- `scripts/inspect_excel_structure.py` -> diagnostico de estructura Excel.
- `scripts/validate_csv_folder.py` -> validacion de calidad CSV.
- `scripts/merge_csv_files.py` -> union de CSV en un archivo.
- `scripts/cleanup_temp_outputs.py` -> limpieza de carpetas temporales.
- `scripts/build_executable.py` -> build de ejecutable con PyInstaller.

## Estructura del proyecto

```text
.
|-- .github/workflows/python-ci.yml
|-- data/
|   |-- input/.gitkeep
|   `-- output/.gitkeep
|-- scripts/
|   |-- data_toolkit_cli.py
|   |-- convert_excel_to_csv.py
|   |-- csv_to_sql_insert.py
|   |-- inspect_excel_structure.py
|   |-- validate_csv_folder.py
|   |-- merge_csv_files.py
|   |-- cleanup_temp_outputs.py
|   |-- build_executable.py
|   `-- lib/
|       |-- common.py
|       |-- excel_csv.py
|       |-- csv_sql.py
|       |-- inspect_excel.py
|       |-- validate_csv.py
|       |-- merge_csv.py
|       `-- cleanup.py
|-- run-tool.bat
|-- run-tool.sh
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- requirements-dev.txt
|-- LICENSE
`-- README.md
```

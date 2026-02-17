#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "screenshots"


def load_font(size: int, bold: bool = False) -> Any:
    regular_candidates = [
        "C:/Windows/Fonts/consola.ttf",
        "C:/Windows/Fonts/Consolas.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    ]
    bold_candidates = [
        "C:/Windows/Fonts/consolab.ttf",
        "C:/Windows/Fonts/Consolas-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]
    candidates = bold_candidates + regular_candidates if bold else regular_candidates

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def create_gradient_background(width: int, height: int) -> Image.Image:
    top = (8, 13, 31)
    bottom = (14, 28, 60)
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)

    for y in range(height):
        ratio = y / max(1, height - 1)
        r = int(top[0] * (1 - ratio) + bottom[0] * ratio)
        g = int(top[1] * (1 - ratio) + bottom[1] * ratio)
        b = int(top[2] * (1 - ratio) + bottom[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # subtle accent glow (top-right)
    glow = Image.new("RGBA", (width, height), 0)
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [(width - 420, -180), (width + 140, 380)],
        fill=(37, 99, 235, 56),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    image.paste(glow, (0, 0), glow)
    return image


def rounded_window(
    canvas: Image.Image,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    radius: int = 14,
) -> None:
    shadow = Image.new("RGBA", canvas.size, 0)
    sdraw = ImageDraw.Draw(shadow)
    sdraw.rounded_rectangle(
        [(x0 + 8, y0 + 10), (x1 + 8, y1 + 10)],
        radius=radius,
        fill=(0, 0, 0, 130),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(9))
    canvas.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [(x0, y0), (x1, y1)],
        radius=radius,
        fill=(15, 23, 42),
        outline=(37, 99, 235),
        width=2,
    )
    draw.rectangle(
        [(x0, y0), (x1, y0 + 44)],
        fill=(17, 28, 51),
    )

    # terminal chrome buttons
    button_y = y0 + 23
    colors = [(239, 68, 68), (245, 158, 11), (34, 197, 94)]
    for i, color in enumerate(colors):
        cx = x0 + 24 + i * 18
        draw.ellipse([(cx - 5, button_y - 5), (cx + 5, button_y + 5)], fill=color)


def draw_badges(
    image: Image.Image,
    x: int,
    y: int,
    labels: list[tuple[str, tuple[int, int, int]]],
) -> int:
    draw = ImageDraw.Draw(image)
    font = load_font(15, bold=True)
    gap = 10
    cursor = x

    for text, color in labels:
        bbox = draw.textbbox((0, 0), text, font=font)
        w = (bbox[2] - bbox[0]) + 24
        h = 30
        draw.rounded_rectangle([(cursor, y), (cursor + w, y + h)], radius=15, fill=color)
        draw.text((cursor + 12, y + 7), text, fill=(239, 246, 255), font=font)
        cursor += w + gap

    return cursor


def write_lines(
    image: Image.Image,
    x: int,
    y: int,
    lines: list[tuple[str, str]],
    line_step: int = 28,
) -> None:
    draw = ImageDraw.Draw(image)
    mono = load_font(18)
    mono_bold = load_font(18, bold=True)
    palette = {
        "ok": (74, 222, 128),
        "note": (251, 191, 36),
        "title": (191, 219, 254),
        "line": (219, 234, 254),
        "muted": (148, 163, 184),
        "accent": (96, 165, 250),
    }

    cursor_y = y
    for kind, text in lines:
        font = mono_bold if kind in {"title", "ok"} else mono
        draw.text((x, cursor_y), text, fill=palette.get(kind, palette["line"]), font=font)
        cursor_y += line_step


def add_footer(image: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(image)
    font = load_font(14)
    draw.text((26, image.height - 26), text, fill=(100, 116, 139), font=font)


def render_menu_wide() -> None:
    width, height = 1400, 780
    image = create_gradient_background(width, height)
    rounded_window(image, 42, 44, width - 42, height - 44)

    draw = ImageDraw.Draw(image)
    title_font = load_font(30, bold=True)
    draw.text((94, 94), "DataForge CLI - Release Preview (Wide)", fill=(147, 197, 253), font=title_font)

    draw_badges(
        image,
        96,
        140,
        [
            ("Responsive UI", (30, 64, 175)),
            ("Dark Blue Theme", (29, 78, 216)),
            ("Cross-platform", (37, 99, 235)),
        ],
    )

    lines = [
        ("title", "[>] Guia Rapida"),
        ("line", "1) Usa opcion 1 para extraer Excel -> CSV."),
        ("line", "2) Usa opcion 2 para convertir CSV -> SQL INSERT."),
        ("line", "3) Perfil SQL: warehouse_clean (staging) o generic (dinamico)."),
        ("muted", ""),
        ("title", "[>] Menu Principal"),
        ("accent", "[1] Extraer hojas Excel a CSV"),
        ("accent", "[2] Generar SQL INSERT desde CSV (warehouse_clean/generic)"),
        ("accent", "[3] Inspeccionar estructura de Excel"),
        ("accent", "[4] Validar calidad de CSV"),
        ("accent", "[5] Unir multiples CSV en uno"),
        ("accent", "[6] Limpiar carpetas temporales"),
        ("accent", "[7] Ver guia de uso"),
        ("accent", "[0] Salir"),
    ]
    write_lines(image, 96, 196, lines, line_step=34)
    add_footer(image, "DataForge CLI • Premium README Mockup • Wide terminal mode")
    image.save(OUT_DIR / "menu-wide.png", format="PNG", optimize=True)


def render_menu_compact() -> None:
    width, height = 1120, 700
    image = create_gradient_background(width, height)
    rounded_window(image, 36, 40, width - 36, height - 40)

    draw = ImageDraw.Draw(image)
    title_font = load_font(28, bold=True)
    draw.text((84, 88), "DataForge CLI - Release Preview (Compact)", fill=(191, 219, 254), font=title_font)

    draw_badges(
        image,
        86,
        136,
        [
            ("Compact Friendly", (29, 78, 216)),
            ("Retro Layout", (30, 64, 175)),
        ],
    )

    lines = [
        ("title", "> Guia Rapida"),
        ("line", "- 1) Extraer Excel -> CSV"),
        ("line", "- 2) Convertir CSV -> SQL INSERT"),
        ("line", "- 3) Perfil: warehouse_clean o generic"),
        ("muted", ""),
        ("title", "> Menu Principal"),
        ("accent", "[1] Excel a CSV   [2] CSV a SQL   [3] Inspeccionar"),
        ("accent", "[4] Validar CSV   [5] Unir CSV    [6] Limpiar"),
        ("accent", "[7] Guia de uso   [0] Salir"),
    ]
    write_lines(image, 86, 202, lines, line_step=38)
    add_footer(image, "DataForge CLI • Premium README Mockup • Compact terminal mode")
    image.save(OUT_DIR / "menu-compact.png", format="PNG", optimize=True)


def render_sql_run() -> None:
    width, height = 1320, 680
    image = create_gradient_background(width, height)
    rounded_window(image, 38, 40, width - 38, height - 40)

    draw = ImageDraw.Draw(image)
    title_font = load_font(29, bold=True)
    draw.text((90, 92), "DataForge CLI - SQL Generation (warehouse_clean)", fill=(147, 197, 253), font=title_font)

    draw_badges(
        image,
        92,
        140,
        [
            ("warehouse_clean", (30, 64, 175)),
            ("SQL Output", (29, 78, 216)),
            ("Release Ready", (37, 99, 235)),
        ],
    )

    lines = [
        ("ok", "[OK] Perfil usado: warehouse_clean"),
        ("ok", "[OK] SQL generado en: .../sql_exports_local/warehouse_seed.sql"),
        ("muted", ""),
        ("line", "- terapia.csv -> stg_terapias: 1937 filas convertidas"),
        ("line", "- users.csv -> stg_profesionales: 29 filas convertidas"),
        ("line", "- viaticos.csv -> stg_viaticos: 48 filas convertidas"),
        ("line", "- consejeria.csv -> stg_terapias: 31 filas convertidas"),
        ("note", "- NOTE: Ignorado sin mapeo: merged_all.csv"),
        ("note", "- NOTE: Ignorado sin mapeo: organizacioninventario.csv"),
        ("muted", ""),
        ("title", "Command"),
        ("accent", "python scripts/csv_to_sql_insert.py --source-path \"ruta/a/csvs\" --profile warehouse_clean"),
    ]
    write_lines(image, 92, 194, lines, line_step=34)
    add_footer(image, "DataForge CLI • Premium README Mockup • SQL generation output")
    image.save(OUT_DIR / "sql-run.png", format="PNG", optimize=True)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render_menu_wide()
    render_menu_compact()
    render_sql_run()
    print(f"[OK] Premium PNG screenshots generated in: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

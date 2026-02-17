from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path


TEMP_CSV_DIRNAME = "csv_exports_local"
TEMP_SQL_DIRNAME = "sql_exports_local"
MIN_PANEL_WIDTH = 56
MAX_PANEL_WIDTH = 100


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")
    return True


def _paint(text: str, enabled: bool, code: str) -> str:
    if not enabled:
        return text
    return f"\033[{code}m{text}\033[0m"


def _dark_blue(text: str, enabled: bool) -> str:
    return _paint(text, enabled, "38;5;33")


def _light_blue(text: str, enabled: bool) -> str:
    return _paint(text, enabled, "38;5;39")


def _bold(text: str, enabled: bool) -> str:
    return _paint(text, enabled, "1")


def _fit_line(line: str, width: int) -> str:
    if len(line) <= width:
        return line.ljust(width)
    return line[: width - 3] + "..."


def _terminal_width() -> int:
    try:
        return shutil.get_terminal_size(fallback=(100, 30)).columns
    except OSError:
        return 100


def _layout_mode(width: int | None = None) -> str:
    current_width = width if width is not None else _terminal_width()
    if current_width < 80:
        return "compact"
    if current_width < 100:
        return "standard"
    return "wide"


def _panel_width(width: int | None = None) -> int:
    current_width = width if width is not None else _terminal_width()
    available = max(MIN_PANEL_WIDTH, current_width - 2)
    return min(MAX_PANEL_WIDTH, available)


def print_panel(title: str, lines: list[str], accent: str = "dark") -> None:
    color_on = _supports_color()
    terminal_width = _terminal_width()
    mode = _layout_mode(terminal_width)

    color_fn = _dark_blue if accent == "dark" else _light_blue

    if mode == "compact":
        max_line = max(26, terminal_width - 6)
        print(color_fn(f"[ {title} ]", color_on))
        for line in lines:
            print(color_fn(f" - {_fit_line(line, max_line).rstrip()}", color_on))
        return

    box_width = _panel_width(terminal_width)
    inner_width = box_width - 4
    border = "+" + ("-" * (box_width - 2)) + "+"

    print(color_fn(border, color_on))
    print(color_fn(f"| {_fit_line(title.center(inner_width), inner_width)} |", color_on))
    print(color_fn("|" + ("-" * (box_width - 2)) + "|", color_on))
    for line in lines:
        print(color_fn(f"| {_fit_line(line, inner_width)} |", color_on))
    print(color_fn(border, color_on))


def print_section_header(title: str) -> None:
    color_on = _supports_color()
    marker_text = "[>]" if _layout_mode() != "compact" else ">"
    marker = _light_blue(marker_text, color_on)
    text = _bold(title, color_on)
    print(f"\n{marker} {text}")


def print_banner() -> None:
    color_on = _supports_color()
    mode = _layout_mode()

    if mode == "compact":
        separator = "-" * min(48, max(24, _terminal_width() - 2))
        print(_dark_blue(separator, color_on))
        print(_dark_blue(_bold("DATAFORGE CLI", color_on), color_on))
        print(_light_blue("BY DANNY MAAZ", color_on))
        print(_light_blue("Excel -> CSV -> SQL pipeline toolkit", color_on))
        print(_dark_blue(separator, color_on))
        return

    lines = [
        r"  ____        _         _____                        ____ _     ___ ",
        r" |  _ \  __ _| |_ __ _ |  ___|__  _ __ __ _  ___  / ___| |   |_ _|",
        r" | | | |/ _` | __/ _` || |_ / _ \| '__/ _` |/ _ \| |   | |    | | ",
        r" | |_| | (_| | || (_| ||  _| (_) | | | (_| |  __/| |___| |___ | | ",
        r" |____/ \__,_|\__\__,_||_|  \___/|_|  \__, |\___| \____|_____|___|",
        r"                                      |___/                         ",
        "",
        "                     BY DANNY MAAZ  -  DATA PIPELINE TOOLKIT",
    ]
    print_panel("DATAFORGE CLI", lines, accent="dark")
    identity = "DATAFORGE CLI  |  BY DANNY MAAZ"
    print(_light_blue(_bold(identity, color_on), color_on))
    subtitle = "Professional terminal toolkit for Excel, CSV and SQL workflows"
    if mode == "standard":
        subtitle = "Professional toolkit for Excel, CSV and SQL workflows"
    print(_light_blue(_bold(subtitle, color_on), color_on))


def to_path(raw_value: str) -> Path:
    return Path(raw_value.strip().strip('"').strip("'"))


def ask_input(label: str, default: str | None = None) -> str:
    if default:
        value = input(f"{label} [{default}]: ").strip()
        return value or default
    return input(f"{label}: ").strip()


def ask_yes_no(label: str, default_yes: bool = True) -> bool:
    suffix = "[Y/n]" if default_yes else "[y/N]"
    value = input(f"{label} {suffix}: ").strip().lower()
    if not value:
        return default_yes
    return value in {"y", "yes", "s", "si"}


def sanitize_name(value: str, fallback: str = "item") -> str:
    cleaned = value.strip().lower().replace(" ", "_")
    cleaned = re.sub(r"[^a-z0-9_]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or fallback


def unique_column_names(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for name in columns:
        base = sanitize_name(name, fallback="columna")
        count = seen.get(base, 0) + 1
        seen[base] = count
        result.append(base if count == 1 else f"{base}_{count}")
    return result

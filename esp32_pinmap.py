#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""esp32-pinmap - which GPIO can you actually use on your ESP32 board?

Lookup CLI for safe pins on classic ESP32 / ESP32-S3 / ESP32-C3: flags
strapping pins, flash & PSRAM occupancy, USB-JTAG, UART0 console and
input-only pins, so you stop wondering why your LED never blinks.

Zero third-party dependencies. Data mirrors Espressif datasheets - always
double-check against the official docs for your exact module.
"""

import argparse
import sys
from pathlib import Path

__version__ = "0.1.0"

# Every GPIO that physically exists on the chip gets an entry; missing
# numbers (20/24/28-31 on classic, 22-25 on S3/C3) simply don't exist.
# Flags: strapping / flash / psram / usb_jtag / console / input_only / note
BOARDS = {
    "esp32": {
        0:  {"strapping": True, "note": "boot mode; internal pull-up, must be HIGH at reset"},
        1:  {"console": True, "note": "UART0 TX - console log & flashing"},
        2:  {"strapping": True, "note": "boot mode; internal pull-down"},
        3:  {"console": True, "note": "UART0 RX - console log & flashing"},
        4:  {},
        5:  {"strapping": True, "note": "SDIO slave timing; internal pull-up"},
        6:  {"flash": True, "note": "SPI flash CLK"},
        7:  {"flash": True, "note": "SPI flash D0"},
        8:  {"flash": True, "note": "SPI flash D1"},
        9:  {"flash": True, "note": "SPI flash D2"},
        10: {"flash": True, "note": "SPI flash D3"},
        11: {"flash": True, "note": "SPI flash CMD"},
        12: {"strapping": True, "note": "MTDI: sets flash voltage - external pull-up bricks 3.3V flash boot"},
        13: {},
        14: {},
        15: {"strapping": True, "note": "MTDO: silences boot log; internal pull-up"},
        16: {"note": "PSRAM on WROVER modules, free on WROOM"},
        17: {"note": "PSRAM on WROVER modules, free on WROOM"},
        18: {},
        19: {},
        21: {},
        22: {},
        23: {},
        25: {"note": "DAC1"},
        26: {"note": "DAC2"},
        27: {},
        32: {},
        33: {},
        34: {"input_only": True, "note": "no output, no internal pull resistors"},
        35: {"input_only": True, "note": "no output, no internal pull resistors"},
        36: {"input_only": True, "note": "VP / ADC1_CH0"},
        39: {"input_only": True, "note": "VN / ADC1_CH3"},
    },
    "esp32-s3": {
        0:  {"strapping": True, "note": "boot mode; must be HIGH at reset"},
        1:  {},
        2:  {},
        3:  {"strapping": True, "note": "JTAG source selection at reset"},
        4:  {},
        5:  {},
        6:  {},
        7:  {},
        8:  {},
        9:  {},
        10: {},
        11: {},
        12: {},
        13: {},
        14: {},
        15: {"note": "XTAL_32K_P optional"},
        16: {"note": "XTAL_32K_N optional"},
        17: {},
        18: {},
        19: {"usb_jtag": True, "note": "USB D- - also native USB-JTAG"},
        20: {"usb_jtag": True, "note": "USB D+ - also native USB-JTAG"},
        21: {},
        26: {"flash": True, "note": "SPI flash/PSRAM CLK"},
        27: {"flash": True, "note": "SPI flash/PSRAM D0"},
        28: {"flash": True, "note": "SPI flash/PSRAM D1"},
        29: {"flash": True, "note": "SPI flash/PSRAM D2"},
        30: {"flash": True, "note": "SPI flash/PSRAM D3"},
        31: {"flash": True, "note": "SPI flash/PSRAM CMD"},
        32: {"flash": True, "note": "SPI flash/PSRAM D4 / OCT"},
        33: {"psram": True, "note": "octal PSRAM DQ4 (N8R8/N16R8)"},
        34: {"psram": True, "note": "octal PSRAM DQ5 (N8R8/N16R8)"},
        35: {"psram": True, "note": "octal PSRAM DQ6 (N8R8/N16R8)"},
        36: {"psram": True, "note": "octal PSRAM DQ7 (N8R8/N16R8)"},
        37: {"psram": True, "note": "octal PSRAM DQS (N8R8/N16R8)"},
        38: {},
        39: {},
        40: {},
        41: {},
        42: {},
        43: {"console": True, "note": "UART0 TX - console log"},
        44: {"console": True, "note": "UART0 RX - console log"},
        45: {"strapping": True, "note": "VDD_SPI voltage at reset"},
        46: {"strapping": True, "input_only": True, "note": "boot mode; input-only"},
        47: {},
        48: {},
    },
    "esp32-c3": {
        0:  {},
        1:  {},
        2:  {"strapping": True, "note": "must be floating or LOW at boot"},
        3:  {},
        4:  {},
        5:  {},
        6:  {},
        7:  {},
        8:  {"strapping": True, "note": "internal pull-up, must be HIGH at boot"},
        9:  {"strapping": True, "note": "BOOT button"},
        10: {},
        11: {"flash": True, "note": "SPI flash CLK"},
        12: {"flash": True, "note": "SPI flash D0"},
        13: {"flash": True, "note": "SPI flash D1"},
        14: {"flash": True, "note": "SPI flash D2"},
        15: {"flash": True, "note": "SPI flash D3"},
        16: {"flash": True, "note": "SPI flash CMD"},
        17: {"flash": True, "note": "SPI flash VDD"},
        18: {"usb_jtag": True, "note": "USB D- - also native USB-JTAG"},
        19: {"usb_jtag": True, "note": "USB D+ - also native USB-JTAG"},
        20: {"console": True, "note": "UART0 TX - console log & flashing"},
        21: {"console": True, "note": "UART0 RX - console log & flashing"},
    },
}

RESERVED_KINDS = ("strapping", "flash", "psram", "usb_jtag", "console")


def normalize_board(name):
    s = name.lower().replace(" ", "").replace("_", "-")
    aliases = {
        "s3": "esp32-s3", "esp32s3": "esp32-s3", "esp-32-s3": "esp32-s3",
        "c3": "esp32-c3", "esp32c3": "esp32-c3", "esp-32-c3": "esp32-c3",
        "esp-32": "esp32", "esp32classic": "esp32", "wroom": "esp32", "wrover": "esp32",
    }
    return aliases.get(s, s)


def usable(board, n, for_output=False):
    pin = board.get(n)
    if pin is None:
        return False
    if any(pin.get(k) for k in RESERVED_KINDS):
        return False
    if for_output and pin.get("input_only"):
        return False
    return True


def safe_pins(board, for_output=False):
    return sorted(n for n in board if usable(board, n, for_output=for_output))


def pin_info(board, n, board_name="esp32"):
    pin = board.get(n)
    if pin is None:
        return f"GPIO{n} ({board_name}): DOES NOT EXIST on this chip"
    if not usable(board, n, for_output=False):
        reason = next(k for k in RESERVED_KINDS if pin.get(k))
        label = {"strapping": "RESERVED (strapping)", "flash": "RESERVED (flash)",
                 "psram": "RESERVED (PSRAM)", "usb_jtag": "RESERVED (USB/JTAG)",
                 "console": "RESERVED (UART0 console)"}[reason]
        out = [f"GPIO{n} ({board_name}): {label}"]
    elif pin.get("input_only"):
        out = [f"GPIO{n} ({board_name}): INPUT-ONLY (no output driver, no pull resistors)"]
    else:
        out = [f"GPIO{n} ({board_name}): OK for general I/O"]
    if pin.get("note"):
        out.append(f"  {pin['note']}")
    if not usable(board, n, for_output=True) and usable(board, n, for_output=False):
        out.append("  input-only: usable for reading sensors, not for LEDs")
    return "\n".join(out)


def render_table(board, board_name, for_output=False):
    safe = set(safe_pins(board, for_output=for_output))
    lines = [f"## {board_name} - {'output-capable' if for_output else 'all usable'} pins", "",
             "| GPIO | status | note |", "|---|---|---|"]
    for n in sorted(board):
        pin = board[n]
        if n not in safe:
            reason = next((k for k in RESERVED_KINDS if pin.get(k)), "input-only" if pin.get("input_only") else "?")
            status = f"no ({reason})"
        elif pin.get("input_only"):
            status = "input-only"
        else:
            status = "OK"
        lines.append(f"| {n} | {status} | {pin.get('note', '')} |")
    return "\n".join(lines) + "\n"


EXAMPLES = """examples:
  python esp32_pinmap.py s3 0            # why is GPIO0 special on S3?
  python esp32_pinmap.py s3 --safe       # list pins safe to use
  python esp32_pinmap.py esp32 --table   # full markdown table (paste into notes)
  python esp32_pinmap.py c3 19 --md >> cheatsheet.md
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="esp32-pinmap", description=__doc__.strip().splitlines()[0],
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("board", help="esp32 | esp32-s3 (s3) | esp32-c3 (c3)")
    ap.add_argument("gpio", nargs="*", type=int, help="GPIO number(s) to look up")
    ap.add_argument("--safe", action="store_true", help="list pins safe to use")
    ap.add_argument("--table", action="store_true", help="render full markdown table")
    ap.add_argument("--output-only", action="store_true",
                    help="with --safe/--table: only pins that can drive outputs (LED, relay...)")
    ap.add_argument("-V", "--version", action="version", version=f"esp32-pinmap {__version__}")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    board_name = normalize_board(args.board)
    board = BOARDS.get(board_name)
    if board is None:
        ap.error(f"unknown board '{args.board}' (known: {', '.join(sorted(BOARDS))})")

    if args.safe:
        safe = safe_pins(board, for_output=args.output_only)
        print(f"{board_name} safe pins{' (output-capable)' if args.output_only else ''}:\n  "
              + ", ".join(str(n) for n in safe))
    if args.table:
        print(render_table(board, board_name, for_output=args.output_only))
    for n in args.gpio:
        print(pin_info(board, n, board_name))
    if not args.safe and not args.table and not args.gpio:
        ap.error("give a GPIO number, or use --safe / --table")
    return 0


if __name__ == "__main__":
    sys.exit(main())

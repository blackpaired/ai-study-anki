#!/usr/bin/env python3
"""Checks an Anki CSV ("front","back") for import problems.

Usage:  python3 -I check_csv.py <cards.csv>
Checks: exactly 2 columns per row, no empty fields, duplicate fronts,
very long answers, line breaks (should be <br>). Header lines starting with # are skipped.
Exit code 0 = all good, 1 = errors found.
"""
import csv
import sys

MAX_BACK = 300  # characters; longer backs are usually too much for one card


def main(path):
    errors, warnings = [], []
    seen = {}
    cards = 0
    with open(path, newline="", encoding="utf-8") as f:
        lines = [l for l in f if not l.startswith("#")]
    for nr, fields in enumerate(csv.reader(lines), start=1):
        if not fields:
            continue
        cards += 1
        if len(fields) != 2:
            errors.append(f"card {nr}: {len(fields)} columns instead of 2 → {fields[:3]}")
            continue
        front, back = (s.strip() for s in fields)
        if not front or not back:
            errors.append(f"card {nr}: empty field → {fields}")
        if "\n" in front or "\n" in back:
            warnings.append(f"card {nr}: real line break in a field, use <br> instead")
        if len(back) > MAX_BACK:
            warnings.append(f"card {nr}: back is {len(back)} characters long – split it?")
        key = front.lower()
        if key in seen:
            warnings.append(f"card {nr}: same front as card {seen[key]} → \"{front}\"")
        else:
            seen[key] = nr

    print(f"{cards} cards checked: {len(errors)} errors, {len(warnings)} warnings")
    for e in errors:
        print("  ERROR  ", e)
    for w in warnings:
        print("  warning", w)
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))

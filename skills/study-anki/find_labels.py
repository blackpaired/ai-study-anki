#!/usr/bin/env python3
"""Finds the labels in a figure (with Tesseract) and prints their boxes as JSON –
as the basis for image occlusion cards.

Usage:
  python3 -I find_labels.py <image.png> [--lang eng] [--padding 4]
  python3 -I find_labels.py <page.png> --crop left,top,right,bottom --out <figure.png> [...]

With --crop, the region (in pixels) is first saved as a new image, which is then analysed.
Output: {"image": ..., "width": ..., "height": ..., "labels":
[{"text": "Pulp", "left": .., "top": .., "width": .., "height": ..}, ...]} – the boxes fit directly
into "boxes" of an image occlusion card (anki_package.py). You decide which of them to hide;
leave out filler words, page numbers and captions.
"""
import argparse
import json
import subprocess
import sys

from PIL import Image


def words(image, lang):
    tsv = subprocess.run(["tesseract", image, "-", "-l", lang, "--psm", "11", "tsv"],
                         capture_output=True, text=True, check=True).stdout
    header, *rows = tsv.splitlines()
    columns = header.split("\t")
    for r in rows:
        w = dict(zip(columns, r.split("\t")))
        text = w.get("text", "").strip()
        if text and float(w.get("conf", -1)) >= 40 and any(ch.isalnum() for ch in text):
            yield {"text": text, "line": (w["block_num"], w["par_num"], w["line_num"]),
                   "l": int(w["left"]), "t": int(w["top"]), "w": int(w["width"]), "h": int(w["height"])}


def group(word_list):
    """Merges words on the same line into one label, unless there is a large gap."""
    groups = []
    for w in sorted(word_list, key=lambda w: (w["line"], w["l"])):
        g = groups[-1] if groups else None
        if g and g["line"] == w["line"] and w["l"] - (g["l"] + g["w"]) < 1.5 * max(g["h"], w["h"]):
            right, bottom = max(g["l"] + g["w"], w["l"] + w["w"]), max(g["t"] + g["h"], w["t"] + w["h"])
            g["l"], g["t"] = min(g["l"], w["l"]), min(g["t"], w["t"])
            g["w"], g["h"] = right - g["l"], bottom - g["t"]
            g["text"] += " " + w["text"]
        else:
            groups.append(dict(w))
    return groups


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--lang", default="eng", help="Tesseract languages, e.g. eng or deu+eng")
    ap.add_argument("--padding", type=int, default=4, help="pixels added around every box")
    ap.add_argument("--crop", help="left,top,right,bottom in pixels")
    ap.add_argument("--out", help="file for the cropped region (with --crop)")
    a = ap.parse_args()

    image = a.image
    if a.crop:
        if not a.out:
            sys.exit("--crop needs --out <file.png>")
        box = tuple(int(x) for x in a.crop.split(","))
        with Image.open(image) as im:
            im.crop(box).save(a.out)
        image = a.out
    with Image.open(image) as im:
        width, height = im.size

    result = []
    for g in group(words(image, a.lang)):
        left, top = max(0, g["l"] - a.padding), max(0, g["t"] - a.padding)
        right, bottom = min(width, g["l"] + g["w"] + a.padding), min(height, g["t"] + g["h"] + a.padding)
        result.append({"text": g["text"], "left": left, "top": top, "width": right - left, "height": bottom - top})
    json.dump({"image": image, "width": width, "height": height, "labels": result},
              sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()

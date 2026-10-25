#!/usr/bin/env python3
"""Builds an Anki package (.apkg) from a cards file (JSON) – with basic cards,
cloze cards and image occlusion cards.

Usage:  python3 -I anki_package.py <cards.json> <output.apkg> [--preview <preview.md>]
        --preview writes all cards as Markdown and, for every image occlusion card, a check image with red boxes.

Needs Anki's own Python library (ships with Anki 23.10 or newer on some systems, e.g. the Arch
package "anki"; otherwise: pip install anki). Anki does NOT need to be closed: a separate
collection is built in a temporary folder and only the package is exported.

Structure of the JSON file:
{
  "deck": "Medicine::Anatomy::Muscles",
  "tags": ["anatomy"],                               (optional, for all cards)
  "cards": [
    {"type": "basic", "front": "Question", "back": "<b>Answer</b><br>Why: …"},
    {"type": "cloze", "text": "The {{c1::axillary nerve}} supplies the {{c2::deltoid}}.",
     "extra": "Reason / source"},
    {"type": "occlusion", "image": "/path/figure.png", "header": "What does the figure show?",
     "extra": "Notes p. 12", "mode": "all",             ("all" = everything hidden, guess one; "one" = only one hidden)
     "boxes": [{"left": 120, "top": 40, "width": 90, "height": 22}, …]}   (pixels in the image)
  ]
}
Optional per card: "tags": [...] and "media": ["/path/image.png"] (for <img src="image.png"> in basic/cloze).

The same card (same deck + same question) gets the same ID on every run: importing a new package
of the same material updates existing cards instead of duplicating them (review progress is kept).
Exit code 0 = package built, 1 = errors in the cards file, 3 = Anki's Python library is missing.
"""
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

from PIL import Image, ImageDraw

# Names of the note types in Anki. The note types live in a template collection in the skill folder,
# created once on the first run and copied every time after that. This way they have the same ID in
# every package, and Anki does not create duplicate note types on the second import.
NOTE_TYPES = {
    "basic": ("Basic", "study-anki: Basic"),
    "cloze": ("Cloze", "study-anki: Cloze"),
    "occlusion": ("Image Occlusion", "study-anki: Image Occlusion"),
}
TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template", "collection.anki2")
CLOZE = re.compile(r"\{\{c\d+::.+?\}\}", re.S)


def guid(*parts):
    return hashlib.sha1("\x1f".join(parts).encode()).hexdigest()[:16]


def check(data):
    """Returns (errors, warnings)."""
    errors, warnings, seen = [], [], {}
    if not str(data.get("deck", "")).strip():
        errors.append('"deck" is missing')
    cards = data.get("cards")
    if not isinstance(cards, list) or not cards:
        return errors + ['"cards" is missing or empty'], warnings
    for nr, c in enumerate(cards, start=1):
        kind = c.get("type")
        if kind == "basic":
            front, back = str(c.get("front", "")).strip(), str(c.get("back", "")).strip()
            if not front or not back:
                errors.append(f"card {nr}: front or back is empty")
            if len(back) > 300:
                warnings.append(f"card {nr}: back is {len(back)} characters long – split it?")
            key = "basic:" + front.lower()
        elif kind == "cloze":
            text = str(c.get("text", ""))
            if not CLOZE.search(text):
                errors.append(f"card {nr}: cloze text without {{{{c1::…}}}}")
            elif len(set(re.findall(r"\{\{c(\d+)::", text))) > 5:
                warnings.append(f"card {nr}: more than 5 clozes – better split it?")
            key = "cloze:" + re.sub(r"\s+", " ", text.lower())
        elif kind == "occlusion":
            image = c.get("image", "")
            boxes = c.get("boxes") or []
            if not os.path.isfile(image):
                errors.append(f"card {nr}: image not found: {image}")
                continue
            if not boxes:
                errors.append(f"card {nr}: no boxes")
            if c.get("mode", "all") not in ("all", "one"):
                errors.append(f'card {nr}: "mode" must be "all" or "one"')
            with Image.open(image) as im:
                w_img, h_img = im.size
            for i, b in enumerate(boxes, start=1):
                try:
                    left, top, w, h = (float(b[k]) for k in ("left", "top", "width", "height"))
                except (KeyError, TypeError, ValueError):
                    errors.append(f"card {nr}, box {i}: needs left/top/width/height")
                    continue
                if w <= 0 or h <= 0 or left < 0 or top < 0 or left + w > w_img + 1 or top + h > h_img + 1:
                    errors.append(f"card {nr}, box {i}: outside the image ({w_img}×{h_img})")
            key = "image:" + os.path.basename(image) + json.dumps(boxes, sort_keys=True)
        else:
            errors.append(f'card {nr}: unknown type "{kind}" (basic / cloze / occlusion)')
            continue
        for m in c.get("media", []):
            if not os.path.isfile(m):
                errors.append(f"card {nr}: media file not found: {m}")
        if key in seen:
            warnings.append(f"card {nr}: duplicate (same as card {seen[key]})")
        else:
            seen[key] = nr
    return errors, warnings


def create_template():
    """Creates the template collection with the three note types (first run only)."""
    from anki.collection import Collection

    os.makedirs(os.path.dirname(TEMPLATE), exist_ok=True)
    col = Collection(TEMPLATE)
    col.add_image_occlusion_notetype()
    for old, new in NOTE_TYPES.values():
        m = col.models.by_name(old)
        m["name"] = new
        col.models.update_dict(m)
    col.close()


def build(data, output):
    from anki.collection import Collection, DeckIdLimit, ExportAnkiPackageOptions

    if not os.path.isfile(TEMPLATE):
        create_template()
    tmp = tempfile.mkdtemp(prefix="study-anki-")
    try:
        shutil.copy(TEMPLATE, os.path.join(tmp, "collection.anki2"))
        col = Collection(os.path.join(tmp, "collection.anki2"))
        types = {kind: col.models.by_name(name) for kind, (_, name) in NOTE_TYPES.items()}
        deck = data["deck"].strip()
        did = col.decks.id(deck)
        all_tags = list(data.get("tags", []))
        counts = {"basic": 0, "cloze": 0, "occlusion": 0}
        for c in data["cards"]:
            kind, tags = c["type"], all_tags + list(c.get("tags", []))
            for m in c.get("media", []):
                col.media.add_file(m)
            if kind == "occlusion":
                with Image.open(c["image"]) as im:
                    w_img, h_img = im.size
                oi = ":oi=1" if c.get("mode", "all") == "all" else ""
                parts = []
                for i, b in enumerate(c["boxes"], start=1):
                    left, top, w, h = (float(b[k]) for k in ("left", "top", "width", "height"))
                    parts.append(f"{{{{c{i}::image-occlusion:rect:left={left / w_img:.4f}:top={top / h_img:.4f}"
                                 f":width={w / w_img:.4f}:height={h / h_img:.4f}{oi}}}}}")
                before = set(col.find_notes(""))
                col.add_image_occlusion_note(
                    notetype_id=types[kind]["id"], image_path=c["image"], occlusions="<br>".join(parts),
                    header=c.get("header", ""), back_extra=c.get("extra", ""), tags=tags)
                (nid,) = set(col.find_notes("")) - before
                note = col.get_note(nid)
                note.guid = guid(deck, "image", os.path.basename(c["image"]), json.dumps(c["boxes"], sort_keys=True))
                col.update_note(note)
                col.set_deck([card.id for card in note.cards()], did)
            else:
                note = col.new_note(types[kind])
                if kind == "basic":
                    note["Front"], note["Back"] = c["front"], c["back"]
                    note.guid = guid(deck, "basic", c["front"])
                else:
                    note["Text"], note["Back Extra"] = c["text"], c.get("extra", "")
                    note.guid = guid(deck, "cloze", c["text"])
                note.tags = tags
                col.add_note(note, did)
            counts[kind] += 1
        total = len(col.find_cards(""))
        col.export_anki_package(
            out_path=os.path.abspath(output),
            options=ExportAnkiPackageOptions(with_scheduling=False, with_deck_configs=False,
                                             with_media=True, legacy=False),
            limit=DeckIdLimit(did))
        col.close()
        return counts, total
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def preview(data, path):
    """Writes all cards as Markdown (for proofreading) and, for every image occlusion card, a check
    image with red boxes next to it (<preview>_card<nr>.png)."""
    lines = [f"# Preview: {data['deck']}", ""]
    for nr, c in enumerate(data["cards"], start=1):
        if c["type"] == "basic":
            lines += [f"## Card {nr} (basic)", f"- Front: {c['front']}", f"- Back: {c['back']}"]
        elif c["type"] == "cloze":
            lines += [f"## Card {nr} (cloze)", f"- Text: {c['text']}", f"- Extra: {c.get('extra', '')}"]
        else:
            check_image = f"{os.path.splitext(path)[0]}_card{nr}.png"
            with Image.open(c["image"]) as im:
                im = im.convert("RGB")
                d = ImageDraw.Draw(im)
                for i, b in enumerate(c["boxes"], start=1):
                    left, top, w, h = (float(b[k]) for k in ("left", "top", "width", "height"))
                    d.rectangle([left, top, left + w, top + h], outline="red", width=3)
                    d.text((left + 3, top + 2), str(i), fill="red")
                im.save(check_image)
            lines += [f"## Card {nr} (image occlusion)", f"- Image: {c['image']}", f"- Check image: {check_image}",
                      f"- Header: {c.get('header', '')}", f"- Extra: {c.get('extra', '')}",
                      f"- {len(c['boxes'])} boxes: {c['boxes']}"]
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main(argv):
    if len(argv) not in (3, 5) or (len(argv) == 5 and argv[3] != "--preview"):
        print(__doc__)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        data = json.load(f)
    errors, warnings = check(data)
    for e in errors:
        print("  ERROR  ", e)
    for w in warnings:
        print("  warning", w)
    if errors:
        print(f"{len(errors)} errors – no package built.")
        return 1
    if len(argv) == 5:
        preview(data, argv[4])
        print("Preview:", argv[4])
    try:
        import anki.collection  # noqa: F401
    except ImportError:
        print("Anki's Python library is missing. Install it with: pip install anki\n"
              "(some Linux packages of Anki include it). Until then only CSV works (see SKILL.md).")
        return 3
    counts, total = build(data, argv[2])
    print(f"Package built: {argv[2]}")
    print(f"  {counts['basic']} basic, {counts['cloze']} cloze, "
          f"{counts['occlusion']} image occlusion → {total} cards in deck \"{data['deck']}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

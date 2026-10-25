---
name: study-anki
description: Automatically creates Anki flashcards from study materials (PDFs, slides, lecture notes, study notes, tables) as a ready-to-import Anki package (.apkg) – basic cards, cloze cards and image occlusion cards made from the figures in the materials. First converts the materials to Markdown, writes good cards following the rules of effective learning (one piece of information per card, unambiguous questions, why cards, difference and case cards), using only facts from the materials, has them checked against the sources and builds a package that imports with a double-click. CSV on request. Use when the user says "Anki", "flashcards", "cloze", "image occlusion", "make cards", or invokes /study-anki.
---

# Study Anki – flashcards from your materials

The user studies for exams with **Anki**. You turn their materials into cards they can import with a double-click.
Language of the cards: **if the user writes in the same language as the materials, use that language and don't ask.** If they differ (e.g. the user writes German, the materials are English) or the materials are mixed, **ask at the very start** – as the first question, as soon as you have seen the materials and before anything else – which language they want: the user's language or the language of the materials. Use the multiple-choice question tool if available, otherwise one short line in the chat. Then use that language for all cards (technical terms as in the materials); when adding to an existing deck, keep its language.
Goal: cards that are **short, unambiguous and correct** – and that ask not only for facts but also for the **why**.

Argument (optional): path to a file or folder. If missing, ask for it (or use files the user sends in the chat).

**Running in Claude.ai or Claude Desktop** (files uploaded to the chat instead of a local folder): read the uploaded files directly – Claude can read PDFs itself, so `to_md.sh` is optional. Write every file you create (the .apkg package, check images, CSV) to the outputs folder so the user can download it. Install missing Python packages with `pip` when needed. If a system program can't be installed there, say so briefly and use the fallback described in the step concerned. Install the Anki library with `pip install anki pillow`. If `tesseract` is missing for image occlusion, read the label positions from the image yourself and verify them with the check images. The user imports the downloaded `.apkg` in the Anki app on their computer.

**Output:** by default an **Anki package** `<Material>_Anki.apkg` (all three card types, images included). Only if the user explicitly wants **CSV** (or Anki's Python library is missing, see step 5) write a CSV – then only basic cards are possible (no cloze, no image occlusion).

## Workflow

### 1. Convert the materials to Markdown
```bash
<skill-folder>/to_md.sh "<folder-or-file>"
```
- Reported **scans**: render the pages as images into a temporary folder outside the materials (`pdftoppm -r 130 -png file.pdf <temp-folder>/p`) and **look at them yourself** if you can view images, especially tables. OCR for running text (`tesseract image.png - -l eng`, add languages as needed).
- Never modify or delete the original files.

### 2. Ask briefly (one round, max. 4 questions)
If your environment has a tool for multiple-choice questions, use it; otherwise ask as a short numbered list.
- **Scope:** all of the material (Recommended) / only certain chapters
- **Amount:** compact (exam essentials only) / normal (Recommended) / everything, including details
- **Card types** (several allowed): basic cards (Recommended), cloze (Recommended), image occlusion from the figures (Recommended – only offer it if the material has labelled figures), case cards
- **Content** (several allowed): facts (Recommended), why cards (Recommended), differences/comparisons
If the user skips this or says "just do it": use the recommended options and say which ones you chose.

If the folder contains `<Material>_Quiz-Log.md` (skill `study-quiz`) or `<Material>_Progress.md` (skill `study-tutor`), turn the **weak spots** listed there into cards first and mention it.

### 3. Write the cards – the rules for good cards
**For all card types:**
1. **One piece of information per card.** Not "List all 7 adductors with their innervation", but one card per muscle/fact. Lists only up to about 3–4 items; split longer lists into several cards.
2. **Unambiguous.** There must be only **one** correct answer. Add context: "**Hip:** Which ligament limits extension the most?" instead of "Which ligament limits extension?".
3. **Numbers, exceptions, variants** ("inconstant", "or") must be included – exactly those get tested.
4. **Mnemonics** only on the back / in the extra field and only if they are factually correct (check every initial letter).
5. **Accuracy:** facts only from the materials. Reasoning from general subject knowledge is allowed but must not contradict the materials. If the materials differ from the textbook standard, the materials win (write "according to your notes" if useful).
6. HTML is allowed: `<b>…</b>` for bold, `<br>` for a line break.

**Basic cards** (question → answer) – for assignments, why questions, differences, cases:
- **Short answer**, key statement first and in **bold**, then at most 1–2 sentences of reasoning: `<b>Radial nerve</b><br>Why: it lies in the extensor compartment (dorsal layer).`
- **Why cards:** "Why is brachioradialis supplied by the radial nerve although it flexes?"
- **Difference cards:** "What is the difference between X and Y?" – answer as a short contrast ("X: …<br>Y: …").
- **Case cards:** "A patient can't abduct the arm beyond 90° and has numb skin over the lateral shoulder – which nerve?" – only if it clearly follows from the material.
- **Both directions** for important assignments as **two separate cards** (muscle → nerve and nerve → muscles).
- No yes/no questions.

**Cloze cards** – for definitions, key sentences, processes, sentences with a key term:
- A complete, meaningful sentence; **only the key term** becomes the gap: `The {{c1::axillary nerve}} passes through the {{c2::quadrangular space}}.`
- Every **separate number** (`c1`, `c2` …) = a separate card. Same number = asked together (only if it really belongs together).
- At most about **3 gaps per sentence**, otherwise split. No gaps on filler words or on terms that can be guessed from the grammar.
- For ambiguous gaps add a **hint**: `{{c1::iliofemoral ligament::ligament}}`.
- In the **extra** field: a short reason or the source ("notes p. 14").

**Image occlusion cards** – for labelled figures (anatomy, dental charts, histology, X-rays, instruments, diagrams):
1. **Find figures:** render the pages with figures (`pdftoppm -r 150 -png -f N -l N file.pdf <folder>/page`) and **look at them**. Suitable: figures with **readable labels** of exam-relevant structures. Unsuitable: decorative images, photos without labels, tiny or blurry figures.
2. **Crop + find the labels:**
   ```bash
   python3 -I <skill-folder>/find_labels.py <page.png> --crop left,top,right,bottom --out "<folder>/<Material>_Anki_Images/<name>.png" --lang eng
   ```
   Keep the images in `<Material>_Anki_Images/` next to the materials (so the package can be rebuilt later). Output: all recognised labels with pixel boxes.
3. **Choose what to hide:** only the technical terms, no page numbers, captions or copyright lines. If a label is missing from the list (e.g. slanted or very small), read its box from the image yourself. For figures with numbers + a legend ("1 enamel, 2 dentin …"): hide the **legend entries**, not the numbers.
4. **Mode:** `"all"` (all boxes hidden, one is asked – default, prevents guessing from the neighbours) or `"one"` (only the asked box is hidden – when the other labels should help with orientation).
5. **Header** = what the figure shows ("Longitudinal section of a molar"), **extra** = source ("notes p. 12, fig. 3").
6. At most about 10–12 boxes per figure; with more, split into two cards with different boxes.
7. The images come from the user's materials – for their own use only; don't publish them.

### 4. Write the cards file
Write the cards as JSON into a temporary folder (`<temp-folder>/<Material>_cards.json`):
```json
{
  "deck": "Medicine::Anatomy::Muscles and nerves",
  "tags": ["anatomy"],
  "cards": [
    {"type": "basic", "front": "Which nerve supplies the deltoid?", "back": "<b>Axillary nerve</b>"},
    {"type": "cloze", "text": "The {{c1::axillary nerve}} passes through the {{c2::quadrangular space}}.", "extra": "Notes, section 3"},
    {"type": "occlusion", "image": "/path/Material_Anki_Images/tooth.png", "header": "Tooth, longitudinal section", "extra": "Notes p. 12",
     "mode": "all", "boxes": [{"left": 597, "top": 71, "width": 116, "height": 28}]}
  ]
}
```
- Deck name with `::` for subdecks, matching the subject and material.
- Same deck + same question = same card ID: a later package of the same material **updates** existing cards instead of duplicating them, and review progress is kept. So **keep the deck name** when adding cards.

### 5. Check and build the package
1. **Preview + technical check:**
   ```bash
   python3 -I <skill-folder>/anki_package.py <cards.json> "<folder>/<Material>_Anki.apkg" --preview <temp-folder>/<Material>_preview.md
   ```
   The script checks the cards (empty fields, cloze without a gap, boxes outside the image, duplicates, overly long answers), writes the preview and builds the package. If there are errors, no package is built → fix them and run again.
   **Look at every check image** (`<preview>_card<nr>.png`, red boxes) if you can view images: does every box fully cover its label without hiding neighbours? Otherwise fix the boxes and rebuild.
2. **Content** – a fresh reviewer finds more errors than the author:
   - **If your AI tool supports subagents:** start one (e.g. `study-notes-checker` from [ai-study-notes](https://github.com/blackpaired/ai-study-notes) if installed, otherwise a general subagent) with this task: "Check every card in this preview against the sources: is the answer / the gap correct, is the question unambiguous, are variants/exceptions missing, are mnemonics correct? For image occlusion: does the header match the figure? Do not change any files. Report problems with card numbers and the location in the source." Give it the preview path and all source files (for scans also the page images).
   - **If not:** do this check yourself as a separate, deliberate pass, re-reading the sources instead of relying on memory.
   Apply the justified corrections to the JSON, then run step 1 again.
3. **If Anki's Python library is missing** (exit code 3 / `No module named 'anki'`): tell the user it can be installed with `pip install anki` (some Linux packages of Anki include it), and offer a CSV until then (step 6).

### 6. Only on request: CSV instead of a package
File `<Material>_Anki.csv` in the material's folder, **UTF-8**, basic cards only:
```csv
#separator:Comma
#html:true
#deck:<Subject>::<Topic>
"Hip: Which is the strongest ligament of the human body?","<b>Iliofemoral ligament</b><br>Load capacity approx. 350 kg"
```
- Every row = one card, **both fields in double quotes**, double any quotes inside the text (`""`), no real line breaks (`<br>`).
- The `#` header lines work from Anki 2.1.55. Don't set `#notetype` (its name depends on the Anki interface language).
- Check: `python3 -I <skill-folder>/check_csv.py "<file>.csv"`, then have the content checked as above.

### 7. Wrap-up
Tell the user:
- where the package is and **how many cards** (basic / cloze / image occlusion, per chapter),
- what the check found and what you corrected,
- **How to import:** double-click the `.apkg` (or in Anki *File → Import*) → *Import*. The cards land in the deck from the cards file; the note types are called "study-anki: Basic / Cloze / Image Occlusion".
- Offer to open the package right away (`xdg-open` on Linux, `open` on macOS) – then they only have to click *Import* in Anki.
- Offer: more cards for one chapter, more image occlusions, or checking with `/study-quiz` whether it sits.

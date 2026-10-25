---
name: study-anki
description: Automatically creates Anki flashcards from study materials (PDFs, slides, lecture notes, study notes, tables) as a CSV in the format "question","answer" that can be imported into Anki directly. First converts the materials to Markdown, writes good cards following the rules of effective learning (one piece of information per card, unambiguous questions, why cards, difference and case cards), using only facts from the materials, has them checked against the sources and validates the CSV technically. Use when the user says "Anki", "flashcards", "make cards", "cards for spaced repetition", or invokes /study-anki.
---

# Study Anki – flashcards from your materials

The user studies for exams with **Anki**. You turn their materials into cards they can import with one click.
Language of the cards: **if the user writes in the same language as the materials, use that language and don't ask.** If they differ (e.g. the user writes German, the materials are English) or the materials are mixed, **ask at the very start** – as the first question, as soon as you have seen the materials and before anything else – which language they want: the user's language or the language of the materials. Use the multiple-choice question tool if available, otherwise one short line in the chat. Then use that language for all cards (technical terms as in the materials); when adding cards to an existing CSV, keep its language.
Goal: cards that are **short, unambiguous and correct** – and that ask not only for facts but also for the **why**.

Argument (optional): path to a file or folder. If missing, ask for it (or use files the user sends in the chat).

## Workflow

### 1. Convert the materials to Markdown
```bash
<skill-folder>/to_md.sh "<folder-or-file>"
```
- Reported **scans**: render the pages as images into a temporary folder outside the materials (`pdftoppm -r 130 -png file.pdf <temp-folder>/p`) and **look at them yourself** if you can view images, especially tables. OCR for running text (`tesseract image.png - -l eng`, add languages as needed).
- Never modify or delete the original files.

### 2. Ask briefly (one round, max. 3 questions)
If your environment has a tool for multiple-choice questions, use it; otherwise ask as a short numbered list.
- **Scope:** all of the material (Recommended) / only certain chapters
- **Amount:** compact (exam essentials only) / normal (Recommended) / everything, including details
- **Card types** (several allowed): facts (Recommended), why cards (Recommended), differences/comparisons, cases/applications
If the user skips this or says "just do it": use the recommended options and say which ones you chose.

If the folder contains `<Material>_Quiz-Log.md` (skill `study-quiz`) or `<Material>_Progress.md` (skill `study-tutor`), turn the **weak spots** listed there into cards first and mention it.

### 3. Write the cards – the rules for good cards
1. **One piece of information per card.** Not "List all 7 adductors with their innervation", but one card per muscle/fact. Lists only up to about 3–4 items; split longer lists into several cards.
2. **Unambiguous question.** There must be only **one** correct answer. Put context at the front: "**Hip:** Which ligament limits extension the most?" instead of "Which ligament limits extension?".
3. **Short answer.** Key statement first, in **bold**. Then at most 1–2 sentences of reasoning, e.g. `<b>Radial nerve</b><br>Why: it lies in the extensor compartment (dorsal layer).`
4. **Why cards** (if chosen): "Why is brachioradialis supplied by the radial nerve although it flexes?" – the answer explains the connection in 1–2 sentences.
5. **Difference cards:** "What is the difference between X and Y?" – answer as a short contrast ("X: …<br>Y: …").
6. **Case cards** (if chosen): "A patient can't abduct the arm beyond 90° and has numb skin over the lateral shoulder – which nerve?" – only if it clearly follows from the material.
7. **Both directions** for important assignments as **two separate cards** (muscle → nerve and nerve → muscles), not as a reverse card.
8. **Numbers, exceptions, variants** ("inconstant", "or") must be included – exactly those get tested.
9. **Mnemonics** only on the back and only if they are factually correct (check every initial letter).
10. **No yes/no questions**, no cloze texts where the answer can be guessed from the grammar.

**Accuracy:** facts only from the materials. Reasoning from general subject knowledge is allowed but must not contradict the materials. If the materials differ from the textbook standard, the materials win (write "according to your notes" on the card if useful).

### 4. CSV format (exactly like this, so the import works)
File: `<Material>_Anki.csv` in the material's folder, **UTF-8**. If the file already exists, ask whether to add to it or replace it; when adding, no duplicate fronts.

```csv
#separator:Comma
#html:true
#deck:<Subject>::<Topic>
"Hip: Which is the strongest ligament of the human body?","<b>Iliofemoral ligament</b><br>Load capacity approx. 350 kg"
"Which nerve supplies the deltoid?","<b>Axillary nerve</b>"
```
- **Every row = one card**: `"question","answer"` – **both fields always in double quotes**, separated by a comma.
- **Double any quotes inside the text**: `"What does ""passive standing"" mean?"`.
- **No real line breaks** inside a field; use `<br>` instead. Bold with `<b>…</b>`.
- The `#` header lines tell Anki the separator, that HTML is allowed and the target deck (works from Anki 2.1.55; for older versions delete these 3 lines). Don't set `#notetype` – its name depends on the Anki interface language ("Basic", "Einfach" …); without it Anki uses the default note type.
- Deck name with `::` for subdecks, matching the subject (e.g. `Medicine::Anatomy::Muscles and nerves`).

### 5. Check
1. **Technically** – always:
   ```bash
   python3 -I <skill-folder>/check_csv.py "<folder>/<Material>_Anki.csv"
   ```
   Fix errors, look at warnings (duplicates, too long) and resolve them sensibly (split long cards).
2. **Content** – a fresh reviewer finds more errors than the author:
   - **If your AI tool supports subagents:** start one (e.g. `study-notes-checker` from [ai-study-notes](https://github.com/blackpaired/ai-study-notes) if installed, otherwise a general subagent) with this task: "Check every card (row) of this Anki CSV against the sources: is the answer correct, is the question unambiguous, are variants/exceptions missing, are mnemonics correct? Do not change any files. Report problems with row numbers and the location in the source." Give it the CSV path and all source files (for scans also the page images).
   - **If not:** do this check yourself as a separate, deliberate pass, re-reading the sources instead of relying on memory.
   Apply the justified corrections, then run step 1 again.

### 6. Wrap-up
Tell the user:
- where the CSV is and **how many cards** (split by type/chapter),
- what the check found and what you corrected,
- **How to import:** open Anki → *File → Import* → choose the CSV → check that "Field 1 → Front" and "Field 2 → Back" are mapped and HTML is allowed → *Import*. The cards land in the deck from the header automatically.
- Offer: more cards on one chapter, additional case cards, or checking with `/study-quiz` whether it sits.

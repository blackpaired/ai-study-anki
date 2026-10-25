# AI Study Anki

A skill for **terminal AI agents** (AI coding agents / agentic CLIs such as Claude Code, Codex CLI, Gemini CLI, OpenCode …) that turns your study materials (PDFs, lecture notes, slides, even scans) into **Anki flashcards**. You get a CSV file in the simple format `"question","answer"` that you can import into Anki with one click.

## What you get

- **Good cards, not just many cards**: one piece of information per card, unambiguous questions with context, short answers with the key statement in bold.
- **Why cards** that ask for the connection, not only the fact.
- Optional **difference cards** and **case cards**.
- **Variants, exceptions and numbers** from your materials are included, because exactly those get tested.
- **Weak spots first**: if you used [ai-study-quiz](https://github.com/blackpaired/ai-study-quiz) or [ai-study-tutor](https://github.com/blackpaired/ai-study-tutor) before, the weak spots from their logs become cards first.
- **Two checks**: a reviewer pass compares every card with your sources, and `check_csv.py` makes sure the CSV imports cleanly (2 columns, no empty fields, no duplicates, no overly long answers).
- **Automatic conversion** of your materials to Markdown (`to_md.sh`), including detection of scanned PDFs.

## The CSV format

```csv
#separator:Comma
#html:true
#deck:Medicine::Anatomy::Muscles and nerves
"Which nerve supplies the deltoid?","<b>Axillary nerve</b>"
"Why is brachioradialis supplied by the radial nerve although it flexes?","<b>It developed from the dorsal (extensor) layer.</b><br>Innervation shows origin, not function."
```

- One row per card, both fields in double quotes, separated by a comma.
- `<b>` and `<br>` for formatting (HTML is enabled by the header).
- The header lines set the separator, HTML and the target deck (Anki 2.1.55 or newer). For older Anki versions, delete the three `#` lines.

## How it works

1. **Convert:** all files in your folder are converted to `.md` with `markitdown` (fallback: `pandoc` for Word files). For scanned pages, the AI looks at rendered page images directly or runs OCR.
2. **Ask:** 3 quick questions: scope, amount and card types.
3. **Write:** `<Material>_Anki.csv` is created in your materials folder.
4. **Check:** content check against the sources + technical CSV check; justified corrections are applied.
5. **Import:** in Anki: *File → Import* → choose the CSV → *Import*.

## Requirements

- A terminal AI agent that can read files and run shell commands. Skill and subagent support is a plus, but not required.
- Linux or macOS (Windows via WSL)
- Python 3 (for the CSV check)
- [`markitdown`](https://github.com/microsoft/markitdown): `pipx install 'markitdown[all]'`
- `poppler`: `sudo pacman -S poppler` / `sudo apt install poppler-utils` / `brew install poppler`
- Optional: [`pandoc`](https://pandoc.org) (fallback for Word files), `tesseract` plus the language packs you need (for scans)
- [Anki](https://apps.ankiweb.net) 2.1.55 or newer recommended

## Installation

```bash
git clone https://github.com/blackpaired/ai-study-anki.git
cd ai-study-anki
bash install.sh
```

By default the script copies the skill to `~/.claude/skills/study-anki/`. Claude Code and some other tools read skills from there (`SKILL.md` is an open format used by several AI agents). If your AI tool loads skills from a different folder, pass it:

```bash
bash install.sh ~/.my-ai-tool/skills
```

The script also shows which required programs are missing.

To install by hand instead:

```bash
mkdir -p <skills-folder>
cp -r skills/study-anki <skills-folder>/
chmod +x <skills-folder>/study-anki/to_md.sh <skills-folder>/study-anki/check_csv.py
```

Then restart your AI agent.

**Tool without skill support?** It still works: tell the AI *"follow the instructions in `<skills-folder>/study-anki/SKILL.md` for ~/Documents/Physiology/"*.

## Usage

Put the materials for one exam into one folder, then in your AI agent type:

```
/study-anki ~/Documents/Physiology/
```

Plain language works too: *"make Anki cards from ~/Documents/Physiology"*, or *"Anki cards only for chapter 3, with case cards"*.

Some useful follow-ups:

- "add more cards for chapter 5"
- "make the answers shorter"
- "add case cards"

### Checking a CSV only

```bash
python3 -I <skills-folder>/study-anki/check_csv.py ~/Documents/Physiology/Heart_Anki.csv
```

## Works well with

- [ai-study-notes](https://github.com/blackpaired/ai-study-notes): study notes that explain the connections, exported as a PDF.
- [ai-study-tutor](https://github.com/blackpaired/ai-study-tutor): teaches you the material step by step.
- [ai-study-quiz](https://github.com/blackpaired/ai-study-quiz): quizzes you like an oral examiner.

## Important

- Facts come from your materials. Reasoning and mnemonics partly come from general knowledge. **If anything contradicts your lecture or textbook, your lecture wins.**
- The content check catches a lot, but it is not guaranteed to catch everything. If a card looks wrong, fix it in Anki or ask the AI.
- Every run uses your AI usage (tokens / plan limits). Large materials mean more usage.

---

*This repo was created with the help of Claude Opus 5.5.*

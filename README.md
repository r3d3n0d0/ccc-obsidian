# Catechism notes for Obsidian

Save the English *Catechism of the Catholic Church* from [vatican.va](https://www.vatican.va/archive/ENG0015/_INDEX.HTM) as one Obsidian note per section, with links you can point at any numbered paragraph.

This repository is the program only. It downloads the public pages into a folder you choose. The text is copyright [Libreria Editrice Vaticana](https://www.vatican.va/archive/ENG0015/_INDEX.HTM): keep the notes in a private vault and do not publish them as your own work.

## What you get

A folder of 374 section notes plus an index, numbered so Obsidian's A-to-Z sort matches the book:

```text
00 - Catechism.md
01 - PROLOGUE/
    00 - PROLOGUE.md
    01 - I. The life of man - to know and love God.md
02 - PART ONE - THE PROFESSION OF FAITH/
    01 - SEC. ONE I BELIEVE - WE BELIEVE/
        01 - CH. ONE MAN'S CAPACITY FOR GOD/
            01 - I. The Desire for God.md
            05 - IN BRIEF.md
ccc-paragraphs.json
```

A section note looks like this (the paragraph is a stand-in, not the Vatican text):

```markdown
---
aliases: ["CCC 27", "CCC 28", "CCC 29", "CCC 30"]
---
# I. The Desire for God

[[00 - Catechism|Catechism]] | [[01 - PROLOGUE/00 - PROLOGUE|← PROLOGUE]] | [[...|II. Ways of Coming to Know God →]] | [Vatican](https://www.vatican.va/archive/ENG0015/__P9.HTM)
***

*PART ONE: THE PROFESSION OF FAITH > SECTION ONE "I BELIEVE" - "WE BELIEVE" > CHAPTER ONE MAN'S CAPACITY FOR GOD*

[CCC 27] Paragraph text from the Vatican page. ^ccc-27

[^1]: A footnote citation from the Vatican page, such as Jn 17:3.
***
```

`^ccc-27` is a block ID. Obsidian hides it in reading view; it is what a paragraph link points at.

## Install

You need Python 3.9 or newer, `curl`, and Beautiful Soup.

```bash
git clone https://github.com/r3d3n0d0/ccc-obsidian.git
cd ccc-obsidian
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scrape_ccc.py --help
```

On Windows, use `py -3 -m venv .venv` and `.venv\Scripts\python`. `pip install .` also works; the command is then `ccc-obsidian`.

## Use

Try a few pages in a trial folder first. `--limit` leaves the rest out of the index and links, so keep it out of your vault:

```bash
.venv/bin/python scrape_ccc.py --limit 3 -o /tmp/ccc-trial
```

When the notes look right, write the full copy into a folder inside your vault. A full run takes a few minutes.

```bash
.venv/bin/python scrape_ccc.py -o ~/Documents/MyVault/Catechism --save-output
```

Later runs can omit `-o`. To pick up pages that failed, run again with `--skip-existing`, which downloads only the missing notes and refreshes the links in the rest. To re-download a page whose old note is still there, run without it.

**Which folder is used.** The first of these that is set: `-o`, the `CCC_OUTPUT` environment variable, or the folder saved by `--save-output` (or by answering the question the program asks when nothing is set). The saved path lives in `~/.config/ccc-obsidian/output-dir`, or `%APPDATA%\ccc-obsidian\output-dir` on Windows. `--where` prints it and `--forget-output` clears it. The program warns before writing to a folder that is not inside a vault.

## Linking

### Link to a paragraph

Obsidian resolves `[[...]]` by file name, not by alias. The `CCC 27` aliases let the quick switcher find a section, but a hand-typed `[[CCC 27]]` is an empty link. A paragraph link names the note and the block ID:

```markdown
[[03 - III. The Final Purification, or Purgatory#^ccc-1030|CCC 1030]]
```

Clicking it opens the section at that paragraph, and hovering previews only that paragraph. With `!` in front, it embeds the paragraph's text. A numbered paragraph that continues in a quotation below it shows only the numbered part.

You do not have to look up the note. Every run writes `ccc-paragraphs.json` next to the index, with a ready link for each number:

```json
{
 "1030": {
  "file": "02 - PART ONE - THE PROFESSION OF FAITH/.../03 - III. The Final Purification, or Purgatory.md",
  "target": "03 - III. The Final Purification, or Purgatory#^ccc-1030",
  "link": "[[03 - III. The Final Purification, or Purgatory#^ccc-1030|CCC 1030]]"
 }
}
```

`target` is the file name, or the path from the Catechism folder when the name repeats (as "IN BRIEF" does). A script, template, or AI assistant can read this file to write correct links. To insert links by hand, see [Obsidian scripts](#obsidian-scripts).

### Add links to notes you already have

`--relink` adds missing block IDs to the notes in the folder and rewrites `ccc-paragraphs.json`. It downloads nothing and does not need Beautiful Soup. It changes only `[CCC N]` lines and footnote lines, and a second run changes nothing. A normal run does the same at the end.

```bash
.venv/bin/python scrape_ccc.py --relink
```

### Bible links in footnotes (optional)

This program does not download or include a Bible. `--bible` is only for a vault that already has one, as one note per chapter. Without it, footnotes stay plain text. The Bible notes are read, never changed.

```bash
.venv/bin/python scrape_ccc.py --relink --bible ~/Documents/MyVault/Bible
```

A footnote such as `Cf. Jn 6:39; 10:28` then becomes:

```markdown
Cf. [[Jn-06#The Bread from Heaven|Jn 6:39]]; [[Jn-10#Jesus Is Rejected by the Jews|10:28]]
```

What the Bible notes need:

- One note per chapter, anywhere under the folder. Subfolders are fine.
- An `aliases` entry such as `John 6`, or a file name such as `Jn-06.md`.
- Optional: `##` headings and verse markers such as `[39]`. With them, a link opens the section containing the verse; without them, the chapter.

Book names follow common English usage (`Psalms` or `Psalm`, `Song of Songs` or `Song of Solomon`). Add others to `BIBLE_BOOKS` in `scrape_ccc.py`. Both the Vatican abbreviations (`Gen`, `1 Pet`) and shorter forms (`Gn`, `1 Pt`) are recognized, as are misreadings in the footnotes such as `I Cor` and `In 8:32` for John.

Left as text: chapters the folder lacks, citations without a verse (`Ps 51`), and non-biblical sources (`DS 1820`). The link opens your translation, so the wording may differ from the Catechism's quotation.

## Obsidian scripts

Two [QuickAdd](https://github.com/chhoumann/quickadd) user scripts are in `obsidian/`:

- `search-catechism.js` asks for words and opens search limited to the Catechism folder. `divine mercy` searches for the phrase; `mercy OR merciful` for either word.
- `insert-ccc-link.js` asks for a paragraph number and inserts its link from `ccc-paragraphs.json`. `1030, 1032` and `1030-1032` insert several.

In both, text selected in the editor fills the prompt. To set one up:

1. Install QuickAdd and turn it on.
2. Copy the script into the vault, for example `scripts/insert-ccc-link.js`, and set `FOLDER` at the top to the vault-relative path of the Catechism folder.
3. In QuickAdd, add a Macro choice, add the script under **User scripts**, and turn on the choice's command (the lightning bolt).
4. Optionally bind a hotkey under Settings → Hotkeys.

After you change a script, reload Obsidian.

## Options

| Option | What it does |
| --- | --- |
| `-o`, `--output FOLDER` | Write here for this run. |
| `--save-output` | Remember `--output` for later runs on this computer. |
| `--where` | Print the folder that would be used, then exit. |
| `--forget-output` | Delete the saved folder. The next run asks again. |
| `--link NOTE` | Link this vault note from the index. Repeat for more than one. |
| `--dry-run`, `-n` | Fetch the index and list file names. Download no sections. |
| `--limit N` | Download only the first N sections. Use a trial folder. |
| `--skip-existing` | Skip sections whose note exists. Still refresh links. |
| `--relink` | Add block IDs (and Bible links with `--bible`) to the notes on disk and rewrite `ccc-paragraphs.json`. No downloads. |
| `--bible FOLDER` | Optional. Your own Bible chapter notes; none is included. |
| `CCC_OUTPUT` | Environment variable. Used when `-o` is absent. |

## If a run fails

- "No table of contents found" means the Vatican markup at `https://www.vatican.va/archive/ENG0015/_INDEX.HTM` may have changed.
- `bs4 not installed` means Beautiful Soup is missing from the virtual environment you are using.
- `curl` has to be on your `PATH`.

The program exits with status 1 if any page failed, and its summary says whether to re-run with or without `--skip-existing`.

## Note format

- **Numbered names.** Siblings are numbered `01`, `02`, … in table-of-contents order so the file list matches the book. A heading with children becomes a folder, and its own page is `00 - Title.md` inside it.
- **Short labels.** A leading `CHAPTER`, `SECTION`, `Article`, or `Paragraph` becomes `CH.`, `SEC.`, `Art.`, or `Para.` in file names. The heading inside the note keeps the full Vatican title.
- **Safe file names.** Characters Obsidian rejects are removed, and a colon becomes ` - `.
- **Navigation.** Previous and next follow the table of contents and skip notes that do not exist. Links use the folder path when a name repeats.
- **Body.** `[CCC N]` starts each numbered paragraph. Short lines without a final period become `####` headings, indented paragraphs become quotations, and footnotes become `[^N]`.
- **Downloads.** The program pauses 0.35 seconds between pages and retries failures up to three times.

## License

The program is [MIT](LICENSE). That license covers this code, not the Catechism, whose text remains copyright Libreria Editrice Vaticana.

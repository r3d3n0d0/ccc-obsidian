# Catechism notes for Obsidian

Save the English *Catechism of the Catholic Church* from [vatican.va](https://www.vatican.va/archive/ENG0015/_INDEX.HTM) as one Obsidian note per section.

This repository is the program only. It does not contain the text of the Catechism. The program downloads the public pages into a folder you choose. That text is copyright [Libreria Editrice Vaticana](https://www.vatican.va/archive/ENG0015/_INDEX.HTM). Keep the notes in a private vault. Do not publish the generated notes as your own work.

You choose the folder. The program does not look for a vault and does not ship with anyone's path in it.

## What you get

A folder of Markdown notes that follows the table of contents. Obsidian sorts file names from A to Z, so each sibling is numbered and the list matches the book.

```text
00 - Catechism.md
01 - PROLOGUE/
    00 - PROLOGUE.md
    01 - I. The life of man - to know and love God.md
    02 - II. Handing on the Faith - Catechesis.md
02 - PART ONE - THE PROFESSION OF FAITH/
    01 - SEC. ONE I BELIEVE - WE BELIEVE/
        01 - CH. ONE MAN'S CAPACITY FOR GOD/
            01 - I. The Desire for God.md
            05 - IN BRIEF.md
```

A full run writes 374 section notes plus the index. It pauses between requests, so expect a few minutes.

A section note looks like this. The paragraph below is a stand-in, not the Vatican text:

```markdown
---
aliases: ["CCC 27", "CCC 28", "CCC 29", "CCC 30"]
---
# I. The Desire for God

[[00 - Catechism|Catechism]] | [[01 - PROLOGUE/00 - PROLOGUE|← PROLOGUE]] | [[...|II. Ways of Coming to Know God →]] | [Vatican](https://www.vatican.va/archive/ENG0015/__P9.HTM)
***

*PART ONE: THE PROFESSION OF FAITH > SECTION ONE "I BELIEVE" - "WE BELIEVE" > CHAPTER ONE MAN'S CAPACITY FOR GOD*

**27** Paragraph text from the Vatican page.

[^1]: A footnote citation from the Vatican page.
***
```

The heading and the link label keep the Vatican title. The file name is the shortened, numbered form.

## Install

You need Python 3.9 or newer, `curl`, and Beautiful Soup.

```bash
git clone https://github.com/r3d3n0d0/ccc-obsidian.git
cd ccc-obsidian
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scrape_ccc.py --help
```

On Windows, use `py -3 -m venv .venv` and `.venv\Scripts\python scrape_ccc.py --help`. `curl` is included with Windows 10 and later.

`pip install .` also works. After that, the command is `ccc-obsidian`.

## Choose a folder

The program has no default folder. It uses the first of these that is set:

1. `--output` or `-o` for this run only
2. The `CCC_OUTPUT` environment variable
3. The folder saved last time you answered the question

If none of those is set, and you are at a terminal, it asks. It does not guess.

```text
Where should the notes be written?

Choose a folder inside your Obsidian vault. It is created if needed.
Example: ~/Documents/MyVault/Catechism
```

Point it at a folder inside the vault, the same way you would create any other folder of notes. `Catechism` is a reasonable name. Put it next to your other reference notes, or wherever you want it. The program creates the folder.

It looks upward for a `.obsidian` directory. If it does not find one, it says so and asks you to confirm. That warning is expected for a trial in `/tmp`. Say yes only when you mean to write outside a vault.

The answer is stored on your computer, not in this repository:

| System | Saved path |
| --- | --- |
| Linux and macOS | `~/.config/ccc-obsidian/output-dir` |
| Windows | `%APPDATA%\ccc-obsidian\output-dir` |

`XDG_CONFIG_HOME` is honored on Linux and macOS. Do not commit that file. To see it, run `--where`. To clear it, run `--forget-output`.

### Try a few pages first

Use a trial folder. `--limit` rewrites the index so the sections you did not download appear as plain titles. You do not want that rewrite in the vault.

```bash
.venv/bin/python scrape_ccc.py --limit 3 -o /tmp/ccc-trial
```

Open `/tmp/ccc-trial/00 - Catechism.md` and one section note. When the shape looks right, run the full copy into the vault.

### Write into the vault

```bash
.venv/bin/python scrape_ccc.py \
  -o ~/Documents/MyVault/Catechism \
  --save-output
```

`--save-output` remembers that folder. The next run can omit `-o`.

If the vault already has a note the index should point at, name it with `--link`. Repeat the flag for more than one note. The name is the note's title, without brackets.

```bash
.venv/bin/python scrape_ccc.py -o ~/Documents/MyVault/Catechism --link Bible
```

Without `--link`, the index does not point at any other note. There is no assumed Bible folder.

### Run it again

```bash
.venv/bin/python scrape_ccc.py --skip-existing
```

This uses the saved folder. It does not download a section whose note is already there. It does refresh previous/next links, and it rewrites the index. Use it to pick up pages that failed the first time.

If a page failed and the old note is still on disk, `--skip-existing` will not replace it. Run again without `--skip-existing` to download that page fresh.

```bash
.venv/bin/python scrape_ccc.py --where
.venv/bin/python scrape_ccc.py --forget-output
```

## Why the notes look like this

### Numbers, so the file list matches the book

Obsidian sorts names from A to Z. It does not understand "two" before "three", or "Article 2" before "Article 10".

Without a prefix, the top of the folder would be Part Four, then Part One, then Part Three, then Part Two, then the Prologue. Chapter Three would sit above Chapter Two. Article 10 would sit above Article 4.

Each group of siblings is numbered `01`, `02`, `03` in table-of-contents order. Two digits are enough. The widest group in the book is well under 100.

A part, section, chapter, or article that has children becomes a folder. If that heading also has its own page, the note is `00 - Title.md` inside the folder, so the section itself stays above its children. The index uses the same idea: `00 - Catechism.md`.

Part One and Part Four are headings on the Vatican site with no page of their own. Those folders have no `00` note.

### Short labels, so the long titles are readable

`CHAPTER`, `SECTION`, `Article`, and `Paragraph` begin a large share of the names. Spelling them out pushes the real title off the edge of the file list. In the file and folder name they become `CH.`, `SEC.`, `Art.`, and `Para.`.

`PART` and `PROLOGUE` stay. They are short, and they are the landmarks at the top of the book.

Only the leading structural word is shortened. "I BELIEVE IN JESUS CHRIST, THE ONLY SON OF GOD" is still there. The heading inside the note is the Vatican line, including colons and quotation marks. A wikilink shows that same line. The short name is only for the file list.

### File names Obsidian will accept

Obsidian rejects these characters in a note name: `\ / : * ? " < > | # ^ [ ]`.

A colon becomes ` - `, so "PART ONE: THE PROFESSION OF FAITH" is stored as `PART ONE - THE PROFESSION OF FAITH`. Quotation marks and question marks are removed from the file name. `IV. How Can We Speak about God?` is stored as `IV. How Can We Speak about God`. The heading in the note still has the question mark.

Titles contain periods (`I.`, `CH.`, `Para. 1.`). The program adds `.md` as plain text. Treating the last period as a file extension would save `I. The Desire for God` as `I.md`.

### Links that point at notes you actually have

The path in a wikilink is unique. The label is the title you want to read:

```markdown
[[02 - CH. ONE MAN'S CAPACITY FOR GOD/05 - IN BRIEF|IN BRIEF]]
```

Many sections are named "IN BRIEF". The folder path tells them apart, so the alias is the title, not a second copy of the path.

Previous and next follow the table of contents. They do not follow the Previous and Next controls on the Vatican page, because those can disagree with the outline. An arrow points only at a note that exists. If a download failed, or `--limit` stopped early, the arrow steps over the gap to the nearest note that was written. A later run rewrites the arrows once the missing note is there. A page with no body text is left out of the index and out of the arrows.

The index has the alias `Catechism`, so `[[Catechism]]` opens it from anywhere in the vault. Each numbered paragraph is also an alias, such as `CCC 27`, so the quick switcher can jump to it. The property name is `aliases`, which is what Obsidian recognizes.

### Headings, quotations, and footnotes

The Vatican pages are old HTML. The script keeps the reading order and turns the markup into Markdown.

- A paragraph number at the start of a paragraph becomes bold: `**27**`.
- A short unnumbered line with no final period, such as "Above all - Charity" or "Part One: the Profession of Faith", becomes a `####` heading. A real sentence ends with `.`, `?`, or `!` and stays a paragraph.
- A paragraph the Vatican indented, and an unnumbered paragraph that follows a line ending in a colon, becomes a blockquote.
- Footnote markers become `[^1]`, with the citation under the body.

The breadcrumb under the title comes from the page's outline trail, not from the bold running headers. Those headers repeat the section name and are dropped.

### A polite download

The pages live on vatican.va. The program waits 0.35 seconds after each section page. `curl` retries a timeout, a refused connection, and HTTP 408, 429, and server errors, up to three times. Pages are decoded as Latin-1, which is the charset those pages declare.

Notes are written after the downloads for that run, so previous/next can see which files succeeded. The program exits with status 1 if any page failed. The summary tells you whether to re-run with `--skip-existing` (the note was never written) or without it (an older note is still there and was left unchanged).

## Options

| Option | What it does |
| --- | --- |
| `-o`, `--output FOLDER` | Write here for this run. |
| `--save-output` | Remember `--output` for later runs on this computer. |
| `--where` | Print the folder that would be used, then exit. |
| `--forget-output` | Delete the saved folder. The next run asks again. |
| `--link NOTE` | Link this vault note from the index. Repeat for more than one. |
| `--dry-run`, `-n` | Fetch the index and list file names. Do not download sections. |
| `--limit N` | Download only the first N sections. Point `-o` at a trial folder. |
| `--skip-existing` | Skip a download when the note is already there. Still refresh links. |
| `CCC_OUTPUT` | Environment variable. Used when `-o` is absent. |

`--limit` and a failed download both leave later sections out of the links until a run downloads them. That is why a partial run belongs in a trial folder.

## If a run fails

The index page is `https://www.vatican.va/archive/ENG0015/_INDEX.HTM`. If the program says no table of contents was found, the Vatican markup may have changed.

`curl` has to be on your `PATH`. The message `bs4 not installed` means Beautiful Soup is missing. Install it with `pip install -r requirements.txt` inside the same virtual environment you use to run the script.

## License

The program is [MIT](LICENSE). That license covers this code. It does not cover the Catechism. The text you download remains copyright Libreria Editrice Vaticana.

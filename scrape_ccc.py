#!/usr/bin/env python3
"""
Save the Catechism of the Catholic Church from www.vatican.va as Obsidian notes.

One note per table-of-contents page, plus an index named 00 - Catechism.md.
You choose the folder. Nothing in this program points at a particular vault.

  python3 scrape_ccc.py --limit 3 -o /tmp/ccc-trial
  python3 scrape_ccc.py -o ~/Documents/MyVault/Catechism
  python3 scrape_ccc.py --skip-existing

The first run with no --output asks where to write and remembers the answer
on this computer only. See README.md for the how and the why.

The pages are copyright Libreria Editrice Vaticana. This is for a private vault.
There is a short pause between requests.
"""
import argparse
import html as html_lib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("bs4 not installed — run: pip install beautifulsoup4")
    sys.exit(1)

BASE_URL = "https://www.vatican.va/archive/ENG0015/"
INDEX_URL = BASE_URL + "_INDEX.HTM"
BOOK = "Catechism of the Catholic Church"
INDEX_STEM = "00 - Catechism"
PAUSE = 0.35
RETRIES = 3
RETRY_DELAY = 2

# IntraText links look like <a href=__P9.HTM> with no quotes.
PARA_RE = re.compile(r"^(\d{1,4})\s+(.*)$", re.S)


def clean(text):
    return " ".join((text or "").split()).strip()


def fs_name(title):
    """Source title made safe for a file or directory name.

    Obsidian rejects \\ / : * ? \" < > | # ^ [ ] in note names. The words
    stay in the order they have on vatican.va.
    """
    name = clean(title).replace(":", " - ")
    name = re.sub(r"[\\\\/*?\"<>|#^\[\]]", "", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    name = re.sub(r"(?: - ){2,}", " - ", name)
    return name or "Untitled"


# Leading structural words only. The rest of the Vatican title stays.
_ABBREV = (
    (re.compile(r"^CHAPTER\b", re.I), "CH."),
    (re.compile(r"^SECTION\b", re.I), "SEC."),
    (re.compile(r"^ARTICLE\b", re.I), "Art."),
    (re.compile(r"^PARAGRAPH\b", re.I), "Para."),
)


def outline_name(title):
    """File or folder name: shorten the structural word, then make it safe."""
    name = clean(title)
    for pattern, short in _ABBREV:
        name, count = pattern.subn(short, name, count=1)
        if count:
            break
    return fs_name(name)


def assign_paths(nodes, parent=Path()):
    """Number siblings in outline order and shorten structural words.

    Obsidian sorts the file list from A to Z. The prefix 01, 02, ... makes
    that sort follow the Vatican table of contents. A heading with children
    becomes a directory. Its own page, if it has one, is 00 - Title.md
    inside that directory so the section note sorts first.
    """
    for number, node in enumerate(nodes, start=1):
        name = outline_name(node["title"])
        label = f"{number:02d} - {name}"
        children = node.get("children") or []
        if children:
            folder = parent / label
            node["rel"] = folder / f"00 - {name}" if node.get("href") else None
            assign_paths(children, folder)
        else:
            node["rel"] = parent / label if node.get("href") else None


def link_target(node):
    """Wikilink path for a note, relative to the Catechism directory."""
    rel = node.get("rel")
    if rel is None:
        return fs_name(node["title"])
    return rel.as_posix()


def note_file(rel):
    """Markdown path for an outline entry.

    Add the extension as text. Path.with_suffix() treats the last period in
    the title as an extension, so "I. The Desire for God" would become "I.md".
    """
    return rel.parent / f"{rel.name}.md"


def normalize_href(href):
    """Return __Pxx.HTM, or '' when href is not a section page."""
    if not href:
        return ""
    name = href.split("#", 1)[0].strip().split("/")[-1]
    match = re.match(r"^__P([0-9A-Za-z]+)(?:\.HTM)?$", name, re.I)
    if not match:
        return ""
    return f"__P{match.group(1)}.HTM"


def wikilink(target, display):
    display = clean(display).replace("|", "/").replace("[", "(").replace("]", ")")
    if not display or display == target:
        return f"[[{target}]]"
    return f"[[{target}|{display}]]"


def fetch(url, timeout=30):
    """GET a page with curl. Vatican pages declare charset=iso-8859-1.

    curl retries timeouts, refused connections, and HTTP 408, 429, and 5xx.
    --max-time is reset on each attempt, so the subprocess limit covers all of them.
    """
    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-L", "--compressed",
                "--max-time", str(timeout),
                "--retry", str(RETRIES),
                "--retry-delay", str(RETRY_DELAY),
                "--retry-connrefused",
                "-A", "ccc-obsidian/1.0",
                "-w", "\n%{http_code}",
                url,
            ],
            capture_output=True,
            timeout=(timeout + RETRY_DELAY) * (RETRIES + 1) + 5,
        )
    except FileNotFoundError:
        print("ERROR: curl is not installed")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"  timed out: {url}")
        return None
    if result.returncode != 0:
        err = result.stderr.decode("iso-8859-1", errors="replace").strip()
        print(f"  fetch failed ({result.returncode}): {err}")
        return None
    body, sep, status = result.stdout.rpartition(b"\n")
    if not sep:
        print(f"  empty response for {url}")
        return None
    try:
        code = int(status)
    except ValueError:
        print(f"  could not read HTTP status for {url}")
        return None
    if code < 200 or code >= 300:
        print(f"  HTTP {code} for {url}")
        return None
    if not body.strip():
        print(f"  empty body for {url}")
        return None
    return body.decode("iso-8859-1")


# ── table of contents ─────────────────────────────────────────────────────

def _iter_lis(container):
    """Li elements directly under container. A ul wrapped in another ul does not add depth."""
    items = []
    for child in getattr(container, "children", []):
        name = getattr(child, "name", None)
        if name == "li":
            items.append(child)
        elif name in ("ul", "ol"):
            items.extend(_iter_lis(child))
    return items


def _text_outside_lists(tag):
    parts = []
    for child in tag.children:
        name = getattr(child, "name", None)
        if name in ("ul", "ol"):
            continue
        if name is None:
            parts.append(str(child))
        else:
            parts.append(_text_outside_lists(child))
    return clean(" ".join(parts))


def _own_anchor(li):
    """The section link on this li, ignoring links inside a nested list."""
    for anchor in li.find_all("a", href=True):
        if not normalize_href(anchor.get("href")):
            continue
        parent = anchor.parent
        nested = False
        while parent is not None and parent is not li:
            if getattr(parent, "name", None) in ("ul", "ol"):
                nested = True
                break
            parent = parent.parent
        if not nested:
            return anchor
    return None


def _walk_toc(container):
    nodes = []
    for li in _iter_lis(container):
        anchor = _own_anchor(li)
        if anchor:
            href = normalize_href(anchor.get("href"))
            title = clean(anchor.get_text()) or href
        else:
            href = None
            title = _text_outside_lists(li)
        children = _walk_toc(li)
        if not title and not href and not children:
            continue
        nodes.append({
            "title": title or href or "Untitled",
            "href": href,
            "children": children,
        })
    return nodes


def parse_toc(html):
    """Return the TOC tree. Depth comes from nested lists, not font size."""
    soup = BeautifulSoup(html, "html.parser")
    best = None
    best_count = 0
    for ul in soup.find_all("ul"):
        count = sum(
            1 for anchor in ul.find_all("a", href=True)
            if normalize_href(anchor.get("href")))
        if count > best_count:
            best = ul
            best_count = count
    if best is None:
        return []
    return _walk_toc(best)


def flatten_pages(nodes):
    """Section pages in reading order. Headings with no href are index-only."""
    pages = []
    seen = set()

    def walk(items):
        for node in items:
            href = node.get("href")
            if href and href not in seen:
                seen.add(href)
                pages.append(node)
            walk(node.get("children") or [])

    walk(nodes)
    return pages


# ── one section page ──────────────────────────────────────────────────────

def _crumbs(soup):
    """Outline trail from <meta name="part">. The attribute is double-escaped."""
    meta = soup.find("meta", attrs={"name": re.compile(r"^part$", re.I)})
    if meta is None:
        return []
    content = html_lib.unescape(meta.get("content") or "")
    return [clean(part) for part in content.split(">") if clean(part)]


def _is_crumb_fragment(text, crumbs):
    """Running heads repeat a piece of the outline and are not body text."""
    title = clean(text)
    if not title or len(title) > 100:
        return False
    if PARA_RE.match(title):
        return False
    for crumb in crumbs:
        if title == crumb:
            return True
        # "MAN: THE IMAGE OF GOD" inside "Article 1 MAN: THE IMAGE OF GOD"
        if len(title) >= 8 and title in crumb:
            return True
        # A broken tag often leaves the first word, e.g. "Article" from "Article 1 ..."
        if len(title) >= 4 and "." not in title and crumb.startswith(title + " "):
            return True
    return False


def _is_bold_heading(paragraph):
    """True when the paragraph has no text outside <b> tags."""
    fragment = BeautifulSoup(str(paragraph), "html.parser")
    node = fragment.find("p") or fragment
    for bold in node.find_all("b"):
        bold.decompose()
    return clean(node.get_text()) == "" and paragraph.find("b") is not None


def _without_notes(text):
    return re.sub(r"\[\^\d+\]", "", text or "").strip()


def _is_section_label(text):
    """A short unnumbered line the Vatican left as an ordinary paragraph.

    "Part One: the Profession of Faith" and "Above all - Charity" have no
    bold tag and no final period. A real sentence ends with . ? or !.
    """
    bare = _without_notes(text)
    if not bare or len(bare) > 80 or not re.search(r"[A-Za-z]", bare):
        return False
    return not bare.endswith((".", "?", "!"))


def _ends_with_colon(block):
    return _without_notes(block.get("text") or "").endswith(":")


def _inline_text(paragraph):
    """Paragraph text with Vatican footnote markers turned into [^n]."""
    fragment = BeautifulSoup(str(paragraph), "html.parser")
    node = fragment.find("p") or fragment
    for sup in node.find_all("sup"):
        number = clean(sup.get_text())
        sup.replace_with(f"[^{number}]" if number.isdigit() else "")
    text = clean(node.get_text())
    return re.sub(r"\s+\[\^", "[^", text)


def _footnotes(soup):
    """Citations live after the body, as <a name=$...> plus the next font."""
    notes = []
    seen = set()
    for anchor in soup.find_all("a"):
        name = anchor.get("name") or ""
        if not name.startswith("$"):
            continue
        number = clean(anchor.get_text())
        if not number.isdigit() or number in seen:
            continue
        font = anchor.find_parent("font")
        cite = ""
        if font is not None:
            nxt = font.find_next_sibling("font")
            if nxt is not None:
                cite = clean(nxt.get_text())
        if not cite:
            continue
        seen.add(number)
        notes.append((number, cite))
    return notes


def parse_page(html):
    """Headers, body blocks, footnotes, and the page's own Previous/Next."""
    soup = BeautifulSoup(html, "html.parser")
    crumbs = _crumbs(soup)
    nav = {}
    for anchor in soup.find_all("a"):
        label = clean(anchor.get_text()).lower()
        href = normalize_href(anchor.get("href"))
        if not href:
            continue
        if label == "previous":
            nav["prev"] = href
        elif label == "next":
            nav["next"] = href

    blocks = []
    numbers = []
    for paragraph in soup.find_all("p", class_="MsoNormal"):
        text = _inline_text(paragraph)
        if not text:
            continue
        if _is_crumb_fragment(text, crumbs):
            continue
        # A fully bold line is a subheading. Numbered paragraphs stay body text
        # even when the Vatican wrapped them in <b>.
        if _is_bold_heading(paragraph) and not PARA_RE.match(text):
            blocks.append({"kind": "heading", "text": text})
            continue
        style = paragraph.get("style") or ""
        if "margin-left" in style:
            blocks.append({"kind": "quote", "text": text})
            continue
        match = PARA_RE.match(text)
        if match:
            number, rest = match.group(1), match.group(2)
            numbers.append(number)
            blocks.append({"kind": "para", "num": number, "text": rest})
        elif _is_section_label(text):
            blocks.append({"kind": "heading", "text": text})
        else:
            blocks.append({"kind": "para", "num": None, "text": text})

    # Some quotations are not indented. They follow a paragraph that ends with a colon.
    for index, block in enumerate(blocks):
        if index == 0 or block["kind"] != "para" or block.get("num"):
            continue
        if _ends_with_colon(blocks[index - 1]):
            block["kind"] = "quote"

    title = crumbs[-1] if crumbs else ""
    return {
        "title": title,
        "crumbs": crumbs,
        "blocks": blocks,
        "notes": _footnotes(soup),
        "nav": nav,
        "numbers": numbers,
    }


def _yaml_quote(text):
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _body_blocks(node, parsed):
    title = parsed["title"] or node["title"]
    return [
        block for block in parsed["blocks"]
        if block["kind"] != "heading" or block["text"] != title]


def has_body(node, parsed):
    """A page of nothing but repeated outline labels is not a section."""
    return any(
        block["kind"] != "heading" and clean(re.sub(r"\[\^\d+\]", "", block["text"]))
        for block in _body_blocks(node, parsed))


def toc_neighbor(href, ordered_hrefs, present, step):
    """Next (step 1) or previous (step -1) section that will have a note.

    Empty pages, failed downloads, and pages this run did not fetch are
    stepped over. The landing page is always in present.
    """
    try:
        index = ordered_hrefs.index(href)
    except ValueError:
        return None
    cursor = index + step
    while 0 <= cursor < len(ordered_hrefs):
        candidate = ordered_hrefs[cursor]
        if candidate in present:
            return candidate
        cursor += step
    return None


def build_nav(href, by_href, ordered_hrefs, present):
    """Catechism | previous | next | Vatican. Arrows point only at real notes."""
    parts = [wikilink(INDEX_STEM, "Catechism")]
    for step, arrow_at_end in ((-1, False), (1, True)):
        target_href = toc_neighbor(href, ordered_hrefs, present, step)
        target = by_href.get(target_href) if target_href else None
        if not target:
            continue
        label = target["title"]
        display = f"{label} →" if arrow_at_end else f"← {label}"
        parts.append(wikilink(link_target(target), display))
    parts.append(f"[Vatican]({BASE_URL}{href})")
    return " | ".join(parts)


def refresh_nav(path, new_nav):
    """Replace the generated nav lines. Returns updated, same, missing, or error."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"  ERROR reading {path.name}: {exc}")
        return "error"
    lines = text.splitlines()
    found = False
    changed = False
    for index, line in enumerate(lines):
        if "[Vatican](" in line and (
                line.startswith("[[Catechism]]")
                or line.startswith(f"[[{INDEX_STEM}")):
            found = True
            if line != new_nav:
                lines[index] = new_nav
                changed = True
    if not found:
        return "missing"
    if not changed:
        return "same"
    ending = "\n" if text.endswith("\n") else ""
    try:
        path.write_text("\n".join(lines) + ending, encoding="utf-8")
    except OSError as exc:
        print(f"  ERROR writing {path.name}: {exc}")
        return "error"
    return "updated"


def render_page(node, by_href, parsed, ordered_hrefs, present):
    """Return (filename, markdown). Filename is None when the page has no body.

    The note's path is the table-of-contents outline. The heading uses the
    page's own outline title when the Vatican page has one.
    """
    href = node["href"]
    title = parsed["title"] or node["title"]
    body_blocks = _body_blocks(node, parsed)
    if not has_body(node, parsed):
        return None, None

    rel = note_file(node["rel"])
    lines = []
    if parsed["numbers"]:
        aliases = ", ".join(_yaml_quote(f"CCC {number}") for number in parsed["numbers"])
        lines += ["---", f"aliases: [{aliases}]", "---"]
    lines += [f"# {title}", ""]

    nav = build_nav(href, by_href, ordered_hrefs, present)
    lines += [nav, "***", ""]

    parents = [crumb for crumb in parsed["crumbs"][:-1] if crumb and crumb != title]
    if parents:
        lines += [f"*{' > '.join(parents)}*", ""]

    for block in body_blocks:
        if block["kind"] == "heading":
            lines += [f"#### {block['text']}", ""]
        elif block["kind"] == "quote":
            lines += [f"> {block['text']}", ""]
        elif block.get("num"):
            lines += [f"[CCC {block['num']}] {block['text']}", ""]
        else:
            lines += [f"{block['text']}", ""]

    if parsed["notes"]:
        for number, cite in parsed["notes"]:
            lines.append(f"[^{number}]: {cite}")
        lines.append("")

    lines += ["***", nav]
    return rel, "\n".join(lines) + "\n"


# ── index ─────────────────────────────────────────────────────────────────

def _render_nodes(nodes, lines, depth, present):
    leaves = []

    def flush():
        if not leaves:
            return
        for link in leaves:
            lines.append(f"- {link}")
        leaves.clear()
        lines.append("")

    for node in nodes:
        children = node.get("children") or []
        title = node["title"]
        href = node.get("href")
        if children:
            flush()
            level = min(depth + 1, 6)
            if href in present:
                heading = wikilink(link_target(node), title)
                lines.append(f"{'#' * level} {heading}")
            else:
                lines.append(f"{'#' * level} {title}")
            lines.append("")
            _render_nodes(children, lines, depth + 1, present)
        elif href:
            # A page with no note stays in the outline as plain text.
            if href in present:
                leaves.append(wikilink(link_target(node), title))
            else:
                leaves.append(title)
        elif title:
            flush()
            lines += [title, ""]
    flush()


def render_index(tree, present, link_names):
    """Index of the whole TOC. Only hrefs in present become links.

    link_names are optional notes already in the vault, such as Bible.
    They are not assumed. Pass them with --link when you have them.
    """
    lines = [
        "---",
        "aliases:",
        "  - Catechism",
        "---",
    ]
    if link_names:
        linked = " ".join(wikilink(name, name) for name in link_names)
        lines.append(f"links: {linked}")
    lines += [
        f"# {BOOK}",
        "",
    ]
    first = next((node for node in flatten_pages(tree) if node["href"] in present), None)
    if first:
        lines.append(wikilink(link_target(first), "Start Reading →"))
        lines += ["", "---", ""]
    _render_nodes(tree, lines, depth=1, present=present)
    return "\n".join(lines).rstrip() + "\n"


# ── driver ────────────────────────────────────────────────────────────────

def main(output_dir, dry_run=False, skip_existing=False, limit=None, link_names=None):
    out = Path(output_dir)
    link_names = list(link_names or [])
    print(f"[*] Output folder: {out}")

    print("[*] Fetching index page...")
    index_html = fetch(INDEX_URL)
    if not index_html:
        print(f"ERROR: Could not fetch {INDEX_URL}")
        sys.exit(1)

    tree = parse_toc(index_html)
    pages = flatten_pages(tree)
    print(f"[*] {len(pages)} section pages.")
    for node in tree[:8]:
        kind = node["href"] or "heading"
        print(f"  {kind}  {node['title'][:70]}")
    if not pages:
        print("\nERROR: No TOC links found. The Vatican page structure may have changed.")
        sys.exit(1)

    assign_paths(tree)
    todo = pages[:limit] if limit else pages
    if limit:
        print(f"[*] Limit: first {len(todo)} of {len(pages)} pages.")
        print("[*] Pages past the limit are left out of links until a run downloads them.")

    if dry_run:
        print(f"\n[*] Dry run. Would write to {out}")
        print(f"[*] Would write {INDEX_STEM}.md and {len(todo)} section notes. No pages downloaded.")
        for node in todo[:20]:
            print(f"  {note_file(node['rel']).as_posix()}")
        if len(todo) > 20:
            print(f"  ... {len(todo) - 20} more")
        return

    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"ERROR creating {out}: {exc}")
        sys.exit(1)

    def note_path(node):
        return out / note_file(node["rel"])

    by_href = {node["href"]: node for node in pages}
    ordered_hrefs = [node["href"] for node in pages]
    parsed_by_href = {}
    ready = []
    existing = []
    empty = []
    failed = []
    for index, node in enumerate(todo, start=1):
        href = node["href"]
        print(f"[{index}/{len(todo)}] {node['title'][:60]} → {href}")

        if skip_existing and note_path(node).is_file():
            print("  SKIPPED (file exists)")
            existing.append(node)
            continue

        page_html = fetch(BASE_URL + href)
        time.sleep(PAUSE)
        if page_html is None:
            failed.append(node)
            continue

        parsed = parse_page(page_html)
        parsed_by_href[href] = parsed
        if not has_body(node, parsed):
            print("  SKIPPED (no body text)")
            empty.append(node)
            continue
        ready.append(node)

    def compute_present(exclude):
        """Notes this run will write, plus notes already on disk.

        Empty pages and hrefs in exclude (a write that left no file) are omitted.
        A failed download that still has an older note stays linked.
        """
        empty_hrefs = {node["href"] for node in empty}
        ready_hrefs = {node["href"] for node in ready}
        present = set()
        for node in pages:
            href = node["href"]
            if href in exclude or href in empty_hrefs:
                continue
            if href in ready_hrefs or note_path(node).is_file():
                present.add(href)
        return present

    def write_notes(present):
        """Write new notes and refresh prev/next in notes already on disk."""
        written_nodes = []
        write_failed = []
        refreshed = 0
        ready_hrefs = {node["href"] for node in ready}
        for node in ready:
            if node["href"] not in present:
                continue
            parsed = parsed_by_href[node["href"]]
            filename, markdown = render_page(
                node, by_href, parsed, ordered_hrefs, present)
            if filename is None:
                write_failed.append(node)
                continue
            path = out / filename
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(markdown, encoding="utf-8")
            except OSError as exc:
                print(f"  ERROR writing {filename}: {exc}")
                write_failed.append(node)
                continue
            prose = sum(1 for block in parsed["blocks"] if block["kind"] != "heading")
            print(f"  WRITTEN ({prose} blocks, {len(parsed['notes'])} notes) {filename}")
            written_nodes.append(node)

        for node in pages:
            href = node["href"]
            if href not in present or href in ready_hrefs:
                continue
            path = note_path(node)
            if not path.is_file():
                continue
            new_nav = build_nav(href, by_href, ordered_hrefs, present)
            status = refresh_nav(path, new_nav)
            if status == "updated":
                print(f"  REFRESHED nav {path.name}")
                refreshed += 1
            elif status == "missing":
                print(f"  nav line not found, left as-is: {path.name}")
            elif status == "error":
                write_failed.append(node)
        return written_nodes, write_failed, refreshed

    print(f"[*] Writing {len(ready)} notes...")
    present = compute_present(set())
    written_nodes, write_failed, refreshed = write_notes(present)
    # A failed write left no file. Rebuild the arrows without that page.
    missing = {node["href"] for node in write_failed if not note_path(node).is_file()}
    if missing:
        print("[*] A note failed to write. Rebuilding links without it.")
        left_out = [node for node in write_failed if node["href"] in missing]
        present = compute_present(missing)
        written_nodes, write_failed, refreshed = write_notes(present)
        write_failed = left_out + write_failed

    index_path = out / f"{INDEX_STEM}.md"
    try:
        index_path.write_text(
            render_index(tree, present, link_names), encoding="utf-8")
    except OSError as exc:
        print(f"ERROR writing {index_path.name}: {exc}")
        sys.exit(1)
    print(f"[*] Written: {index_path.name}")
    print()
    print("=== DONE ===")
    problems = failed + write_failed
    print(f"{len(written_nodes)} written, {len(existing)} already there, "
          f"{len(empty)} no body text, {len(problems)} FAILED, "
          f"{refreshed} nav refreshed")
    for node in problems:
        print(f"  FAILED  {node['href']}  {node['title'][:60]}")
    print(f"Output directory: {out}")
    if any(not note_path(node).is_file() for node in problems):
        print("Re-run with --skip-existing to fetch the missing pages and "
              "refresh links in the notes already written.")
    if any(note_path(node).is_file() for node in problems):
        print("Notes that already exist were left unchanged. "
              "Re-run without --skip-existing to download them again.")
    if problems:
        sys.exit(1)


def config_path():
    """Where this computer remembers the output folder. Not part of the program."""
    if os.name == "nt":
        root = Path(os.environ.get("APPDATA") or Path.home())
        return root / "ccc-obsidian" / "output-dir"
    root = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    return root / "ccc-obsidian" / "output-dir"


def read_saved_output():
    path = config_path()
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text or text.startswith("#"):
        return None
    return Path(text).expanduser()


def remember_output(folder):
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(str(folder) + "\n", encoding="utf-8")
    print(f"[*] Saved this folder for next time: {path}")


def vault_root(folder):
    """The Obsidian vault that contains folder, if the folder is inside one."""
    start = folder if folder.is_dir() else folder.parent
    for parent in [start, *start.parents]:
        if (parent / ".obsidian").is_dir():
            return parent
    return None


def ask(prompt):
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        raise SystemExit(2)


def prompt_for_folder():
    """Ask for a folder. Explain the vault, and do not invent a path."""
    print("Where should the notes be written?")
    print()
    print("Choose a folder inside your Obsidian vault. It is created if needed.")
    print("Example: ~/Documents/MyVault/Catechism")
    print()
    print("The path is saved on this computer only, at")
    print(f"  {config_path()}")
    print("It is not stored in the program.")
    print()
    while True:
        raw = ask("Folder: ")
        if not raw:
            print("Enter a folder, or press Ctrl-C to stop.")
            continue
        folder = Path(raw).expanduser().resolve()
        if folder.exists() and not folder.is_dir():
            print(f"That path is a file, not a folder: {folder}")
            continue
        if vault_root(folder) is None:
            print("No .obsidian folder was found above that path.")
            print("That is right for a trial outside your vault.")
            print("For notes you want to open in Obsidian, choose a folder inside the vault.")
            answer = ask("Write here anyway? [y/N] ")
            if answer.lower() not in {"y", "yes"}:
                continue
        print(f"Notes will be written to:\n  {folder}")
        answer = ask("Continue? [Y/n] ")
        if answer.lower() in {"", "y", "yes"}:
            return folder


def chosen_output(explicit):
    """Flag, then CCC_OUTPUT, then the saved folder. None when nothing is set."""
    if explicit:
        return Path(explicit).expanduser().resolve(), "option"
    env = os.environ.get("CCC_OUTPUT", "").strip()
    if env:
        return Path(env).expanduser().resolve(), "environment"
    saved = read_saved_output()
    if saved is not None:
        return saved, "saved"
    return None, None


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Save the Vatican Catechism as Obsidian notes. "
                    "You choose the folder. See README.md.")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Folder to write. Example: ~/Documents/MyVault/Catechism. "
             "Overrides CCC_OUTPUT and the saved folder for this run.")
    parser.add_argument(
        "--save-output", action="store_true",
        help="Remember --output as the folder for later runs on this computer.")
    parser.add_argument(
        "--where", action="store_true",
        help="Print the saved folder and exit. Does not download anything.")
    parser.add_argument(
        "--forget-output", action="store_true",
        help="Delete the saved folder so the next run asks again.")
    parser.add_argument(
        "--link", action="append", default=None, metavar="NOTE",
        help="Note to link from the index, without brackets. "
             "Repeat for more than one. Example: --link Bible")
    parser.add_argument(
        "--dry-run", "-n", action="store_true",
        help="Fetch the index and list planned files. Do not download section pages.")
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Do not download a section whose note is already there. "
             "Prev/next in those notes is still refreshed.")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Download only the first N section pages. Use with -o pointing "
             "at a trial folder, not your vault.")
    return parser


def main_cli(argv=None):
    parser = parse_args()
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be at least 1")
    if args.forget_output:
        path = config_path()
        if path.is_file():
            path.unlink()
            print(f"Forgot the saved folder ({path}).")
        else:
            print("No saved folder to forget.")
    folder, source = chosen_output(args.output)
    if args.save_output:
        if folder is None:
            parser.error("--save-output needs --output or CCC_OUTPUT")
        remember_output(folder)
    if args.where:
        if folder is None:
            print("No folder saved. Pass --output, or run the program and answer the question.")
            raise SystemExit(1)
        print(folder)
        return
    if args.forget_output and not args.output and not os.environ.get("CCC_OUTPUT", "").strip():
        return
    if folder is None:
        if not sys.stdin.isatty():
            print("No output folder. Pass --output FOLDER, or set CCC_OUTPUT.", file=sys.stderr)
            raise SystemExit(2)
        folder = prompt_for_folder()
        remember_output(folder)
    elif source == "option" and vault_root(folder) is None:
        print("Note: no .obsidian folder above this path. That is fine for a trial.")
    link_names = []
    for name in args.link or []:
        cleaned = name.strip()
        if cleaned.startswith("[[") and cleaned.endswith("]]"):
            cleaned = cleaned[2:-2]
        cleaned = cleaned.split("|", 1)[0].strip()
        if cleaned:
            link_names.append(cleaned)
    main(folder, dry_run=args.dry_run, skip_existing=args.skip_existing,
         limit=args.limit, link_names=link_names)


if __name__ == "__main__":
    main_cli()

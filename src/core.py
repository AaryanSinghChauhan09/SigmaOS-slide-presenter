"""Markdown slide presenter for SigmaOS-slide-presenter (inspired by hype).

Principles: pure markdown->deck parsing, deterministic slide numbering and
export filenames, theme registry with fail-fast validation, next/prev planning
without side effects, thin export apply layer tested only inside a tempdir.
"""
import argparse, os, sys, tempfile

ENGINE = {
    "name": "sigma-slide",
    "summary": "Markdown slide deck builder with themes and export planning",
    "language": "python",
    "verbs": ["build", "themes", "next-plan", "export-plan"],
    "principles": ["Abstraction", "Separation of Concerns", "Fail-Fast", "KISS",
                   "Least Astonishment", "Deterministic Testing"],
}

cli_doc = """\
$ sigma-slide build talk.md
$ sigma-slide themes
$ sigma-slide next-plan talk.md --current 1
$ sigma-slide export-plan talk.md --format html
"""

THEMES = {
    "light": {"bg": "#ffffff", "fg": "#111111", "accent": "#2e7d32"},
    "dark": {"bg": "#101418", "fg": "#eeeeee", "accent": "#80cbc4"},
    "terminal": {"bg": "#000000", "fg": "#00ff66", "accent": "#00ccff"},
}


class SlideError(ValueError):
    pass


def validate_theme(name):
    if name not in THEMES:
        raise SlideError(f"unknown theme: {name!r} (have: {', '.join(sorted(THEMES))})")
    return dict(THEMES[name])


def build_deck(markdown):
    """Parse markdown into a deck. Slides split on '---' lines.

    First heading (or first non-empty line) is the title; '- ' lines are
    bullets. Pure and deterministic.
    """
    blocks, cur = [], []
    for line in str(markdown).splitlines():
        if line.strip() == "---":
            if cur:
                blocks.append(cur)
            cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append(cur)
    deck = []
    for block in blocks:
        title, bullets = None, []
        for line in block:
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                if title is None:
                    title = s.lstrip("#").strip()
            elif s.startswith(("- ", "* ")):
                bullets.append(s[2:].strip())
            elif title is None:
                title = s
        if title is None:
            continue  # a block with no title contributes nothing
        deck.append({"index": len(deck), "title": title, "bullets": bullets})
    return deck


def next_plan(deck, current):
    """Pure plan for advancing: wraps around, or starts at 0 (least surprise)."""
    if not deck:
        raise SlideError("empty deck")
    if current is None:
        return {"from": None, "to": 0, "title": deck[0]["title"], "wrap": False}
    try:
        current = int(current)
    except (TypeError, ValueError):
        raise SlideError(f"bad current index: {current!r}")
    if not 0 <= current < len(deck):
        raise SlideError(f"current slide out of range: {current}")
    nxt = (current + 1) % len(deck)
    return {"from": current, "to": nxt, "title": deck[nxt]["title"],
            "wrap": nxt == 0}


def export_plan(deck, outdir=".", fmt="html"):
    """Pure plan: deterministic target filenames for every slide."""
    if not deck:
        raise SlideError("empty deck")
    if fmt not in ("html", "md"):
        raise SlideError(f"unknown format: {fmt} (have: html, md)")
    return [os.path.join(outdir, f"slide-{i + 1:03d}.{fmt}")
            for i in range(len(deck))]


def _slide_html(slide, colors):
    items = "".join(f"<li>{b}</li>" for b in slide["bullets"])
    return (f"<html><body style=\"background:{colors['bg']};color:{colors['fg']}\">"
            f"<h1 style=\"color:{colors['accent']}\">{slide['title']}</h1>"
            f"<ul>{items}</ul></body></html>\n")


def _slide_md(slide):
    lines = [f"# {slide['title']}"] + [f"- {b}" for b in slide["bullets"]]
    return "\n".join(lines) + "\n"


def write_export(deck, outdir, fmt="html", theme="light"):
    """Apply layer: write each slide file (self_test uses a tempdir only)."""
    colors = validate_theme(theme)
    files = export_plan(deck, outdir, fmt)
    os.makedirs(outdir, exist_ok=True)
    for path, slide in zip(files, deck):
        body = _slide_html(slide, colors) if fmt == "html" else _slide_md(slide)
        tmp = path + ".sigma-tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(body)
        os.replace(tmp, path)
    return files


def parse_markdown_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="parse a markdown file into a deck")
    b.add_argument("markdown_path")
    sub.add_parser("themes", help="list themes")
    n = sub.add_parser("next-plan", help="plan the next slide (pure)")
    n.add_argument("markdown_path")
    n.add_argument("--current", type=int, default=None,
                   help="current slide index (omit to start at 0)")
    e = sub.add_parser("export-plan", help="plan (or write) an export")
    e.add_argument("markdown_path")
    e.add_argument("--format", choices=("html", "md"), default="html")
    e.add_argument("--theme", default="light")
    e.add_argument("--outdir", default="dist")
    e.add_argument("--write", action="store_true", help="actually write files")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.cmd == "build":
            deck = build_deck(parse_markdown_file(args.markdown_path))
            print(f"{len(deck)} slide(s)")
            for s in deck:
                print(f"{s['index']}: {s['title']} ({len(s['bullets'])} bullet(s))")
        elif args.cmd == "themes":
            for name in sorted(THEMES):
                c = THEMES[name]
                print(f"{name}\tbg={c['bg']} fg={c['fg']} accent={c['accent']}")
        elif args.cmd == "next-plan":
            deck = build_deck(parse_markdown_file(args.markdown_path))
            plan = next_plan(deck, args.current)
            print(f"{plan['from']} -> {plan['to']}: {plan['title']}"
                  f"{' (wrap)' if plan['wrap'] else ''}")
        elif args.cmd == "export-plan":
            deck = build_deck(parse_markdown_file(args.markdown_path))
            files = export_plan(deck, args.outdir, args.format)
            if args.write:
                write_export(deck, args.outdir, args.format, args.theme)
            verb = "wrote" if args.write else "would write"
            for f in files:
                print(f"{verb} {f}")
        return 0
    except (SlideError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


DEMO_MD = """\
# SigmaOS Deck
Intro slide

---

## Features
- Fast
- Simple

---

## Thanks
- Questions?
"""


def self_test() -> None:
    deck = build_deck(DEMO_MD)
    assert len(deck) == 3
    assert [s["title"] for s in deck] == ["SigmaOS Deck", "Features", "Thanks"]
    assert deck[1]["bullets"] == ["Fast", "Simple"]
    assert [s["index"] for s in deck] == [0, 1, 2]
    # empty-ish markdown -> empty deck -> fail-fast everywhere
    assert build_deck("") == []
    assert build_deck("\n\n---\n\n") == []
    try:
        next_plan([], 0)
    except SlideError:
        pass
    else:
        raise AssertionError("empty deck not caught")
    # next-plan: starts at 0, advances, wraps (least astonishment)
    p0 = next_plan(deck, None)
    assert p0 == {"from": None, "to": 0, "title": "SigmaOS Deck", "wrap": False}
    p1 = next_plan(deck, 0)
    assert (p1["to"], p1["wrap"]) == (1, False)
    p2 = next_plan(deck, 2)
    assert (p2["to"], p2["wrap"], p2["title"]) == (0, True, "SigmaOS Deck")
    for bad in (lambda: next_plan(deck, 3),
                lambda: next_plan(deck, -1),
                lambda: next_plan(deck, "x")):
        try:
            bad()
        except SlideError:
            pass
        else:
            raise AssertionError("expected SlideError")
    # themes: validated, fail-fast
    assert validate_theme("dark")["bg"] == "#101418"
    try:
        validate_theme("neon")
    except SlideError:
        pass
    else:
        raise AssertionError("unknown theme not caught")
    # export planning: deterministic filenames
    files = export_plan(deck, "dist", "html")
    assert files == ["dist/slide-001.html", "dist/slide-002.html",
                     "dist/slide-003.html"]
    assert files == export_plan(deck, "dist", "html")   # deterministic
    assert export_plan(deck, "out", "md")[0] == "out/slide-001.md"
    for bad in (lambda: export_plan(deck, "d", "pdf"),
                lambda: export_plan([], "d")):
        try:
            bad()
        except SlideError:
            pass
        else:
            raise AssertionError("expected SlideError")
    # apply layer: write inside a tempdir only
    with tempfile.TemporaryDirectory() as d:
        written = write_export(deck, os.path.join(d, "dist"), "html", "dark")
        assert len(written) == 3
        body = open(written[1], encoding="utf-8").read()
        assert "<h1" in body and "Features" in body and "Fast" in body
        assert "#101418" in body                       # dark theme applied
        md_files = write_export(deck, os.path.join(d, "md"), "md")
        assert open(md_files[2], encoding="utf-8").read() == "# Thanks\n- Questions?\n"
        # file input path
        path = os.path.join(d, "talk.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(DEMO_MD)
        assert len(build_deck(parse_markdown_file(path))) == 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

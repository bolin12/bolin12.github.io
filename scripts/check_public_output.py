"""Fail the build when the public site output contains anything private.

The public build is the only thing published; this is the last gate before it leaves the private
repository. It looks for authoring notes, to-do markers, drafts, contact details and source files.

Usage:
  python scripts/check_public_output.py <built_site_dir> [source_dir]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {".html", ".htm", ".css", ".js", ".xml", ".txt", ".json", ".svg", ".webmanifest"}
SOURCE_SUFFIXES = {".yml", ".yaml", ".md", ".tex", ".cls", ".py", ".ps1", ".sh", ".toml"}
FORBIDDEN_TEXT = [
    (r'class="note"', "authoring note in the HTML"),
    (r"TODO", "to-do marker"),
    (r"建议补|待补|请补充|请核对|可改回", "fill-in or review hint"),
    (r"骨架|草稿", "draft wording"),
    (r"published:\s*false", "draft front matter"),
    # Generic on purpose: this file is public, so it must not contain the real number or address.
    (r"(?<!\d)1[3-9]\d[- ]?\d{4}[- ]?\d{4}(?!\d)", "mobile phone number"),
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z]{2,}", "plain email address"),
]
# Files a static output should never contain, whatever their content.
FORBIDDEN_NAMES = {"NOTES.md", "resume.cls", "main.tex", "main_en.tex", "resume.yml", "resume_en.yml"}


def draft_permalinks(source: Path) -> list[str]:
    """Permalinks of draft pages: anything under drafts/, or with published: false in the front matter."""
    links = []
    for path in source.rglob("*.md"):
        parts = path.relative_to(source).parts
        if any(part.startswith((".", "_site", "public_repo", "vendor")) for part in parts):
            continue
        head = path.read_text(encoding="utf-8", errors="ignore").split("---")
        if len(head) < 3:
            continue
        in_drafts = parts[0] == "drafts"
        if not in_drafts and not re.search(r"^published:\s*false\s*$", head[1], re.M):
            continue
        match = re.search(r"^permalink:\s*(\S+)\s*$", head[1], re.M)
        if match:
            links.append(match.group(1))
    return links


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    site = Path(sys.argv[1])
    source = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(".")
    problems: list[str] = []
    files = [p for p in site.rglob("*") if p.is_file()]
    for path in files:
        rel = path.relative_to(site).as_posix()
        if path.name in FORBIDDEN_NAMES or path.suffix.lower() in SOURCE_SUFFIXES:
            problems.append(f"{rel}: source or private file in the output")
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern, why in FORBIDDEN_TEXT:
            match = re.search(pattern, text)
            if match:
                context = text[max(0, match.start() - 20): match.end() + 20].replace("\n", " ")
                problems.append(f"{rel}: {why}: ...{context}...")
    for link in draft_permalinks(source):
        target = site / link.strip("/")
        if target.exists():
            problems.append(f"{link}: a draft page was published")
    if problems:
        print(f"PUBLIC OUTPUT CHECK FAILED ({len(problems)} problem(s)):")
        for line in problems:
            print("  -", line)
        return 1
    print(f"public output check passed: {len(files)} files, nothing private found")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Write NOTES.md: every authoring note and to-do in one place, for the author only.

The notes live in the source (comments and note fields); the published site never shows them. This
gathers them next to the entry they belong to, so you can see what is left to fill in. NOTES.md stays in
the private repository and is excluded from the site.

Usage:
  python scripts/notes_report.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "NOTES.md"


def resume_notes(path: Path) -> list[tuple[str, list[str], list[str]]]:
    """(where, todos, notes) per section/entry/point of the resume data, read line by line."""
    rows: list[tuple[str, list[str], list[str]]] = []
    section = item = label = ""
    todos: list[str] = []
    notes: list[str] = []
    in_todo = False

    def flush(where: str) -> None:
        nonlocal todos, notes
        if todos or notes:
            rows.append((where, todos, notes))
        todos, notes = [], []

    def where() -> str:
        return " / ".join(p for p in (section, item, label) if p)

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        title = re.match(r"-\s+title:\s*(.+)", stripped)
        lab = re.match(r"-\s+label:\s*(.+)", stripped)
        if title and indent == 2:
            flush(where()); section, item, label = title.group(1), "", ""
            in_todo = False
            continue
        if title and indent == 6:
            flush(where()); item, label = title.group(1), ""
            in_todo = False
            continue
        if lab:
            flush(where()); label = lab.group(1)
            in_todo = False
            continue
        if stripped.startswith("# TODO"):
            todos.append(re.sub(r"^#\s*TODO\(补充\):\s*", "", stripped))
            in_todo = True
            continue
        if in_todo and stripped.startswith("#"):
            todos[-1] += " " + stripped.lstrip("# ").strip()
            continue
        in_todo = False
        note = re.match(r"note:\s*(.+)", stripped)
        if note:
            notes.append(note.group(1).strip("（）"))
    flush(where())
    return rows


def page_notes(path: Path) -> tuple[bool, list[str], list[str]]:
    """(published, todo blocks, visible placeholder notes) of one project or content page."""
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    front = parts[1] if len(parts) == 3 else ""
    published = not re.search(r"^published:\s*false\s*$", front, re.M)
    todos = [" ".join(b.split()) for b in re.findall(r"\{%\s*comment\s*%\}(.*?)\{%\s*endcomment\s*%\}", text, re.S)]
    placeholders = [" ".join(re.sub(r"<[^>]+>", "", m).split())
                    for m in re.findall(r'<(?:span|p) class="note">(.*?)</(?:span|p)>', text, re.S)]
    return published, todos, placeholders


def main() -> int:
    lines = ["# 批注与待补清单", "",
             "自动生成（scripts/notes_report.py），只在私有仓库里，不会发布到网站。改完简历或页面后会重新生成。", ""]
    total = 0
    rows = resume_notes(ROOT / "_data" / "resume.yml")
    lines += ["## 简历（_data/resume.yml）", ""]
    for place, todos, notes in rows:
        lines.append(f"### {place or '（顶部）'}")
        for t in todos:
            lines.append(f"- [ ] **待补**：{t}")
            total += 1
        for n in notes:
            lines.append(f"- 批注：{n}")
        lines.append("")
    pages = sorted((ROOT / "projects").rglob("*.md")) + sorted((ROOT / "drafts").rglob("*.md"))
    lines += ["## 项目页（projects/ 已发布，drafts/ 草稿只在本地预览可见）", ""]
    for path in pages:
        published, todos, placeholders = page_notes(path)
        if not (todos or placeholders):
            continue
        published = published and path.relative_to(ROOT).parts[0] != "drafts"
        lines.append(f"### {path.relative_to(ROOT).as_posix()}（{'已发布' if published else '草稿，未发布'}）")
        for t in todos:
            lines.append(f"- [ ] **待补**：{t}")
            total += 1
        for p in placeholders:
            lines.append(f"- 占位：{p}")
            total += 1
        lines.append("")
    lines.insert(3, f"待补条目共 **{total}** 条。")
    lines.insert(4, "")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.name}: {total} to-do/placeholder items")
    return 0


if __name__ == "__main__":
    sys.exit(main())

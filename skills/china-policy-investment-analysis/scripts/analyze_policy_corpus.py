#!/usr/bin/env python3
"""Reproducible structure and keyword probes for Chinese policy documents.

The output is evidence for manual review, not a policy-importance score.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path
from typing import Any, Iterable


SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}
HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
SPACE_RE = re.compile(r"\s+")
HEADING_RE = re.compile(
    r"^\s*(?P<heading>(?:第[一二三四五六七八九十百零〇0-9]+[篇章节][^\n]{0,80})"
    r"|(?:[一二三四五六七八九十百零〇]+、[^\n]{1,80}))\s*$"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count exact keywords and list heading candidates in policy files."
    )
    parser.add_argument("inputs", nargs="+", help="Files or directories to analyze")
    parser.add_argument(
        "--recursive", action="store_true", help="Search directories recursively"
    )
    parser.add_argument(
        "--keywords", default="", help="Comma-separated exact keywords"
    )
    parser.add_argument(
        "--keywords-file", help="UTF-8 file with one exact keyword per line"
    )
    parser.add_argument(
        "--start-marker", help="Keep text after the first exact marker occurrence"
    )
    parser.add_argument(
        "--end-marker", help="Keep text before the first exact marker occurrence"
    )
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="json"
    )
    parser.add_argument("--output", help="Write output to this UTF-8 file")
    return parser.parse_args(argv)


def collect_files(inputs: Iterable[str], recursive: bool) -> list[Path]:
    found: set[Path] = set()
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_SUFFIXES:
                found.add(path)
            continue
        if path.is_dir():
            iterator = path.rglob("*") if recursive else path.glob("*")
            found.update(
                candidate.resolve()
                for candidate in iterator
                if candidate.is_file()
                and candidate.suffix.lower() in SUPPORTED_SUFFIXES
            )
            continue
        raise FileNotFoundError(f"Input does not exist: {path}")
    return sorted(found, key=lambda item: str(item))


def load_keywords(args: argparse.Namespace) -> list[str]:
    keywords = [item.strip() for item in args.keywords.split(",") if item.strip()]
    if args.keywords_file:
        path = Path(args.keywords_file).expanduser().resolve()
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                keywords.append(value)
    normalized = [unicodedata.normalize("NFKC", value) for value in keywords]
    return list(dict.fromkeys(normalized))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_plain_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    errors: list[str] = []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeError("; ".join(errors))


def read_pdf(path: Path) -> tuple[str, str]:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages), "pypdf"
    except (ImportError, OSError, ValueError) as pypdf_error:
        binary = shutil.which("pdftotext")
        if not binary:
            raise RuntimeError(
                "PDF extraction needs pypdf or the pdftotext executable; "
                f"pypdf result: {pypdf_error}"
            ) from pypdf_error
        with tempfile.TemporaryDirectory(prefix="policy-pdf-") as temp_dir:
            output = Path(temp_dir) / "document.txt"
            completed = subprocess.run(
                [binary, "-layout", str(path), str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr.strip() or "pdftotext failed")
            return output.read_text(encoding="utf-8", errors="replace"), "pdftotext"


def read_document(path: Path) -> tuple[str, str]:
    if path.suffix.lower() == ".pdf":
        return read_pdf(path)
    return read_plain_text(path)


def crop_text(text: str, start_marker: str | None, end_marker: str | None) -> str:
    cropped = text
    if start_marker:
        marker = unicodedata.normalize("NFKC", start_marker)
        position = cropped.find(marker)
        if position < 0:
            raise ValueError(f"start marker not found: {start_marker}")
        cropped = cropped[position + len(marker) :]
    if end_marker:
        marker = unicodedata.normalize("NFKC", end_marker)
        position = cropped.find(marker)
        if position < 0:
            raise ValueError(f"end marker not found: {end_marker}")
        cropped = cropped[:position]
    return cropped


def heading_candidates(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            heading = SPACE_RE.sub(" ", match.group("heading")).strip()
            if heading not in headings:
                headings.append(heading)
    return headings


def analyze_file(
    path: Path,
    keywords: list[str],
    start_marker: str | None,
    end_marker: str | None,
) -> dict[str, Any]:
    text, extraction = read_document(path)
    normalized = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    body = crop_text(normalized, start_marker, end_marker)
    compact = SPACE_RE.sub("", body)
    hanzi_count = len(HAN_RE.findall(body))
    counts = {
        keyword: {
            "count": compact.count(SPACE_RE.sub("", keyword)),
            "per_10000_hanzi": 0.0,
        }
        for keyword in keywords
    }
    for values in counts.values():
        if hanzi_count:
            values["per_10000_hanzi"] = round(
                values["count"] * 10000 / hanzi_count, 4
            )
    return {
        "path": str(path),
        "sha256": sha256(path),
        "extraction": extraction,
        "body_characters": len(body),
        "hanzi_count": hanzi_count,
        "keywords": counts,
        "heading_candidates": heading_candidates(body),
        "warnings": [
            "Heading candidates may contain both table-of-contents and body copies; review manually."
        ],
    }


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Policy corpus probe",
        "",
        f"- Files analyzed: {len(payload['documents'])}",
        f"- Files with errors: {len(payload['errors'])}",
        "- Scope: exact substring counts after NFKC normalization and whitespace removal",
        "",
    ]
    for document in payload["documents"]:
        lines.extend(
            [
                f"## {Path(document['path']).name}",
                "",
                f"- Path: `{document['path']}`",
                f"- SHA-256: `{document['sha256']}`",
                f"- Extraction: `{document['extraction']}`",
                f"- Han characters: {document['hanzi_count']}",
                "",
                "| Keyword | Count | Per 10,000 Han characters |",
                "|---|---:|---:|",
            ]
        )
        for keyword, values in document["keywords"].items():
            lines.append(
                f"| {markdown_escape(keyword)} | {values['count']} | "
                f"{values['per_10000_hanzi']:.4f} |"
            )
        lines.extend(["", "### Heading candidates", ""])
        if document["heading_candidates"]:
            lines.extend(f"- {item}" for item in document["heading_candidates"])
        else:
            lines.append("- None found")
        lines.extend(["", "> " + document["warnings"][0], ""])
    if payload["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend(
            f"- `{item['path']}`: {item['error']}" for item in payload["errors"]
        )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        files = collect_files(args.inputs, args.recursive)
        keywords = load_keywords(args)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not files:
        print("error: no supported .txt, .md, or .pdf files found", file=sys.stderr)
        return 2
    if not keywords:
        print("error: provide --keywords or --keywords-file", file=sys.stderr)
        return 2

    documents: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for path in files:
        try:
            documents.append(
                analyze_file(path, keywords, args.start_marker, args.end_marker)
            )
        except (OSError, UnicodeError, RuntimeError, ValueError) as exc:
            errors.append({"path": str(path), "error": str(exc)})

    payload = {
        "method": {
            "normalization": "Unicode NFKC",
            "keyword_count": "exact substring after all whitespace removal",
            "body_start_marker": args.start_marker,
            "body_end_marker": args.end_marker,
        },
        "documents": documents,
        "errors": errors,
    }
    rendered = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        if args.format == "json"
        else render_markdown(payload)
    )
    if args.output:
        Path(args.output).expanduser().resolve().write_text(
            rendered + "\n", encoding="utf-8"
        )
    else:
        print(rendered)
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Reconcile an academic-PDF audit with ID-named files and identity evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader


ID_COLUMNS = ("ID", "id", "Record_ID", "provisional_include_no", "study_id", "record_id")
TITLE_COLUMNS = ("title", "Title", "article_title")
DOI_COLUMNS = ("doi", "DOI")
FILE_COLUMNS = ("pdf_filename", "PDF filename", "filename")
PATH_COLUMNS = ("pdf_path", "PDF path", "path", "corrected_pdf_path", "accepted_pdf")
STATUS_COLUMNS = ("identity_status", "identity status", "validation_status", "validation status", "download_status", "download status", "retrieval_status", "retrieval status", "status")
DEFAULT_ACCEPTED = {"accepted", "downloaded", "downloaded_validated", "accepted_pdf", "user_supplied_pdf", "corrected_pdf_validated_existing"}
TOKEN_RE = re.compile(r"[a-z0-9]+")
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:a-z0-9]+", re.I)


def first(row: dict[str, str], names: tuple[str, ...]) -> str:
    return next((str(row.get(name, "")).strip() for name in names if str(row.get(name, "")).strip()), "")


def normalize_doi(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", value)
    value = re.sub(r"^doi:\s*", "", value)
    return value.rstrip(".,;)")


def tokens(value: str) -> set[str]:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return set(TOKEN_RE.findall(value))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_path(row: dict[str, str], pdf_dir: Path, rid: str) -> Path:
    raw = first(row, PATH_COLUMNS)
    if raw:
        candidate = Path(raw).expanduser()
        return candidate if candidate.is_absolute() else pdf_dir / candidate
    filename = first(row, FILE_COLUMNS) or f"{rid}.pdf"
    return pdf_dir / filename


def inspect_pdf(path: Path, expected_title: str, expected_doi: str, text_pages: int) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path)}
    if not path.exists():
        return {**result, "structural": "fail", "identity": "fail", "reason": "missing_file"}
    try:
        reader = PdfReader(str(path))
        pages = len(reader.pages)
        if pages < 1:
            raise ValueError("zero pages")
        text = "\n".join((reader.pages[i].extract_text() or "") for i in range(min(pages, text_pages)))
    except Exception as exc:
        return {**result, "structural": "fail", "identity": "fail", "reason": f"unreadable: {exc}"}

    digest = sha256(path)
    expected = tokens(expected_title)
    observed = tokens(text)
    title_coverage = len(expected & observed) / len(expected) if expected else None
    found_dois = {normalize_doi(match.group(0)) for match in DOI_RE.finditer(text)}
    normalized_expected_doi = normalize_doi(expected_doi)

    conflicting_dois = {
        doi for doi in found_dois
        if doi != normalized_expected_doi
        and not normalized_expected_doi.startswith(doi + ".")
        and not doi.startswith(normalized_expected_doi + ".")
    }
    if normalized_expected_doi and conflicting_dois and normalized_expected_doi not in found_dois:
        identity, reason = "fail", "doi_mismatch"
    elif normalized_expected_doi and normalized_expected_doi in found_dois:
        identity, reason = "pass", "doi_match"
    elif title_coverage is not None and len(expected) >= 5 and title_coverage >= 0.80:
        identity, reason = "pass", "strong_early_title_match"
    elif title_coverage is not None and title_coverage >= 0.55:
        identity, reason = "review", "partial_title_match"
    else:
        identity, reason = "review", "insufficient_identity_evidence"

    return {
        **result,
        "structural": "pass",
        "identity": identity,
        "reason": reason,
        "pages": pages,
        "sha256": digest,
        "title_coverage": round(title_coverage, 3) if title_coverage is not None else None,
        "expected_doi": normalized_expected_doi,
        "found_dois": sorted(found_dois),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--pdf-dir", required=True, type=Path)
    parser.add_argument("--accepted-status", action="append", dest="accepted", help="Repeat to override accepted status labels")
    parser.add_argument("--text-pages", type=int, default=2, help="Early pages used for identity evidence (default: 2)")
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--require-identity", action="store_true", help="Exit nonzero for review outcomes as well as hard failures")
    args = parser.parse_args()
    if args.text_pages < 1:
        parser.error("--text-pages must be at least 1")
    if not args.pdf_dir.is_dir():
        parser.error("--pdf-dir must be an existing directory")

    with args.audit.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        rows = list(reader)
    audit_errors: list[dict[str, object]] = []
    for label, aliases in (("ID", ID_COLUMNS), ("status", STATUS_COLUMNS)):
        if not any(name in headers for name in aliases):
            audit_errors.append({"reason": f"missing_{label}_column", "accepted_columns": aliases})
    accepted = set(args.accepted or DEFAULT_ACCEPTED)
    results: list[dict[str, object]] = []
    hashes: defaultdict[str, list[str]] = defaultdict(list)
    seen_ids: set[str] = set()
    status_counts: defaultdict[str, int] = defaultdict(int)

    for row_number, row in enumerate(rows, start=2):
        rid = first(row, ID_COLUMNS)
        status = first(row, STATUS_COLUMNS)
        status_counts[status or "(blank)"] += 1
        if not rid or not status:
            audit_errors.append({"row": row_number, "reason": "missing_id_or_status"})
            continue
        if rid in seen_ids:
            audit_errors.append({"row": row_number, "id": rid, "reason": "duplicate_id"})
        seen_ids.add(rid)
        if status not in accepted:
            continue
        path = resolve_path(row, args.pdf_dir, rid)
        inspected = inspect_pdf(path, first(row, TITLE_COLUMNS), first(row, DOI_COLUMNS), args.text_pages)
        item = {"row": row_number, "id": rid, "audit_status": status, **inspected}
        results.append(item)
        if inspected.get("sha256"):
            hashes[str(inspected["sha256"])].append(rid)

    duplicate_hashes = {digest: ids for digest, ids in hashes.items() if len(set(ids)) > 1}
    accepted_paths = [path for path in args.pdf_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"]
    referenced_paths = {Path(str(item["path"])).resolve() for item in results}
    unreferenced_files = sorted(path.name for path in accepted_paths if path.resolve() not in referenced_paths)
    summary = {
        "audit_rows": len(rows),
        "audit_errors": audit_errors,
        "status_counts": dict(status_counts),
        "accepted_statuses": sorted(accepted),
        "accepted_rows_checked": len(results),
        "pdf_files": len(accepted_paths),
        "structural_failures": sum(item["structural"] == "fail" for item in results),
        "identity_failures": sum(item["identity"] == "fail" for item in results),
        "identity_review": sum(item["identity"] == "review" for item in results),
        "duplicate_hashes": duplicate_hashes,
        "unreferenced_files": unreferenced_files,
        "results": results,
    }
    payload = json.dumps(summary, ensure_ascii=False, indent=2)
    print(payload)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(payload + "\n", encoding="utf-8")

    hard_failure = audit_errors or summary["structural_failures"] or summary["identity_failures"] or duplicate_hashes or unreferenced_files
    review_failure = args.require_identity and summary["identity_review"]
    sys.exit(1 if hard_failure or review_failure else 0)


if __name__ == "__main__":
    main()

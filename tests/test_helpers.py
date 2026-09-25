"""Public, synthetic fixtures. No private files or network access required."""
import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


ROOT = Path(__file__).resolve().parents[1]
VALIDATE = ROOT / "literature-pdf-retrieval/scripts/validate_pdf_audit.py"
EXTRACT = ROOT / "literature-pdf-retrieval/scripts/extract_article_pages.py"
TITLE = "Learning autonomy evidence across educational settings"
DOI = "10.1234/synthetic-only"


def make_pdf(path, text, pages=1):
    writer = PdfWriter()
    for _ in range(pages):
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                                 NameObject("/Subtype"): NameObject("/Type1"),
                                 NameObject("/BaseFont"): NameObject("/Helvetica")})
        page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"):
            DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
        content = DecodedStreamObject()
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content.set_data(f"BT /F1 11 Tf 50 700 Td ({safe}) Tj ET".encode("ascii"))
        page[NameObject("/Contents")] = writer._add_object(content)
    with path.open("wb") as stream:
        writer.write(stream)


class HelpersTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.pdfs = self.work / "pdfs"
        self.pdfs.mkdir()

    def audit(self, rows, fields=None, extra=()):
        path = self.work / "audit.csv"
        fields = fields or list(rows[0])
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        report = self.work / "report.json"
        result = subprocess.run([sys.executable, str(VALIDATE), "--audit", str(path),
            "--pdf-dir", str(self.pdfs), "--json-out", str(report), *extra], capture_output=True, text=True)
        return result, json.loads(report.read_text()) if report.exists() else None

    def row(self, rid="R001", **changes):
        return dict(ID=rid, title=TITLE, DOI=DOI, identity_status="accepted", **changes)

    def test_doi_match_and_input_preservation(self):
        path = self.pdfs / "R001.pdf"
        make_pdf(path, TITLE + " DOI " + DOI)
        original = path.read_bytes()
        result, report = self.audit([self.row()], extra=["--require-identity"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(report["results"][0]["reason"], "doi_match")
        self.assertEqual(path.read_bytes(), original)

    def test_real_project_aliases_and_absolute_path(self):
        path = self.pdfs / "R001.pdf"
        make_pdf(path, DOI)
        result, report = self.audit([dict(Record_ID="R001", Title=TITLE, DOI=DOI,
            accepted_pdf=str(path), status="downloaded_validated")])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["accepted_rows_checked"], 1)

    def test_wrong_doi_is_not_rescued_by_title(self):
        make_pdf(self.pdfs / "R001.pdf", TITLE + " 10.9999/other")
        result, report = self.audit([self.row()])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["results"][0]["reason"], "doi_mismatch")

    def test_identity_review_blocks_strict_gate(self):
        make_pdf(self.pdfs / "R001.pdf", "Unreadable identity")
        result, report = self.audit([self.row()], extra=["--require-identity"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["identity_review"], 1)

    def test_missing_columns_fail_even_with_no_files(self):
        result, report = self.audit([dict(unrecognized_id="R001", state="accepted")])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(report["audit_errors"]), 3)

    def test_blank_id_and_duplicate_id_fail(self):
        for rows in ([dict(ID="", status="not_attempted")],
                     [dict(ID="R001", status="not_attempted")] * 2):
            with self.subTest(rows=rows):
                result, report = self.audit(rows)
                self.assertEqual(result.returncode, 1)
                self.assertTrue(report["audit_errors"])

    def test_unresolved_queue_is_valid_without_claiming_success(self):
        result, report = self.audit([dict(ID="R001", status="login_required")], extra=["--require-identity"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["accepted_rows_checked"], 0)
        self.assertEqual(report["status_counts"], {"login_required": 1})

    def test_orphan_pdf_blocks_zero_checked_false_success(self):
        make_pdf(self.pdfs / "R001.PDF", DOI)
        result, report = self.audit([dict(ID="R001", status="custom_accepted")])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["unreferenced_files"], ["R001.PDF"])

    def test_custom_status_and_relative_path(self):
        make_pdf(self.pdfs / "custom.pdf", DOI)
        result, report = self.audit([dict(ID="R001", title=TITLE, DOI=DOI,
            pdf_path="custom.pdf", status="approved_source")], extra=["--accepted-status", "approved_source"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report["accepted_rows_checked"], 1)

    def test_missing_explicit_path_does_not_fall_back(self):
        make_pdf(self.pdfs / "R001.pdf", DOI)
        result, report = self.audit([self.row(pdf_path="missing.pdf")])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["results"][0]["reason"], "missing_file")

    def test_duplicate_hashes_across_ids_fail(self):
        path = self.pdfs / "R001.pdf"
        make_pdf(path, DOI)
        (self.pdfs / "R002.pdf").write_bytes(path.read_bytes())
        result, report = self.audit([self.row(), self.row("R002")])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(report["duplicate_hashes"]), 1)

    def test_html_disguised_as_pdf_fails(self):
        (self.pdfs / "R001.pdf").write_text("<html>Sign in</html>")
        result, report = self.audit([self.row()])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["structural_failures"], 1)

    def test_invalid_text_page_count(self):
        result, report = self.audit([self.row()], extra=["--text-pages", "0"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(report)

    def extract(self, source, output, start, end):
        return subprocess.run([sys.executable, str(EXTRACT), str(source), str(output),
            "--start", str(start), "--end", str(end)], capture_output=True, text=True)

    def test_extract_inclusive_range_preserves_original(self):
        source, output = self.work / "issue.pdf", self.work / "article.pdf"
        make_pdf(source, "Synthetic issue", pages=4)
        original = source.read_bytes()
        result = self.extract(source, output, 2, 3)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(PdfReader(output).pages), 2)
        self.assertEqual(source.read_bytes(), original)

    def test_extract_rejects_invalid_ranges_without_output(self):
        source, output = self.work / "issue.pdf", self.work / "article.pdf"
        make_pdf(source, "Synthetic issue", pages=4)
        for start, end in [(0, 2), (-1, 2), (3, 2), (2, 5)]:
            with self.subTest(start=start, end=end):
                self.assertEqual(self.extract(source, output, start, end).returncode, 2)
                self.assertFalse(output.exists())

    def test_extract_rejects_existing_output_and_source_overwrite(self):
        source, output = self.work / "issue.pdf", self.work / "article.pdf"
        make_pdf(source, "Synthetic issue", pages=4)
        output.write_bytes(b"preserve me")
        original = source.read_bytes()
        self.assertEqual(self.extract(source, source, 1, 2).returncode, 2)
        self.assertEqual(self.extract(source, output, 1, 2).returncode, 2)
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(output.read_bytes(), b"preserve me")


if __name__ == "__main__":
    unittest.main()

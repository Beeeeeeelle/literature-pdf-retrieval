# Small, fictional starting examples

`record_state.csv` contains placeholder titles and no real DOI or accepted PDF.
`retrieval_attempts.csv` and `human_handoff.md` are templates, not observed events.
No paper files or private institutional logs are distributed.

Run a queue-only check using an **empty** PDF directory:

```bash
mkdir -p .test-output/empty-pdfs
python literature-pdf-retrieval/scripts/validate_pdf_audit.py \
  --audit examples/record_state.csv --pdf-dir .test-output/empty-pdfs \
  --require-identity
```

Expected: 2 audit rows, 0 accepted rows, 0 files, no audit errors. This is a valid
unresolved queue, not successful retrieval or a completed review.

## CSV columns and reconciliation

Use `ID,title,DOI,pdf_filename,identity_status` for a simple audit. The validator also
recognizes legacy `Record_ID`, `accepted_pdf` and `status=downloaded_validated`.
Relative `pdf_path` / `accepted_pdf` paths resolve against `--pdf-dir`; explicit missing
paths fail instead of silently falling back to a different ID-named file.

Accepted labels default to `accepted`, `downloaded`, `downloaded_validated`,
`accepted_pdf`, `user_supplied_pdf`, and `corrected_pdf_validated_existing`.
Use repeated `--accepted-status` arguments to **replace** that set for another project.
When present, identity status takes priority over retrieval status. Check the reported
status counts to ensure your mapping is correct; custom pending labels are retained.

Missing ID/status columns, blank row IDs/statuses, duplicate IDs, unreadable or
mismatched files, cross-ID duplicate hashes, and unreferenced PDF files return nonzero.
With `--require-identity`, unresolved identity outcomes also return nonzero. A failed
check writes its JSON report when `--json-out` is provided; it does not move or alter PDFs.

The checker inventories top-level PDF files in `--pdf-dir`. Keep candidate and rejected
files in separate folders. A parser pass is a triage result; inspect version,
completeness and source identity before canonical acceptance.

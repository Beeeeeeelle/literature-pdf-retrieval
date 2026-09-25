# Detailed Literature PDF Retrieval Workflow

## Inputs

- Excel/CSV/RIS study list with stable IDs and titles.
- Prefer columns for DOI/URL, title, authors, year, journal/source, decision label, and notes.
- Optional contact email for Unpaywall.
- Optional Zotero library/export.
- Optional authenticated Chrome session and institutional proxy.

## Output Layout

Recommended structure:

```text
outputs/<project>/
  pdfs/
  pdfs_staging/
  pdfs_rejected/
  logs/
  record_state.csv
  retrieval_attempts.csv
  master_availability_audit.csv
  remaining_queue.csv
  <source>_completed.xlsx
```

Keep one durable current-state row for every source row, including failures. Append every retrieval attempt to a separate attempt ledger. For large projects, rebuild a master audit after each meaningful batch instead of relying on memory.

At run start, write a small manifest in `logs/` containing the input path and hash, audit path, PDF directories, ID column, title/DOI columns, accepted statuses, date, and tool/script version. This prevents a resumed run from silently switching source workbooks or output folders.

## Retrieval Order

1. Apply user exclusions and scope rules.
2. Normalize IDs and file names.
3. Enrich missing DOI or stable URL by exact-title search.
4. Try direct public PDF routes and Unpaywall.
5. Try high-yield repositories and open platforms.
6. Import to Zotero and run Find Available PDFs when available.
7. Try authenticated Chrome/proxy workflows in small platform-specific batches.
8. Incorporate user-supplied PDFs and whole-issue extraction.
9. Rebuild audit and remaining queue.

## Queue Design for Large Corpora

Maintain separate queues instead of one flat "missing" list:

- `downloaded_validated`
- `excluded_by_user_rule`
- `missing_no_doi`
- `missing_has_doi`
- `wrong_article_suspected`
- `platform_tried_no_pdf`
- `login_required_or_paywalled`
- `rate_limited_or_challenge`
- `server_error_or_404`
- `not_attempted`

Group remaining rows by DOI prefix, host, and source type. Work high-yield groups first. If a low-yield platform returns 0 downloads in a small representative batch, pause that platform and switch to title/repository search.

Assign each queue row a `next_action` and `routes_tried` summary. Prefer actionable values such as `enrich_doi`, `search_title_repository`, `try_authenticated_publisher`, `manual_identity_review`, `extract_from_full_issue`, or `request_user_pdf`. A queue is a work plan, not another copy of the word “missing.”

## Resume and Idempotency

- Reconcile the input, current-state audit, accepted directory, staging directory, and rejected directory before making network requests.
- Compare hashes, not only filenames. Do not redownload accepted hashes or overwrite a different existing hash.
- Reconcile stale paths from earlier machines against the configured PDF directory and filename. Record a path mapping in a new audit copy before validation; the validator does not silently replace an explicit missing path with another file.
- Preserve prior attempt rows. Start a new attempt with a timestamp and route name.
- Save progress after each accepted PDF and after each small browser batch. A crash should lose at most the active candidate, not the batch state.
- When metadata changes, retain the old value in notes or attempt history and rerun identity validation.

## Candidate Promotion and Correction

1. Download or copy to `pdfs_staging/<ID>__<route>__<timestamp>.pdf`.
2. Check PDF structure, page count, extracted first pages, DOI evidence, title/author evidence, and hash.
3. If rejected, move to `pdfs_rejected/` with the reason in the filename and record the attempt.
4. If ambiguous, keep it out of `pdfs/` and add it to manual review.
5. If accepted and no prior accepted file exists, promote it to `pdfs/<ID>.pdf` and update current state.
6. If replacing a prior file, move the prior hash to a recoverable `stale_corrected/` or rejected location, promote atomically, and record old/new hashes.
7. Mark downstream extraction, eligibility, or coding derived from the old hash as stale; rerun it before final reporting.

Never copy a candidate directly over an accepted ID-named PDF before validation.

## DOI and Title Enrichment

For missing DOI records:

- Search exact title with quotes.
- Check Crossref/OpenAlex/Semantic Scholar, publisher pages, conference proceedings, repository pages, ERIC, ProQuest-open, and dissertation repositories.
- If a DOI is found, append it to the audit and rerun DOI-based routes.
- If the official title expands the workbook title, record the official title/variant in notes and use first-page validation.
- Do not accept a result only because keywords overlap; confirm title, authors, venue/year, or DOI.

## Direct Public Source Patterns

- **OJS journals**: Look for `citation_pdf_url`, `article/download/...`, or galley links. If `article/view/...` downloads an HTML shell, try the `download` endpoint.
- **DSpace/IRIS repositories**: If `/bitstream/...` or `/retrieve/...` returns HTML, look for metadata `citation_pdf_url`; for DSpace 7, try `/server/api/core/bitstreams/<uuid>/content`.
- **CEUR**: Use volume table of contents to confirm paper number before downloading `paperNN.pdf`.
- **arXiv**: Use `https://arxiv.org/pdf/<id>`.
- **JMIR**: Use article `/PDF` routes and validate page text.
- **SCITEPRESS**: Follow the official paper's download link. On certificate errors, use another valid official route or pause for resolution; do not disable certificate verification.
- **eScholarship**: If the page is blocked or unavailable, try the stable content route `https://escholarship.org/content/<qt-id>/<qt-id>.pdf`.
- **OhioLINK ETD**: Use the page's `citation_pdf_url` or `ws/send_file/send?accession=...&disposition=inline`.
- **MIT Press/books**: Confirm the file is the target chapter, not book front matter or table of contents.
- **Zenodo/Figshare/Mendeley Data**: Inspect API metadata. Dataset/software/image records may have files but are not article PDFs.

## Authenticated Browser Rules

- Reuse the user's active authenticated browser session.
- Do not ask for repeated login unless a page clearly shows session expiry.
- Do not refresh continuously while the user is logging in.
- Work one article at a time on rate-sensitive platforms.
- Stop on 429, CAPTCHA, Cloudflare/WAF challenge, or login loops.
- Save only actual PDF bytes. Do not print HTML pages to PDF unless explicitly requested as a web capture.
- Monitor browser downloads and network PDF responses, but validate every saved file afterward.
- Give the browser worker a numbered batch containing ID, title, DOI, canonical landing URL, routes already tried, and exact output/staging path. Reconcile returned files by ID and hash after every small batch.
- Do not let direct scripts and browser workers write the same final filename concurrently. All workers write unique staging names; one reconciliation step promotes files.
- When the browser yields a signed or session URL, record both the stable landing page and the resolved download URL when safe; use the stable URL for future resumption.

## Matching Rules

Before accepting a PDF, validate at least one of:

- DOI match in extracted text or metadata.
- Strong first-page title match.
- Stable article/chapter ID or PII match.
- First-page author/title strongly matches the source row.
- Documented human confirmation of identity. Supplying a file alone is not confirmation.

Prefer first page or title zone for title matching. Body text can contain many title words from citations and should not be enough by itself.

Identity decision rules:

- A normalized DOI match is strong acceptance evidence.
- A confirmed target-article DOI mismatch is rejection evidence even when the title looks similar. A parser flag first requires checking whether the identifier belongs to the article, its containing book, a reference or a template. A truncated or missing DOI needs corroboration.
- If the expected DOI is absent from extracted text, use title plus author/venue/year; many legitimate PDFs do not print the DOI in extractable text.
- Use title scores only as triage. Short/generic titles and OCR-poor scans require manual or metadata-assisted review.
- Extract at least the first two pages when the first page is a cover, repository wrapper, or proceedings front page.
- If two IDs share a hash, verify whether the source records are duplicates; otherwise reject the cross-ID reuse.

For books, proceedings, and whole issues:

- Confirm the downloaded PDF is the target chapter/article.
- Reject cover/front matter/table of contents as `front_matter_or_toc_not_target`.
- If only a full issue is available, extract target page range and record source pages.

## File Validation

Run checks equivalent to:

- `file <pdf>`
- `pdfinfo <pdf>` for page count.
- `pdftotext -f 1 -l 1 <pdf> -` for first-page identity.

Reject these from `pdfs/`:

- HTML pages saved as `.pdf`.
- Login/purchase pages.
- Cloudflare "Just a moment" or WAF pages.
- Server 404/500/error pages.
- Wrong article PDFs.
- Non-target front matter or table of contents.

If a file begins with HTTP headers but contains a valid `%PDF` stream later, clean the leading bytes only when `pdfinfo` and first-page text confirm a valid matching PDF. Record the cleanup in notes.

## Audit Notes

Good notes are concrete:

- `downloaded from CEUR-WS paper10.pdf after TOC title confirmation`
- `downloaded from OJS citation_pdf_url`
- `downloaded from DSpace API bitstream content endpoint after view URL returned HTML shell`
- `Purdue-authenticated ScienceDirect attempt stopped on 429`
- `IGI PDF route redirected to access/recommendation form; no institutional PDF stream found`
- `wrong candidate: front matter/table of contents, not target chapter`
- `HTML login page moved to pdfs_rejected`

## Wrong Candidate Handling

- Move wrong files to `pdfs_rejected/` with a reason-bearing filename.
- Mark audit as `wrong_article_suspected`, `html_not_pdf`, or `front_matter_or_toc_not_target`.
- Keep a quarantine/bad-ID list only for confirmed wrong candidates.
- Remove an ID from the bad list immediately after a correct PDF is found and validated.

## 404 and Broken Link Handling

Do not stop at one broken link:

- Record the broken URL and reason.
- Search exact title, DOI, filename, repository handle, conference volume, and publisher landing page.
- Try canonical repository/download/API endpoints.
- Use Internet Archive only for original public PDF URLs that have gone stale.

## Reporting

Report with stable denominators:

- total candidate records
- valid PDFs in `pdfs/`
- usable records if prior coding/extraction already exists
- user-rule exclusions
- remaining retrievable candidates
- remaining by high-level reason and platform group

When the user wants manual help, provide batches of titles/DOIs that have already been tried and avoid repeating titles already sent.

Also report quality-control counts separately from retrieval counts:

- accepted and identity-validated
- candidate found but needs review
- rejected candidates
- corrected/replaced PDFs
- downstream records made stale by replacement
- duplicate-hash conflicts

“Downloaded” alone is never the success metric.

The validator reports its own parser outcome. If a second parser or human check resolves
an exception, retain the original result and append the resolution with the same file
hash and evidence location. Do not rewrite it as an automatic pass. `source_route=existing`
does not establish original acquisition; browser-route labels do not establish who clicked.

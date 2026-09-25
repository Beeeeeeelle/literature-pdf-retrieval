---
name: literature-pdf-retrieval
description: Retrieve and identity-check academic full texts from study lists or existing PDF folders. Use for missing PDFs, institutional-access handoffs, mismatched files, corpus repair, or resuming an auditable retrieval queue; not literature screening or scientific coding.
---

# Literature PDF Retrieval

Start with the study list, existing PDFs and prior audit. Use available search/browser
tools to prepare sources; the bundled scripts validate and extract pages, but do not
search the network or log in. Python 3.10+ and `pypdf` run the helpers. Optional Poppler
provides a second text parser for ambiguous extraction.

Read [access strategy and human handoff](references/access-and-handoff.md) when choosing
routes or requesting human action; [examples](references/examples.md) for new users;
and [workflow details](references/workflow.md) for audit layout and recovery.

## Core Rule

Use only legal access paths: open access, publisher PDFs available through the user's authenticated institution, author/institution repositories, ERIC/PMC/arXiv/CEUR/OJS/DOAJ pages, public ResearchGate downloads, Internet Archive captures of original public PDFs, Zotero Connector/Find Available PDFs, and user-supplied PDFs. Do not bypass paywalls, CAPTCHA, WAF, or login barriers. If no legal full text is available, mark it clearly instead of creating a fake PDF.

## Operating Principles

- Treat retrieval as an auditable pipeline, not a one-off search. Keep durable per-record status, source URL, validation result, notes, and checked date.
- Preserve source IDs, row order, and source files. Write outputs to a new folder or workbook copy unless the user explicitly asks to edit in place.
- Never count a file as found until it is a readable PDF and identity validation passes or is explicitly marked as user-approved.
- Keep wrong, HTML, login, front-matter, full-issue, and suspect files outside the main `pdfs/` folder, usually in `pdfs_rejected/`.
- Reuse authenticated browser sessions. Do not repeatedly ask the user to log in unless the page clearly shows the session expired.
- First try productive routes available without human intervention. When access is needed, inspect the user's institution's library/resolver links and verified holdings. A library link is a route to try, not proof of entitlement or an acquired PDF.
- Give a bounded human handoff: ID/title/DOI, stable landing page, routes tried, observed obstacle, exact action needed, return location and next step. People may sign in, complete MFA, or save and return a PDF. Resume validation after return; do not restart the entire search or accept a file merely because a person supplied it.
- Stop on 429, CAPTCHA, WAF/challenge pages, repeated login prompts, or suspicious redirects. Record the reason and switch strategy.
- Separate **record state** from **attempt history**. Keep one current-state row per study and append one attempt row per URL/tool try; never overwrite the only evidence of a failed route.
- Treat an existing ID-named PDF as an unverified candidate until its identity passes. File presence, a successful HTTP response, or a Zotero attachment is not acceptance.
- Make accepted-PDF replacement atomic: validate in staging, preserve the previous file in quarantine, promote the candidate, update the audit, then invalidate or rerun any downstream extraction based on the old hash.

## Standard Workflow

1. **Set up output**
   - Create `pdfs/`, `pdfs_staging/`, `pdfs_rejected/`, `logs/`, `record_state.csv`, `retrieval_attempts.csv`, and a completed workbook copy.
   - Name files by stable ID: `001.pdf`, `I109.pdf`, or the project's configured ID format.
   - Keep any raw or source-specific file names in audit fields, not in final PDF names.

2. **Read and normalize the study list**
   - Load stable ID, title, year, authors, DOI, URL, source, decision label, and any user inclusion/exclusion flags.
   - Apply user-stated retrieval exclusions before searching, for example language exclusions, datasets/data records, or records outside the project's current scope.
   - Do not exclude non-journal, book chapter, dissertation, report, or conference records unless the user says to.
   - Build current-state columns such as `ID`, bibliographic fields, `PDF filename`, `PDF path`, `source URL`, `source type`, `retrieval status`, `identity status`, `identity basis`, `notes`, `checked date`, `pages`, and `sha256`.
   - Build attempt columns such as `ID`, timestamp, route/tool, requested URL, resolved URL, HTTP/result class, candidate path/hash, validation outcome, and concrete error.

3. **Enrich metadata before expensive retrieval**
   - For missing DOI rows, run exact-title searches in Crossref/OpenAlex/Semantic Scholar/publisher pages and authoritative repositories.
   - If a DOI or stable publisher URL is found, append it to the audit and rerun DOI/platform workflows.
   - Record title variants when the official title expands or slightly differs from the workbook title.

4. **Retrieve in source-priority waves**
   - Start with high-yield public sources: DOI direct PDFs, Unpaywall, ERIC, PMC, arXiv, CEUR, OJS journals, institutional repositories, eScholarship/OhioLINK/ProQuest-open ETDs, JMIR, MDPI, SCITEPRESS, DOAJ journal pages.
   - Then run Zotero/Find Available PDFs if the user can use Zotero or already has a Zotero library/export.
   - Then use authenticated browser/proxy workflows for platform groups in small batches.
   - Deprioritize a platform group after a representative batch repeatedly returns no PDF, access forms, or purchase pages; record that route as tried.
   - Resume from the audit, not from memory. Skip accepted hashes and already exhausted routes unless metadata or access conditions changed.

5. **Validate every candidate**
   - Check file type, nonzero size, readable page count, and text extraction.
   - Reject HTML/login/challenge/error pages even if they were saved with `.pdf`.
   - Verify identity by DOI, first-page title, stable article/chapter ID, or strong first-page author/title match.
   - For books and proceedings, ensure the downloaded file is the target chapter/article, not a cover, front matter, table of contents, or whole issue unless the user requested that.
   - If a PDF has a valid `%PDF` stream after leading HTTP headers, clean it only when `pdfinfo`/`pdftotext` confirm validity, and record the cleanup.
   - Use three identity outcomes: `accepted`, `needs_review`, and `rejected`. A confirmed different target DOI is rejection evidence. A parser conflict blocks automatic acceptance: inspect whether it comes from the target article, a reference, a book identifier, a template placeholder or extraction damage. An absent DOI is not rejection evidence. Short/generic titles, OCR-poor scans, books and proceedings require review rather than a forced score.
   - Detect duplicate hashes across different IDs. Do not silently accept one PDF for multiple studies unless the records are confirmed duplicates.

6. **Sync and report**
   - Rebuild the master audit after each substantial batch.
   - Maintain a remaining queue split by reason: downloaded, excluded by user rule, wrong article, no public PDF, login required, paywalled, rate limited, server error/404, WAF/challenge, or not yet attempted.
   - Report counts using the same denominator each time, and list newly downloaded IDs plus unresolved IDs/reasons when useful.
   - Before reporting completion, run the bundled validator and reconcile: accepted audit rows, accepted files, hashes, and page counts must agree.

## Phase Gates

Do not advance on counts alone:

1. **Inventory gate**: source rows, stable IDs, exclusions, existing files, and prior audit state reconcile.
2. **Candidate gate**: every new file lands in staging and has an attempt record.
3. **Identity gate**: only `accepted` candidates enter `pdfs/`; ambiguous candidates remain reviewable.
4. **Replacement gate**: corrected PDFs preserve the old hash/file and flag downstream outputs as stale.
5. **Completion gate**: the validator passes and every unresolved record has a current actionable reason plus routes tried.

## Platform Strategy

- **No DOI records**: Search exact title first. Look for DOI, repository landing pages, OJS pages, dissertation repositories, arXiv/CEUR, conference proceedings, and public publisher pages. Do not stop after one 404; try title variants and repository records.
- **ScienceDirect/Elsevier**: Use slow authenticated browser batches. Restrict PDF candidates to the current article PII. Stop immediately on 429/login/challenge.
- **Wiley/BERA**: Try `doi/pdfdirect/<doi>?download=true`, `doi/pdf/<doi>`, and `doi/epdf/<doi>` through proxy.
- **Springer**: Try article/chapter/book PDF routes through proxy. For book records, confirm whether the target is whole book, chapter, or front matter.
- **ACM**: Browser/proxy may succeed where direct curl hits Cloudflare. Validate by first-page title because conference titles may be expanded.
- **MDPI/JMIR/CEUR/SCITEPRESS/OJS**: Prefer public PDF endpoints and metadata `citation_pdf_url`. These are high-yield and should usually be tried before proxy routes.
- **OJS and DSpace repositories**: If a view URL returns a web app or HTML shell, try the official download endpoint or DSpace API bitstream content URL; reject the HTML shell.
- **Zenodo/Figshare/Mendeley Data**: Inspect resource type and files. If the record is a dataset/software/image and the user's criteria exclude datasets, mark excluded instead of downloading non-article data files.
- **IGI Global/Routledge/CRC/Emerald/De Gruyter/World Scientific/Inderscience**: Often low-yield or access-form-heavy. Try small authenticated batches; if representative attempts fail, record platform unavailable and move to title/repository/user-supplied routes.
- **ResearchGate**: Use only publicly available full-text/downloads. Do not log in, scrape private copies, or bypass request-only pages.
- **Internet Archive**: Use only to recover an original public PDF URL or page that is now broken. Record the archived original URL.

## Status Labels

Do not mix retrieval, identity, and access conditions in one field. Prefer:

- `retrieval_status`: `not_attempted`, `candidate_found`, `accepted_pdf`, `exhausted_current_routes`, `excluded_by_user_rule`
- `identity_status`: `not_checked`, `accepted`, `needs_review`, `rejected`
- `access_reason`: `none`, `no_public_pdf_found`, `login_required`, `paywalled_or_purchase_only`, `rate_limited`, `waf_or_captcha`, `server_error_or_404`, `html_not_pdf`

Map legacy labels when resuming an older project; do not rewrite history merely to normalize labels.

Legacy/project-specific labels may include:

- `downloaded`
- `user_supplied_pdf`
- `no_public_pdf_found`
- `no_institutional_or_public_pdf_found`
- `login_required`
- `paywalled_or_purchase_only`
- `rate_limited`
- `waf_or_captcha`
- `server_error_or_404`
- `html_not_pdf`
- `wrong_article_suspected`
- `front_matter_or_toc_not_target`
- `full_issue_needs_extraction`
- `excluded_by_user_rule`
- `not_attempted`

## Validation Checklist

- The main `pdfs/` folder contains only accepted PDF files.
- PDF count, downloaded audit rows, and master availability counts agree.
- Every downloaded row has source URL, source type, pages, validation status, notes, and checked date.
- Every accepted PDF has DOI match, title match, stable article/chapter ID match, or documented manual/user approval.
- Wrong or suspect files are moved to `pdfs_rejected/` and marked in audit.
- Previously wrong IDs are removed from quarantine/bad-ID lists once a correct PDF is found.
- Remaining rows are categorized by actionable reason, not just "missing."
- Duplicate hashes across different IDs are either explained as true duplicate records or rejected.
- Any downstream coding/extraction tied to a replaced hash is marked stale and rerun before it is treated as final.

For project layout, browser handoff, recovery, validation thresholds, and platform edge cases, read `references/workflow.md`. Run `scripts/validate_pdf_audit.py --help` before the final reconciliation pass. Use `--require-identity` for a strict automatic gate. Early-page DOI/title checks are triage, not proof of completeness or final publication version. Preserve parser flags separately from subsequent checks and human decisions.

## Hand off to review

Deliver accepted PDFs, `record_state.csv`, `retrieval_attempts.csv`, validation evidence
and an actionable remaining queue. The optional companion `review-evidence-workflow`
can consume that audit with `prepare_sources.py` and recheck files before coding.
This skill works independently; screening, codebooks and reviewer judgments belong to
the review workflow. Report file acquisition separately from identity acceptance.

# Validation scope

Checked on 2026-09-25. This package contains agent instructions plus local PDF helpers;
it is not an autonomous downloader. Public tests use synthetic PDFs and no credentials.

## Checks performed

| Check | Observed result | What it establishes |
|---|---|---|
| Codex skill-creator structural validator | Passed | Skill frontmatter and package naming satisfy that validator |
| `python -m unittest discover -s tests -v` | 16 tests passed locally with Python 3.12.14 / pypdf 6.10.0 | Specified local helper behavior |
| Queue-only sample from `examples/` | 2 records, 0 accepted, 0 files, no audit errors | A valid unresolved queue is distinct from retrieval success |
| Current Agency audit without header conversion | 130 accepted-labelled rows checked, no audit schema errors | Legacy `Record_ID` / `accepted_pdf` / `downloaded_validated` interoperability |
| Current Agency files | 0 structural failures, 0 cross-ID duplicate hashes, 0 unreferenced files | Local file reconciliation; all recorded hashes/page counts also matched in a separate read-only comparison |
| Agency early-text identity triage | 127 passes, 2 DOI flags, 1 insufficient-evidence flag | Conservative automated checks retained uncertainty |
| Secondary parser follow-up | Expected DOI corroborated for 2 flags; 1 version unresolved | Parser disagreement and version ambiguity are different problems |

The public CI workflow runs the 16 helper tests on Python 3.10 and 3.12; see the
[Actions history](https://github.com/Beeeeeeelle/literature-pdf-retrieval/actions)
for actual remote run results. CI does not contain or fetch the Agency corpus.

## What the synthetic tests cover

- Correct DOI, conflicting DOI despite title agreement, and uncertain identity under a strict gate.
- Project header aliases, custom acceptance labels and relative/absolute file paths.
- Missing columns, blank/duplicate IDs, orphan PDF files and explicit missing paths.
- HTML disguised as PDF and identical files assigned to different records.
- Valid unresolved queues and invalid text-page settings.
- Inclusive page extraction, invalid ranges, source preservation and refusal to overwrite.

The tests found and addressed two portability gaps in the previous local helper: project
header/status variants could be silently skipped, and page extraction lacked explicit
range/overwrite guards. The packaged validator reports schema errors and status counts;
unreferenced files prevent a zero-checked false success.

## Agency follow-up, with bounded claims

The original project ledger labelled all 130 records `downloaded_validated`. This
recheck preserved that historical state and reported current observations separately:

| Record | Initial parser evidence | Follow-up on the same file | Remaining boundary |
|---|---|---|---|
| MR00075 | Book DOI extracted without expected chapter suffix | Poppler extracted the expected chapter DOI | Corroboration, not an invented human approval |
| MR00905 | Insufficient English-title/DOI text from a Chinese article | Poppler extracted the expected DOI | Corroboration, not a completeness certification |
| MR01071 | Title match with a template DOI | Anonymous author placeholders; expected DOI absent | Version identity remains unresolved |

The strict automated run correctly returned **nonzero** for its three original flags.
Secondary checks did not rewrite that result into an all-pass report. Neither the source
PDFs nor the project's research judgments were changed.

This is a bounded implementation example, not a controlled accuracy study. Full-text
files and private access logs are not redistributed. Local detailed reports retain file
hashes, parser outcomes and follow-up checks; the public synthetic tests are independently
runnable. The historical TALL retrieval totals belong to a different process and are
not reported as a test of this new package.

## Still unestablished

Cross-institution retrieval coverage, semantic identity sensitivity/specificity, final
version detection, OCR handling, human usability and comparative time savings require
further evaluation. A second autonomous agent cold-start test was not run for this
standalone release. Do not interpret structural validation or helper tests as those results.

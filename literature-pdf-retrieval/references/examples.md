# Starting requests and expected outputs

## Start from a list

> Use $literature-pdf-retrieval. This CSV has stable IDs, titles and some DOIs. Start with
> my existing PDFs, find missing sources, and check each file against its record. Tell
> me exactly which items need my access.

Preserve originals, reconcile candidates and use a new output folder. Start public work
before asking about optional access. Deliver an audit, accepted files and a queue.

## Use institutional access

> My university is [institution]. I may already be signed in. Check what the library
> provides for these papers. If I need to log in or save a file, give me the precise next
> step; continue other records meanwhile.

Inspect observed access. The institution name is not proof of entitlement. Keep access
handoffs separate from identity review.

## Resume after manual downloads

> Here are the PDFs I saved and the earlier audit. Match them to pending IDs, validate
> them, and continue. Do not overwrite an accepted file.

Stage candidates, compare identity and hashes, and retain unmatched files. If a corrected
source replaces an earlier one, record both hashes and flag affected downstream coding.

## Repair a suspicious corpus

> Filenames look correct, but some may be wrong articles or front matter. Audit this
> folder against the study list and identify what needs replacement or manual checking.

Do not trust filenames or previous downloaded labels. A parser conflict remains visible
even when later checks find a plausible explanation.

## Fictional completion example

> Of 20 targets, 15 have accepted sources, 2 have readable candidates awaiting identity
> checks, 2 need institutional access, and 1 has no copy on routes tried. Your action list
> gives landing pages and a return folder. Accepted sources can proceed while five remain explicit.

This is a sample, not a measured retrieval result. Never invent human actions or decisions
to close a queue.

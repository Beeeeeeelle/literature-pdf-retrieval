# Access strategy and human handoff

The sequence is a preference, not a fixed list every record must exhaust. Reuse accepted
files and previous attempts; group missing records by DOI, host and source type.

| Observation | Agent action | Human contribution / stopping point |
|---|---|---|
| Existing file or prior attempt | Reconcile ID, hash and audit before searching | Clarify scope only when missing |
| Missing DOI or broken link | Search exact title/author and authoritative metadata; retain title variants | Resolve competing reports when needed |
| Public full text likely | Try publisher OA, repositories or available OA tools | Usually no action |
| Direct access fails; institution known | Inspect official library catalogue/resolver and item holdings; try the authorized publisher route | Sign in or complete MFA when required |
| PDF visible but tool cannot save | Give a verified landing page and precise save/return instructions | Save the PDF and return it to staging |
| No subscription confirmed | Try author/institutional copies or existing user/Zotero files; prepare an optional library-request route | Choose document delivery; no request sent or purchase made without authorization |
| 429, challenge or repeated login | Log failure, pause that route and switch permitted source | Human may resolve access; agent does not bypass it |
| Candidate arrives | Validate readability, identity, completeness and hash | Resolve ambiguous versions or identity |

Use tools actually available. Do not promise coverage from an institution name, a DOI
redirect or another article on the platform. Do not collect passwords or store session
tokens. Keep stable landing URLs; omit credential-bearing URLs from shareable logs.

## A useful handoff is specific

```text
Record: R017 — [full title], [DOI]
Tried: publisher public route; repository search; institutional resolver
Obstacle: library route reaches sign-in; PDF bytes not yet acquired
Your step: open [stable library/article page], sign in, save the article PDF
Return: place R017.pdf in the agreed incoming folder or attach it here
Next: I compare identity/pages, record the hash, and update the queue
```

Ask only for the current necessary action. Reuse a working authenticated session. Continue
accessible records while people handle blocked items. A returned PDF receives the same
checks as an automatic download. Retain attempts so future runs do not repeat exhausted routes.

## Three distinct completion questions

1. **Was a file obtained?** Readable bytes exist; a link or HTML wrapper is insufficient.
2. **Is it the intended usable report?** Check identity, article/chapter, version and completeness.
3. **Is the retrieval stage reconciled?** Audit, files, hashes and remaining reasons agree.

Acquisition does not complete scientific screening. If permitted routes do not work,
deliver a reasoned queue. Full coverage in one project does not promise the same result
for another institution, topic or publication period.

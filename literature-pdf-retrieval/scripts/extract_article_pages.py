#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract article pages from a full issue PDF.")
    parser.add_argument("source_pdf")
    parser.add_argument("output_pdf")
    parser.add_argument("--start", type=int, required=True, help="1-based source PDF start page")
    parser.add_argument("--end", type=int, required=True, help="1-based source PDF end page, inclusive")
    args = parser.parse_args()

    source = Path(args.source_pdf)
    output = Path(args.output_pdf)
    if source.resolve() == output.resolve():
        parser.error("output must differ from source; preserve the original PDF")
    if output.exists():
        parser.error("output already exists; choose a new staging filename")
    reader = PdfReader(str(source))
    if not 1 <= args.start <= args.end <= len(reader.pages):
        parser.error(f"page range must satisfy 1 <= start <= end <= {len(reader.pages)}")
    writer = PdfWriter()
    for page_no in range(args.start, args.end + 1):
        writer.add_page(reader.pages[page_no - 1])
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as f:
        writer.write(f)
    print({"output": str(output), "pages": len(PdfReader(str(output)).pages)})


if __name__ == "__main__":
    main()

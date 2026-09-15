---
name: scanned-pdf-to-epub
description: Use when scanned Chinese PDFs or image-only books need text EPUB conversion on macOS, Windows, or Linux, especially when OCR text, original underlined proper names, 专名号, or WeRead/微信读书 compatibility matters.
---

# Scanned PDF To EPUB

## Overview

Convert scanned Chinese PDFs into readable text EPUBs without losing editorial aids such as underlined names. The workflow is cross-platform: choose OCR and rendering tools available on the user's machine, verify a small sample first, then scale.

## Workflow

1. Inspect the PDF.
   - Use `pdfinfo`/Poppler when available, or Python libraries such as `pypdf`, `PyMuPDF`, or `pypdfium2` for page count, metadata, page size, text layer, outline/bookmarks.
   - If `extract_text()` is empty on early pages, treat it as scan/OCR work.
   - Render a few pages with Poppler, PyMuPDF, or pypdfium2 and visually locate title, table of contents, and first body page.

2. Build a sample before full conversion.
   - Pick title/front matter plus one complete short section.
   - Confirm PDF page number vs printed page number offset.
   - Make the EPUB title, nav, and NCX point to real section starts.

3. OCR text with coordinates.
   - Prefer OCR that returns text boxes/character boxes.
   - On Windows, prefer PaddleOCR for local Chinese OCR; use Tesseract only as a fallback for simpler pages. Cloud OCR such as Azure, Baidu, Tencent, or Google is acceptable when privacy/cost is acceptable.
   - On macOS, Vision OCR via a tiny Swift helper is a good local default; PaddleOCR is also fine for portability.
   - On Linux, prefer PaddleOCR or Tesseract, with cloud OCR as the high-accuracy fallback.
   - If OCR returns only line/word boxes, estimate character boxes from the line box and text length; mark underline detection as lower confidence.
   - Sort lines by page coordinates; remove page headers, marginal running titles, and page numbers. In every text path (including the main body), merge same-row OCR fragments left-to-right **before** computing indentation. Carry character boxes through the merge for proper-name marking; a fragment starting far to the right is not evidence of a new paragraph.
   - Use OCR text for layout/alignment, then校对 against reliable text when available.
   - Reconstruct paragraphs across pages in **all prose**, including 前记、序跋 and commentary. A PDF page boundary must not create a new paragraph. Keep a paragraph buffer across pages; determine actual breaks from page-local text-region indentation, block style and headings. Do not use punctuation alone, raw x coordinates across facing pages, or one `<p>` per page.
   - Use [logical row merging](scripts/paragraphs.py) before paragraph accumulation in both front matter and body; it preserves character boxes. Calibrate row tolerance to OCR coordinates and process columns separately.
   - Read [paragraph reconstruction](references/implementation-notes.md#paragraph-reconstruction-across-pages) before assembling XHTML. The optional [paragraph accumulator](scripts/paragraphs.py) supports horizontal prose when supplied with verified region-relative indentation; calibrate its inset-block assumptions to the source edition.

4. Preserve original underlined proper names.
   - Detect underlines from images as horizontal strokes near the bottom of OCR character boxes.
   - If character boxes are estimated, compare the detected stroke span against the estimated character centers and manually review more tokens.
   - Apply detection only to body lines, not headings; headings create false positives from Hanzi strokes.
   - Convert detected spans into semantic markup before styling, e.g. `<span class="proper-name">周威烈王</span>`.

5. Choose WeRead marking strategy.
   - For 微信读书 App and web together, prefer **font/weight marking** over underline:
     `<strong class="proper-name" style="font-family:'Kaiti SC','STKaiti','KaiTi','楷体','FangSong','STFangsong',serif;font-weight:700;text-decoration:none;border:0;background:transparent;">周威烈王</strong>`
   - Do not use `border-bottom` for WeRead web; its column layout can stretch borders across lines/columns.
   - Do not mix Unicode combining underline marks with web CSS in one WeRead file; web may render combining marks as misplaced strokes.
   - If the user insists on real underlines, produce separate App and web editions. See [implementation notes](references/implementation-notes.md).

6. Package and validate EPUB.
   - Use EPUB3: `mimetype`, `META-INF/container.xml`, `OEBPS/content.opf`, `nav.xhtml`, and `toc.ncx`.
   - XHTML must parse as XML. Zip `mimetype` first and uncompressed.
   - Validate with `unzip -t`; parse OPF/nav/NCX/XHTML with XML parser.
   - Audit every page boundary as `join`, `new-paragraph`, or section transition; inspect ambiguous cases in the source. Check known continuations in the generated XHTML are inside one `<p>`, and verify actual new paragraphs and chapter boundaries remain separate. Include front matter and indented commentary in this check; XML/ZIP validity does not validate reading order or paragraph structure.
   - Treat reader rendering as a separate check: compare visible column-boundary text against XHTML on the target reader. If text exists in the EPUB but is missing onscreen, investigate import parsing/rendering; a no-markup comparison edition can test style involvement, but do not claim a confirmed cause or fix without reproducing the result.
   - Report sample scope, remaining OCR risk, and which reader edition to use.

## Common Mistakes

- Making an image-only EPUB when the user asked for a text EPUB.
- Splitting prose at PDF page boundaries, or merging all pages into one paragraph without preserving genuine paragraph starts.
- Removing full-width prose with a fixed margin-x filter; scan alignment can shift between pages.
- Trusting OCR without a校对 pass on names, dynasties, and section starts.
- Treating WeRead App and WeRead web as the same renderer.
- Using `border-bottom` as an underline fallback in WeRead web.
- Leaving Unicode combining underline marks in a web-targeted EPUB.
- Applying underline detection to headings or TOC pages.

## When More Detail Is Needed

Read [implementation-notes.md](references/implementation-notes.md) for cross-platform OCR choices, Windows PaddleOCR setup, macOS Vision helper shape, underline detection heuristics, EPUB packaging checks, and WeRead compatibility variants.

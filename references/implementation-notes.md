# Implementation Notes

## Cross-Platform Tooling Pattern

Use the same logical pipeline everywhere: inspect PDF, render pages, OCR with coordinates, detect printed underlines, package EPUB. Swap tools by platform.

### Shared Python Dependencies

Run [environment preparation](environment-setup.md) first. Do not install every backend listed in this reference. Choose one PDF renderer and one OCR backend, reuse working equivalents, and add only the packages the conversion code actually imports. Use a task-local virtual environment for new Python dependencies.

Typical roles: `pypdf` for metadata/text-layer inspection; `PyMuPDF` **or** `pypdfium2` for rendering; `Pillow` for images; `numpy` or `opencv-python` for image analysis. Python's standard `zipfile` and `xml.etree.ElementTree` can package and structurally validate EPUB without installing `lxml`.

### macOS

- In Codex Desktop, prefer bundled tools when available:
  - `load_workspace_dependencies`
  - bundled `pdfinfo`, `pdftoppm`, Python, `PIL`, `pypdf`, `lxml`
- If Poppler is installed, `pdfinfo` and `pdftoppm` are excellent for inspection/rendering.
- For local OCR, create a temporary Swift helper using Vision:
  - Input: rendered JPEG/PNG page.
  - Output JSON: lines, line boxes, confidence, per-character boxes.
  - Set `recognitionLevel = .accurate`, `usesLanguageCorrection = false`, languages `zh-Hans`, `zh-Hant`, `en-US`.
- PaddleOCR is also a good macOS choice when cross-platform reproducibility matters more than using native APIs.

### Windows

Prepare an isolated Python environment as described in [environment setup](environment-setup.md), then choose a compatible PaddleOCR/PaddlePaddle combination for that interpreter and machine. Check the backend's official installation guidance and installed API version before using the illustrative OCR code below; package installation alone does not download or validate all required Chinese models.

Notes:
- Use PaddleOCR as the first Windows OCR choice for Chinese books. It is usually better than Tesseract on dense classical Chinese scans.
- Use `PyMuPDF` or `pypdfium2` for rendering pages. This avoids making every Windows user install Poppler first.
- If Poppler is installed separately, `pdfinfo.exe`/`pdftoppm.exe` are still fine.
- Tesseract is acceptable for clean modern scans but often struggles with classical Chinese punctuation, vertical noise, and rare characters.
- Cloud OCR such as Azure AI Vision, Baidu OCR, Tencent OCR, Google Vision, or ABBYY can be used when higher accuracy is worth the privacy/cost tradeoff.

Minimal Windows rendering example:

```python
import fitz

doc = fitz.open("book.pdf")
page = doc[0]
pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
pix.save("page-001.png")
```

Minimal PaddleOCR shape:

```python
from paddleocr import PaddleOCR

ocr = PaddleOCR(use_angle_cls=True, lang="ch")
result = ocr.ocr("page-001.png", cls=True)
for page in result:
    for box, (text, confidence) in page:
        print(text, confidence, box)
```

PaddleOCR commonly returns line boxes rather than reliable per-character boxes. For underline mapping, estimate each character's horizontal span inside the line box and then manually review detected tokens.

### Linux

- Use PaddleOCR for local Chinese OCR.
- Use Poppler (`pdfinfo`, `pdftoppm`) when available; otherwise render with `PyMuPDF` or `pypdfium2`.
- Use cloud OCR when local OCR quality is not enough.

## OCR And 校对

- Use rendered images around 180 DPI for OCR samples.
- Sort OCR lines top-to-bottom using normalized boxes; OCR engines may return lines out of reading order.
- Remove noise:
  - single-character page numbers at margins,
  - vertical running titles such as `通 / 鉴 / 纪 / 事 / 本 / 末`,
  - blank or decorative pages.
- If a public or user-provided text source exists, use it as校对底稿. Keep the edition in mind; do not blindly replace OCR if wording differs from the scanned edition.
- On Windows/PaddleOCR, expect more line-level boxes. Preserve the OCR line text and use校对 text to fix characters, but keep the PDF-derived line breaks until section structure is stable.

## Paragraph Reconstruction Across Pages

Keep source page IDs and line boxes until paragraph reconstruction is complete. Apply the same reconstruction to front matter, prefaces, afterwords and the main text. Do not wrap each PDF page in its own `<p>` or insert `<br/>` at scan-page boundaries.

1. Remove running titles and page numbers using their marginal position **and** narrow geometry. Verify that this does not remove full-width lines when the scan shifts left or right. Cluster fragments with overlapping vertical extents into logical lines and order each row left-to-right before testing indentation; a right-hand OCR fragment is not a new paragraph.
2. Estimate the prose region and character pitch for each page, using full lines, adjacent comparable pages and source images. Compare a line's left edge with its **own page's region**, not the previous page's raw x coordinate. Do not blindly use the most frequent left edge: a page dominated by inset commentary can shift that estimate.
3. Carry the open paragraph and block style to the next page. Continue a nonindented first line without adding a newline or space between Chinese characters. Start a new paragraph only with positive evidence such as first-line indentation relative to that block, a heading or an explicit section transition. A sentence-ending full stop alone does not prove a paragraph boundary; absence of punctuation alone does not override a real heading.
4. Preserve inset commentary: in an edition with two-character block indentation and an additional two-character first-line indentation, offset 4 starts a paragraph within the block, offset 2 continues it, and offset 0 returns to ordinary prose. A short completed last line followed by an offset-2 first line can indicate a return to ordinary prose; verify this against the scan and supply the line-end gap to the helper. Calibrate these levels to the actual edition. The optional `scripts/paragraphs.py` implements this specific horizontal-prose pattern; supply normalized character offsets and reset at section boundaries. Signatures, poetry, tables and vertical text require separate layout handling.
5. Record each page transition with the previous tail, next head, decision and geometry. Review uncertain transitions against both source pages. Assert the final XHTML holds verified continued phrases in a single paragraph, while preserving known true paragraph starts. Check text conservation so paragraph repairs do not drop, reorder or duplicate lines.

Regression examples from a scanned *通鉴纪事本末* first volume:

- PDF pages 9–10: `藩镇之乱` + `则令孜之为也` belongs to one paragraph in the original 序. A per-page paragraph wrapper incorrectly separates it.
- PDF page 40: `蜀既属秦，秦以益强富厚，轻诸侯。` and `燕王哙以国让其相` are OCR fragments of the same printed row. Merge them before indentation detection; otherwise the right-hand fragment becomes a false paragraph. Assert the next row `子之。` remains in that paragraph. Run this regression against the **body** assembly path, not just the front-matter helper.
- A genuine paragraph may begin at the top of the next page; retain its source indentation rather than merging every page boundary.
- Inset commentary can continue onto a page containing ordinary prose below it. Its two-character block margin must not turn every commentary line into a new paragraph.
- Full-width lines in front matter may shift slightly beyond a fixed margin cutoff; do not delete them while filtering narrow running titles.

### Using The Helpers

```python
from paragraphs import merge_logical_rows, Paragraphs

paragraphs = Paragraphs()  # Keep this instance across pages of one section.
# For each page and each horizontal prose column, after removing margins:
rows = merge_logical_rows(ocr_lines, center_tolerance=calibrated_tolerance)
for row in rows:
    x, y, width, height = row["box"]
    # Use row["chars"] with the original page image for proper-name detection.
    paragraphs.feed(
        row["text"], rendered_markup(row), page=page_number,
        offset_chars=(x - region_left) / character_pitch,
        end_gap_chars=(region_right - x - width) / character_pitch,
    )
# At a real section boundary, finish and start a fresh accumulator.
html_paragraphs = paragraphs.finish()
```

`center_tolerance` uses the same units as the OCR boxes and must be less than the separation between adjacent printed rows. Feed one page/column at a time; preserve the resulting row order. The example leaves region detection, escaping and semantic markup to the caller, because these depend on the source edition and OCR backend.

## Underline Detection Heuristic

Use character boxes, or estimated character positions, to detect original printed name underlines:

1. For each body line, inspect rows near the bottom of the line bbox.
2. Threshold dark pixels and find horizontal runs with small gaps.
3. Merge adjacent row-runs into stroke segments.
4. Mark a character underlined when its center or enough of its width overlaps a stroke.
   - If true character boxes are unavailable, distribute character centers across the OCR line box. This is less precise but usable for sample generation.
5. Join adjacent marked characters into tokens.
6. Filter false positives:
   - skip punctuation;
   - skip single common characters unless they are dynastic/state names;
   - skip headings and oversized text;
   - manually review the first page token list.

Known false-positive classes:
- Hanzi long horizontal strokes mistaken for underline.
- Headings and title text.
- OCR-attached particles, e.g. `平阳也` should become `平阳`.

Windows/PaddleOCR review rule:
- Treat every underline token from estimated character positions as provisional.
- Review the first 2-3 pages visually before batch conversion.
- If many tokens shift by one character, apply a small global offset to estimated character centers for that OCR/rendering setup, then re-review.

## WeRead Compatibility

微信读书 App and web behave differently.

Preferred universal strategy:

```html
<strong class="proper-name" style="font-family:'Kaiti SC','STKaiti','KaiTi','楷体','FangSong','STFangsong',serif;font-weight:700;font-style:normal;text-decoration:none;border:0;background:transparent;">周威烈王</strong>
```

Rationale:
- App often strips CSS underline but preserves text and may preserve bold/font cues.
- Web can mishandle Unicode combining marks.
- Bold + kai/fangsong-style font is more stable than underline across both endpoints.

If real underline is required:

- App edition:
  - Unicode combining marks may survive where CSS does not.
  - `U+035F` creates a connected line but may shift left/right depending on font.
  - Half-line marks (`FE27`, `FE2D`, `FE28`) can be tested when alignment is off.
- Web edition:
  - Use only `text-decoration: underline`.
  - Do not use `border-bottom`; WeRead web column layout can stretch it into long unrelated lines.
  - Do not include Unicode combining underline marks.

Keep these as separate files when necessary. A single “hybrid” file can pollute one renderer while fixing the other.

## EPUB Packaging Checklist

Required:
- `mimetype` first in zip, stored/uncompressed.
- `META-INF/container.xml`.
- `OEBPS/content.opf`.
- `OEBPS/nav.xhtml` with EPUB3 nav.
- `OEBPS/toc.ncx` for older readers.
- XHTML files must be XML-valid.

Validation commands:

```bash
unzip -t book.epub
python3 - <<'PY'
from zipfile import ZipFile, ZIP_STORED
from xml.etree import ElementTree as ET
p = "book.epub"
with ZipFile(p) as z:
    assert z.infolist()[0].filename == "mimetype"
    assert z.infolist()[0].compress_type == ZIP_STORED
    for name in ["META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml", "OEBPS/toc.ncx"]:
        ET.fromstring(z.read(name))
PY
```

PowerShell equivalent:

```powershell
tar -tf .\book.epub
@'
from zipfile import ZipFile, ZIP_STORED
from xml.etree import ElementTree as ET
p = "book.epub"
with ZipFile(p) as z:
    assert z.infolist()[0].filename == "mimetype"
    assert z.infolist()[0].compress_type == ZIP_STORED
    for name in ["META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml", "OEBPS/toc.ncx"]:
        ET.fromstring(z.read(name))
'@ | python -
```

## Output Naming

Use explicit reader-target suffixes:

- `_文字样章_专名楷体版.epub` for the universal recommended edition.
- `_微信读书App下划线版.epub` for Unicode underline experiments.
- `_微信读书网页版下划线版.epub` for pure CSS underline experiments.

In the final response, state which file is recommended for which reader.

## Sharing Notes

For Claude Code users, install this skill at:

- macOS/Linux: `~/.claude/skills/scanned-pdf-to-epub`
- Windows: `%USERPROFILE%\.claude\skills\scanned-pdf-to-epub`

For Codex users, install at:

- macOS/Linux: `~/.codex/skills/scanned-pdf-to-epub`
- Windows: `%USERPROFILE%\.codex\skills\scanned-pdf-to-epub`

When sharing publicly, mention that OCR quality depends on the selected OCR backend. The skill is a workflow and compatibility guide; it does not bundle Apple Vision, PaddleOCR models, cloud OCR credentials, or copyrighted source texts.

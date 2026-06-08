# Implementation Notes

## Cross-Platform Tooling Pattern

Use the same logical pipeline everywhere: inspect PDF, render pages, OCR with coordinates, detect printed underlines, package EPUB. Swap tools by platform.

### Shared Python Dependencies

Install these into the active Python environment when the host does not already provide equivalents:

```bash
python -m pip install pillow pypdf lxml pymupdf pypdfium2 opencv-python
```

Use `pypdf` to inspect metadata and confirm whether a text layer exists. Use `PyMuPDF` or `pypdfium2` to render pages when Poppler is unavailable.

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

Recommended local stack:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install paddleocr paddlepaddle opencv-python pillow pypdf lxml pymupdf pypdfium2
```

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

- macOS/Linux: `~/.claude/skills/scanned-pdf-to-weread-epub`
- Windows: `%USERPROFILE%\.claude\skills\scanned-pdf-to-weread-epub`

For Codex users, install at:

- macOS/Linux: `~/.codex/skills/scanned-pdf-to-weread-epub`
- Windows: `%USERPROFILE%\.codex\skills\scanned-pdf-to-weread-epub`

When sharing publicly, mention that OCR quality depends on the selected OCR backend. The skill is a workflow and compatibility guide; it does not bundle Apple Vision, PaddleOCR models, cloud OCR credentials, or copyrighted source texts.

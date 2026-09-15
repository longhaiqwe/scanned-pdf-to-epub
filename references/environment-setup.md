# Environment Check And Setup

Do this before the conversion workflow. The agent handles discovery and routine setup; the user supplies the book and desired result, not a dependency checklist. Keep preparation inside the task's scope and reuse existing authorization.

## 1. Inventory Before Installing

Detect OS/architecture, available disk space in the output location, and usable executable paths. In a hosted agent, check its supplied runtime/dependency tools first (for example Codex's `load_workspace_dependencies` when available). Do not assume those tools exist in another agent host.

Check the actual Python interpreter's version and imports, not just package names listed under a different Python. Inspect:

- Python 3 and its `venv`/`pip` availability when installation is needed.
- One PDF inspection/rendering route: PyMuPDF, pypdfium2, or Poppler (`pdfinfo`, `pdftoppm`). A working renderer can often also supply page metadata; add `pypdf` only if needed.
- Image libraries used by the selected code: Pillow, and NumPy or OpenCV for pixel analysis.
- One Chinese OCR route, including usable language models and coordinate output.
- Python standard-library ZIP/XML support for packaging. `lxml`, `unzip`, and EPUBCheck are additional options, not all mandatory.

For shell discovery, use `command -v` on macOS/Linux or `Get-Command` on PowerShell. Resolve Python explicitly (`python3`, `py -3`, or the host-provided absolute path); run import/version checks with that same interpreter. A binary in PATH or a discoverable Python module still needs a real execution check.

## 2. Choose One Working Pipeline

| Environment | OCR route to check first | PDF rendering options |
| --- | --- | --- |
| macOS | System Vision through a Swift helper, if the compiler and required SDK frameworks work | Existing Poppler, PyMuPDF, or pypdfium2 |
| Windows | A compatible local PaddleOCR/PaddlePaddle installation with Chinese models | PyMuPDF or pypdfium2; existing Poppler also works |
| Linux | Existing PaddleOCR or Tesseract with Chinese language data, checking scan quality | Existing Poppler, PyMuPDF, or pypdfium2 |

On macOS, verify `swiftc` can compile a minimal helper importing Vision and the chosen rendering frameworks; merely finding `swift` is insufficient. If compiler/SDK setup is missing, explain the system installation needed or use another already-working OCR route. Do not require a full Xcode application if the selected toolchain already works.

For PaddleOCR or other version-sensitive backends, inspect the interpreter/platform compatibility and consult the backend's official instructions for the chosen version before installing. Check installed APIs before writing calls; do not assume examples for another major version apply. Start with a supported CPU route when GPU acceleration is unnecessary; do not add GPU drivers as an incidental dependency.

Cloud OCR is a separate choice involving upload and possibly charges. Keep local processing as the default and verify specific authorization before sending book pages to a service.

## 3. Install Only What Is Missing

Tell the user briefly which working tools will be reused and what needs installation. Proceed with ordinary task-local package setup when permitted; do not stop merely to ask the user to run commands the agent can execute.

Create a virtual environment in the conversion work directory, outside the installed Skill and other projects. Pick a new name if `.venv` belongs to unrelated work. Invoke its Python directly so activation state cannot accidentally select another interpreter.

macOS/Linux, with `python3` replaced by the chosen interpreter if necessary:

```bash
python3 -m venv .venv
.venv/bin/python -m pip --version
```

Windows PowerShell, when the Python launcher is available:

```powershell
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip --version
```

Install only the selected code's missing packages using that environment's `python -m pip install ...`. For example, a PDFium/Pillow/NumPy pipeline may need `pypdfium2 pillow numpy`; this is not a requirement to install them when another renderer or host runtime already works. Do not upgrade working global environments or install all alternative renderers/OCR engines.

OCR models may require a separate first-run download. Explain that download before starting it, use the backend's official model source, and confirm the model loads locally before declaring OCR ready. Model download is distinct from uploading the user's PDF.

For system-wide packages/toolchains, paid services or external uploads, use existing authorization and the host's permission rules. If authorization is missing, identify the exact action and reason and ask once. Do not use administrator privileges, change global security settings, or substitute a paid/cloud service simply to bypass a setup failure.

If network access or installation is unavailable, try a working local equivalent. Otherwise report the missing capability, actual error and tailored installation command; do not continue into a full-book job that cannot succeed.

## 4. Verify One Real Page

Choose a representative body page rather than a blank cover. Use the selected interpreter and executables for the complete test:

1. Open the supplied PDF, confirm page count and render the selected page. Open the output image to verify it contains the intended text at readable resolution.
2. Run Chinese OCR. Check recognizable Chinese text, plausible reading order and nonempty line/character boxes in the documented coordinate system. Inspect a few names against the image. English-only recognition, empty output or nonsensical Chinese fails this check.
3. Build a minimal text EPUB from that page. Confirm the XHTML contains the recognized text, its XML parses, resources resolve, and `mimetype` is the first ZIP entry and uncompressed. An image-only EPUB does not pass.
4. Keep the result and record selected executable paths, relevant package/backend versions, OCR language/model configuration and any limitations in the task output directory. Do not record credentials.

Only then proceed to the workflow's complete short-section sample and full conversion. Environment readiness, OCR accuracy, EPUB structure and target-reader rendering remain separate checks; the single-page test does not certify the whole book or WeRead compatibility.

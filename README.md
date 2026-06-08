# scanned-pdf-to-weread-epub

一个用于把扫描版中文 PDF / 图片书转换成文字版 EPUB 的 Agent Skill，重点处理：

- OCR 文字版 EPUB，而不是图片版 EPUB
- 原书下划线专名号 / 人名标记的保留
- 微信读书 App 和网页版的兼容差异
- macOS、Windows、Linux 的 OCR 工具选择

## Install For Codex

macOS / Linux:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/longhaiqwe/scanned-pdf-to-weread-epub.git ~/.codex/skills/scanned-pdf-to-weread-epub
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/longhaiqwe/scanned-pdf-to-weread-epub.git "$env:USERPROFILE\.codex\skills\scanned-pdf-to-weread-epub"
```

## Install For Claude Code

macOS / Linux:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/longhaiqwe/scanned-pdf-to-weread-epub.git ~/.claude/skills/scanned-pdf-to-weread-epub
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
git clone https://github.com/longhaiqwe/scanned-pdf-to-weread-epub.git "$env:USERPROFILE\.claude\skills\scanned-pdf-to-weread-epub"
```

After installing, start a new Codex / Claude Code session, then ask:

```text
Use scanned-pdf-to-weread-epub to convert this scanned Chinese PDF into a text EPUB for WeRead.
```

## Windows OCR Notes

This skill does not require Apple Vision OCR. On Windows, prefer:

- PaddleOCR for local Chinese OCR
- PyMuPDF or pypdfium2 for PDF rendering
- Tesseract only as a fallback for cleaner/simple scans
- Azure/Baidu/Tencent/Google/ABBYY OCR when cloud OCR is acceptable

See [implementation notes](references/implementation-notes.md) for details.

## License

MIT

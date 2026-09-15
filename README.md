# scanned-pdf-to-epub

一个用于把扫描版中文 PDF / 图片书转换成文字版 EPUB 的 Agent Skill，重点处理：

- 可搜索、可重排的 OCR 文字版 EPUB
- 跨页段落续接，以及同一行 OCR 碎片合并
- 前记、序跋和正文统一处理，保留真实段落与缩进评注
- 原书下划线专名号 / 人名标记的保留
- 微信读书 App 和网页版的兼容差异
- macOS、Windows、Linux 的 OCR 工具选择

## Install For Codex

macOS / Linux:

```bash
mkdir -p ~/.codex/skills
git clone https://github.com/longhaiqwe/scanned-pdf-to-epub.git ~/.codex/skills/scanned-pdf-to-epub
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
git clone https://github.com/longhaiqwe/scanned-pdf-to-epub.git "$env:USERPROFILE\.codex\skills\scanned-pdf-to-epub"
```

## Install For Claude Code

macOS / Linux:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/longhaiqwe/scanned-pdf-to-epub.git ~/.claude/skills/scanned-pdf-to-epub
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills" | Out-Null
git clone https://github.com/longhaiqwe/scanned-pdf-to-epub.git "$env:USERPROFILE\.claude\skills\scanned-pdf-to-epub"
```

After installing, start a new Codex / Claude Code session, then ask:

```text
Use scanned-pdf-to-epub to convert this scanned Chinese PDF into a text EPUB for WeRead.
```

## Paragraph Helpers And Checks

`[x, y, width, height]` 坐标采用左上角为原点。先对每页、每个正文栏分别合并同一行的 OCR 碎片，再按该页正文区域计算字符缩进，并用同一个段落缓冲器处理跨页续接。辅助脚本支持横排散文；缩进层级和行容差需按原书校准，不直接适用于竖排、诗歌或表格。

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

测试覆盖跨页续句、真实新段落、缩进评注、同一行碎片合并及字符坐标保留。详见 [段落重建说明](references/implementation-notes.md#paragraph-reconstruction-across-pages)。

EPUB 的 ZIP/XML 检查与阅读器显示验证是两件事。微信读书网页版仍需实测分栏边界是否缺字；遇到文字在文件中完整、界面却缺失时，应检查导入解析和排版，并以去除专名样式的版本作对照，不能据此直接认定是字体问题或已解决。

## Windows OCR Notes

This skill does not require Apple Vision OCR. On Windows, prefer:

- PaddleOCR for local Chinese OCR
- PyMuPDF or pypdfium2 for PDF rendering
- Tesseract only as a fallback for cleaner/simple scans
- Azure/Baidu/Tencent/Google/ABBYY OCR when cloud OCR is acceptable

See [implementation notes](references/implementation-notes.md) for details.

## License

MIT

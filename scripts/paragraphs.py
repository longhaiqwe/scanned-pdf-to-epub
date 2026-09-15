"""Accumulate horizontal prose across scan pages using region-relative indentation.

Caller supplies page-local text-region left edge and character pitch. Remove
marginal material and combine OCR fragments into logical lines before calling.
Do not reuse this layout rule for verse, tables, or vertical text.
"""
class Paragraphs:
    def __init__(self):
        self.paragraphs = []
        self.pending = ''
        self.block_indent = 0.0
        self.last_page = None
        self.last_text = ''
        self.last_end_gap = None
        self.boundaries = []

    def flush(self):
        if self.pending:
            self.paragraphs.append(self.pending)
            self.pending = ''

    def feed(self, text, markup, *, page, offset_chars, force_break=False, end_gap_chars=None):
        # A four-character first-line indent starts a two-character inset block.
        # A subsequent two-character indent continues that block, including on
        # the next page. An unindented line returns to ordinary prose.
        if (self.block_indent == 2.0 and 1.2 <= offset_chars < 3.2
                and self.last_end_gap is not None and self.last_end_gap > 1.5
                and self.last_text.rstrip().rstrip('”’」』').endswith(('。','！','？'))):
            # A short completed line ended the inset block; the following
            # two-character indent is an ordinary paragraph's first line.
            self.block_indent = 0.0
        if offset_chars < 0.8:
            self.block_indent = 0.0
        elif offset_chars >= 3.2:
            self.block_indent = 2.0
        new_paragraph = force_break or offset_chars - self.block_indent >= 1.2
        if self.last_page is not None and page != self.last_page:
            self.boundaries.append(dict(previous_page=self.last_page, page=page,
                action='new-paragraph' if new_paragraph else 'join',
                previous_tail=self.last_text[-50:], next_head=text[:50],
                offset_chars=round(offset_chars, 2), block_indent=self.block_indent))
        if new_paragraph:
            self.flush()
        self.pending += markup
        self.last_page = page
        self.last_text = text
        self.last_end_gap = end_gap_chars

    def finish(self):
        self.flush()
        return self.paragraphs


def merge_logical_rows(lines, *, center_tolerance):
    """Merge fragments on one page's single horizontal prose column.

    Input: dicts with text, box=[x,y,width,height] (top-left origin), and
    optional chars. Tolerance is in the same coordinate units as box. Keep
    source fragments and character boxes without mutating the input.
    """
    from copy import deepcopy

    if center_tolerance <= 0:
        raise ValueError('center_tolerance must be positive')
    rows = []
    for line in sorted(lines, key=lambda line: line['box'][1] + line['box'][3] / 2):
        center = line['box'][1] + line['box'][3] / 2
        if rows and abs(center - rows[-1][0]) < center_tolerance:
            rows[-1][1].append(line)
        else:
            rows.append((center, [line]))
    result = []
    for _, fragments in rows:
        fragments = sorted(fragments, key=lambda line: line['box'][0])
        left = min(line['box'][0] for line in fragments)
        top = min(line['box'][1] for line in fragments)
        right = max(line['box'][0] + line['box'][2] for line in fragments)
        bottom = max(line['box'][1] + line['box'][3] for line in fragments)
        result.append(dict(
            text=''.join(line['text'] for line in fragments),
            box=[left, top, right-left, bottom-top],
            chars=deepcopy([char for line in fragments for char in line.get('chars', [])]),
            fragments=deepcopy(fragments),
        ))
    return result

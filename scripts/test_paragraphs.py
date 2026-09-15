import unittest
from paragraphs import Paragraphs

class ParagraphTests(unittest.TestCase):
    def test_preface_continues_across_pages(self):
        p=Paragraphs()
        p.feed('藩镇之乱','藩镇之乱',page=9,offset_chars=0)
        p.feed('则令孜之为也。','则令孜之为也。',page=10,offset_chars=0)
        self.assertEqual(p.finish(),['藩镇之乱则令孜之为也。'])
    def test_real_top_of_page_paragraph_is_preserved(self):
        p=Paragraphs()
        p.feed('上一段。','上一段。',page=1,offset_chars=0)
        p.feed('下一段。','下一段。',page=2,offset_chars=2)
        self.assertEqual(p.finish(),['上一段。','下一段。'])
    def test_full_stop_does_not_force_break(self):
        p=Paragraphs()
        p.feed('第一句。','第一句。',page=1,offset_chars=0)
        p.feed('同段第二句。','同段第二句。',page=2,offset_chars=0)
        self.assertEqual(p.finish(),['第一句。同段第二句。'])
    def test_inset_commentary_continues(self):
        p=Paragraphs()
        for text,page,offset in [('臣光曰：',1,4),('其为害',1,2),('岂不多哉！',2,2),('夫德者',2,4)]:
            p.feed(text,text,page=page,offset_chars=offset)
        self.assertEqual(p.finish(),['臣光曰：其为害岂不多哉！','夫德者'])
    def test_short_line_ends_inset_block(self):
        p=Paragraphs()
        p.feed('评论。','评论。',page=1,offset_chars=4,end_gap_chars=8)
        p.feed('初，纪事。','初，纪事。',page=1,offset_chars=2,end_gap_chars=0)
        self.assertEqual(p.finish(),['评论。','初，纪事。'])
    def test_markup_survives_join(self):
        p=Paragraphs()
        p.feed('名字','<strong>名字</strong>',page=1,offset_chars=0)
        p.feed('续文','续文',page=2,offset_chars=0)
        self.assertEqual(p.finish(),['<strong>名字</strong>续文'])
    def test_explicit_signature_break(self):
        p=Paragraphs()
        p.feed('正文。','正文。',page=1,offset_chars=0)
        p.feed('署名','署名',page=2,offset_chars=0,force_break=True)
        self.assertEqual(p.finish(),['正文。','署名'])

if __name__=='__main__':unittest.main()

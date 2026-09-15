import unittest
from copy import deepcopy
from paragraphs import Paragraphs, merge_logical_rows

class LogicalRowsTests(unittest.TestCase):
    def test_right_fragment_does_not_become_a_paragraph(self):
        # A real body-row regression: OCR reported the right fragment separately.
        lines = [
            dict(text='燕王哙以国让其相',box=[.5995,.5522,.2482,.0191]),
            dict(text='蜀既属秦，秦以益强富厚，轻诸侯。',box=[.0539,.5508,.5129,.0234]),
            dict(text='子之。',box=[.0515,.5858,.0703,.0203]),
            dict(text='六年，王崩，子赧王延立。',box=[.1148,.6206,.3607,.0233]),
        ]
        p=Paragraphs()
        for row in merge_logical_rows(lines,center_tolerance=.010):
            p.feed(row['text'],row['text'],page=40,
                   offset_chars=(row['box'][0]-.054)/(.795/26))
        self.assertEqual(p.finish(),[
            '蜀既属秦，秦以益强富厚，轻诸侯。燕王哙以国让其相子之。',
            '六年，王崩，子赧王延立。'])

    def test_character_boxes_and_text_order_survive(self):
        a=dict(t='甲',b=[.1,.2,.02,.03]);b=dict(t='乙',b=[.4,.2,.02,.03])
        lines=[dict(text='乙',box=[.4,.2,.02,.03],chars=[b]),
               dict(text='甲',box=[.1,.2,.02,.03],chars=[a])]
        original=deepcopy(lines)
        row=merge_logical_rows(lines,center_tolerance=.01)[0]
        self.assertEqual(row['text'],'甲乙')
        self.assertEqual(row['chars'],[a,b])
        self.assertEqual(lines,original)
        row['chars'][0]['t']='改'
        self.assertEqual(lines,original)

    def test_adjacent_rows_remain_separate(self):
        lines=[dict(text='第一行',box=[.1,.2,.5,.025]),
               dict(text='第二行',box=[.1,.235,.5,.025])]
        self.assertEqual(len(merge_logical_rows(lines,center_tolerance=.01)),2)

    def test_empty_page(self):
        self.assertEqual(merge_logical_rows([],center_tolerance=.01),[])

if __name__=='__main__':unittest.main()

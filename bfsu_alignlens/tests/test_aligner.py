from core.aligner import manual_align_by_index
from core.datatypes import Segment


def test_manual_align():
    a=[Segment('a1','f','en','Hello')]
    b=[Segment('b1','g','zh_sim','你好')]
    rows = manual_align_by_index({'en':a,'zh_sim':b}, 'set_001', 'en')
    assert rows[0].segments['en'] == 'Hello'
    assert rows[0].segments['zh_sim'] == '你好'

from core.segmenter import split_text


def test_zh_punctuation():
    segs = split_text('这是第一句。这是第二句！好吗？', 'zh_sim', 'f1')
    assert len(segs) == 3


def test_en_abbreviation():
    segs = split_text('Dr. Smith arrived. He smiled.', 'en', 'f2')
    assert len(segs) == 2

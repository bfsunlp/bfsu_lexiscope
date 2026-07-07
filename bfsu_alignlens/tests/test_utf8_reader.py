from core.document_reader import read_document


def test_utf8_without_bom_reader(tmp_path):
    p = tmp_path / 'a.txt'
    p.write_text('你好\nhello', encoding='utf-8')
    assert read_document(str(p)) == '你好\nhello'

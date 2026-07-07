from pathlib import Path
from core.datatypes import AlignmentUnit
from core.exporters import export_line_txt


def test_export_txt(tmp_path):
    p = tmp_path/'out.txt'
    export_line_txt([AlignmentUnit(1,'set_001',{'en':'Hello','zh_sim':'你好'}, similarity=.9, status='confirmed')], str(p))
    assert p.exists()
    assert 'Hello' in p.read_text(encoding='utf-8')

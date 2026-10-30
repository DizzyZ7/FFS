from pathlib import Path

def test_social_export_controls_match_js_handler():
    html=(Path(__file__).resolve().parents[1]/'web'/'index.html').read_text(encoding='utf8')
    for element_id in ('social-export','social-aspect','social-framing','download'):
        assert f'id="{element_id}"' in html
    assert "el('social-framing').value" in html

def test_ranked_montage_controls_match_handler():
    html=(Path(__file__).resolve().parents[1]/'web'/'index.html').read_text(encoding='utf8')
    for element_id in ('ranked-montage','ranked-render','highlight-results','auto-duration','auto-pace','asr-model'):
        assert f'id="{element_id}"' in html

def test_recreation_controls_have_matching_handlers():
    html=(Path(__file__).resolve().parents[1]/'web'/'index.html').read_text(encoding='utf8')
    for element_id in ('recreation-create','recreation-refresh','recreation-render',
                       'recreation-status','recreation-shots','recreation-download',
                       'recreation-instructions'):
        assert f'id="{element_id}"' in html
        assert f"el('{element_id}')" in html
    assert '/recreation/shots/' in html
    assert '/recreation/render' in html

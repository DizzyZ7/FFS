import pytest
from app.edit_instructions import parse_edit_request

def test_russian_dynamic_vertical():
    result=parse_edit_request('Сделай динамичный вертикальный ролик на 25 секунд для Reels')
    assert result['target_seconds']==25
    assert result['pace']=='dynamic'
    assert result['format']=='reels'
    assert result['understood']['duration']

def test_landscape_calm():
    result=parse_edit_request('Плавный горизонтальный ролик на 40 сек')
    assert result['pace']=='calm'
    assert result['format']=='landscape'
    assert result['target_seconds']==40

@pytest.mark.parametrize('instruction',['',' '*5,'Сделай ролик на 200 секунд'])
def test_rejects_bad_instruction(instruction):
    with pytest.raises(ValueError):
        parse_edit_request(instruction)

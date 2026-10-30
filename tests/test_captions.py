import pytest
from app.captions import Word, group_words, to_ass

def test_grouping_and_timing():
    words=[Word(0,0.2,'Hello'),Word(0.2,0.5,'world'),Word(1.5,1.9,'again')]
    assert [len(g) for g in group_words(words)]==[2,1]
    ass=to_ass(words)
    assert 'Dialogue: 0,0:00:00.00,0:00:00.50' in ass
    assert 'Hello world' in ass
    assert ass.count('Dialogue:')==2

def test_reject_invalid_timing():
    with pytest.raises(ValueError):
        group_words([Word(1,1,'bad')])
    with pytest.raises(ValueError):
        group_words([Word(0,1,'a'),Word(0.5,2,'b')])

def test_styles():
    for style in ('pop','minimal','bold'):
        assert 'Style: Caption' in to_ass([Word(0,1,'Hello')],style)
    with pytest.raises(ValueError):
        to_ass([],style='unknown')

def test_ass_animation_and_multiline():
    ass=to_ass([Word(0,0.3,'hello'),Word(1,1.4,'world')])
    assert ass.count('Dialogue:')==2
    assert 't(0,170' in ass
    assert ass.splitlines()[-1].startswith('Dialogue:')

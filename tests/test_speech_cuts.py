import pytest
from app.speech_cuts import plan_speech_cuts

def test_removes_long_pause():
    words=[{'start':1,'end':1.4},{'start':1.5,'end':1.8},
           {'start':4,'end':4.3}]
    clips=plan_speech_cuts(words,6,padding=0.1,min_pause=0.65)
    assert len(clips)==2
    assert clips[0]=={'start':0.9,'end':1.9}
    assert clips[1]=={'start':3.9,'end':4.4}

def test_short_gaps_are_kept():
    words=[{'start':0,'end':0.4},{'start':0.5,'end':0.9}]
    assert len(plan_speech_cuts(words,2))==1

def test_empty_speech_is_safe():
    assert plan_speech_cuts([],4)==[]

@pytest.mark.parametrize('words',[
    [{'start':2,'end':1}],
    [{'start':-1,'end':1}],
    [{'start':4,'end':5}],
    [{'start':2,'end':3},{'start':1,'end':2}]
])
def test_invalid_words(words):
    with pytest.raises(ValueError):
        plan_speech_cuts(words,4)

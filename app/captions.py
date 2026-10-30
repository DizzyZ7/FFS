"""Word-aligned caption planning and safe ASS subtitle rendering.

Input transcript is explicit; speech recognition will be integrated separately.
"""
import math
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str

def group_words(words:list[Word],max_words:int=4,max_gap:float=0.45):
    if not 1<=max_words<=12:
        raise ValueError('max_words must be 1..12')
    groups=[]
    current=[]
    last_end=0.0
    for word in words:
        if not math.isfinite(word.start) or not math.isfinite(word.end):
            raise ValueError('Timestamps must be finite')
        if word.start<0 or word.end<=word.start or (current and word.start<last_end):
            raise ValueError('Words must be ordered and non-overlapping')
        if not word.text.strip():
            raise ValueError('Empty word')
        if current and (len(current)>=max_words or word.start-last_end>max_gap):
            groups.append(current)
            current=[]
        current.append(word)
        last_end=word.end
    if current:
        groups.append(current)
    return groups

def _time(seconds:float):
    centis=round(seconds*100)
    hours,rest=divmod(centis,360000)
    minutes,rest=divmod(rest,6000)
    secs,cs=divmod(rest,100)
    return f'{hours}:{minutes:02d}:{secs:02d}.{cs:02d}'

def _ass_escape(text:str):
    return text.replace('\\','\\\\').replace('{','\\{').replace('}','\\}').replace('\\N',' ')

def to_ass(words:list[Word],style:str='pop',max_words:int=4):
    presets={
        'pop':('Arial',58,'&H00FFFFFF','&H009B65FF'),
        'minimal':('Arial',44,'&H00FFFFFF','&H00101010'),
        'bold':('Arial',66,'&H0000FFFF','&H00000000'),
    }
    if style not in presets:
        raise ValueError('Unknown caption style')
    font,size,primary,outline=presets[style]
    header=f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font},{size},{primary},&H000000FF,{outline},&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,70,70,300,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events=[]
    for group in group_words(words,max_words=max_words):
        text=' '.join(_ass_escape(w.text) for w in group)
        # ASS transform creates an animated entrance with easing-like scale.
        animated=r'{\\fscx85\\fscy85\\t(0,170,\\fscx100\\fscy100)}'+text
        events.append(f'Dialogue: 0,{_time(group[0].start)},{_time(group[-1].end)},Caption,,0,0,0,,{animated}')
    return header+'\\n'.join(events)+'\\n'

def save_ass(path:Path,words:list[Word],style:str='pop',max_words:int=4):
    path.write_text(to_ass(words,style,max_words),encoding='utf-8')
    return path

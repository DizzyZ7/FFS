"""Constrained natural-language presets for offline short-form editing.

No shell commands, arbitrary code execution or external AI calls.
"""
import re

def parse_edit_request(instruction: str):
    if not isinstance(instruction,str) or not instruction.strip() or len(instruction)>1000:
        raise ValueError('Provide an edit instruction up to 1000 characters')
    text=instruction.lower()
    duration=None
    match=re.search(r'(\d{1,3})\s*(?:секунд|сек|seconds|second|s)\b',text)
    if match:
        duration=int(match.group(1))
        if not 3<=duration<=180:
            raise ValueError('Requested duration must be 3-180 seconds')
    pace='balanced'
    if any(x in text for x in ('динамич','быстр','энергич','dynamic','fast','snappy')):
        pace='dynamic'
    elif any(x in text for x in ('плавн','спокойн','медлен','calm','slow')):
        pace='calm'
    format='reels'
    if any(x in text for x in ('горизонталь','landscape','16:9','youtube video')):
        format='landscape'
    elif any(x in text for x in ('квадрат','square','1:1')):
        format='square'
    elif any(x in text for x in ('shorts','tiktok','reels','вертикаль','9:16')):
        format='reels'
    return {'target_seconds':duration or 30,'pace':pace,'format':format,
            'understood':{'duration':duration is not None,'pace':pace!='balanced',
                          'format':any(x in text for x in ('shorts','tiktok','reels','вертикаль','9:16','горизонталь','landscape','16:9','квадрат','square','1:1'))},
            'unhandled_instruction':instruction.strip()}

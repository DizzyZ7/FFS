import unittest
from pathlib import Path
from unittest.mock import patch
from app.media import render

class RenderValidationTests(unittest.TestCase):
    def test_empty_timeline(self):
        with self.assertRaisesRegex(ValueError,'empty'):
            render(Path('source.mp4'),[],Path('output.mp4'))

    @patch('app.media.probe',return_value={'duration':10})
    def test_invalid_clip_bounds(self,_):
        with self.assertRaisesRegex(ValueError,'Invalid clip'):
            render(Path('source.mp4'),[{'start':8,'end':11}],Path('output.mp4'))

if __name__=='__main__':
    unittest.main()

import unittest
import sys
from pathlib import Path
from collections import Iterable
sys.path.append('../')
from animation_anchor.htkaligner import PhonemeForcedAligner, PhonemeDuration

class TestPhonemeForcedAligner(unittest.TestCase):
    def setUp(self):
        print('setting up')

    def tearDown(self) -> None:
        print('tearing down')

    def test_align(self):
        aligner = PhonemeForcedAligner()
        phoneme_durations = aligner.align('春走在路上，看看世界无限宽广，繁花似锦，人来人往， 那无人能解的忧伤', Path(__file__).parent / '11.mp3')
        self.assertIsInstance(phoneme_durations[0], PhonemeDuration)
        self.assertIsInstance(phoneme_durations, Iterable)
        print('the forced phonemes is: \n', phoneme_durations)


if __name__ == '__main__':
    unittest.main()
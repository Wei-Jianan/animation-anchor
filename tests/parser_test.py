import unittest
import sys
from pathlib import Path
from collections import Iterable
sys.path.append('../')
from animation_anchor.parser import parser_factory
from animation_anchor.htkaligner import PhonemeForcedAligner

class TestAnimationParser(unittest.TestCase):
    def setUp(self):
        print('setting up')
        self._AnimationParser = parser_factory('AnimationParser')

    def tearDown(self) -> None:
        print('tearing down')

    def test_init(self):
        parser = self._AnimationParser()

    def test_phoneme_durations2viseme_durations(self):
        parser = self._AnimationParser()
        aligner = PhonemeForcedAligner()
        phoneme_durations = aligner.align('春走在路上，看看世界无限宽广，繁花似锦，人来人往， 那无人能解的忧伤', Path(__file__).parent / '11.mp3')
        viseme_durations = parser.phoneme_durations2viseme_durations(phoneme_durations)
        for phoneme_duration, viseme_duration in zip(phoneme_durations, viseme_durations):
            self.assertEqual(phoneme_duration.begin, viseme_duration.begin)
            self.assertEqual(phoneme_duration.end, viseme_duration.end)


if __name__ == '__main__':
    unittest.main()


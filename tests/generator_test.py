import unittest
import cv2
import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt
from animation_anchor.parser import parser_factory
from animation_anchor.htkaligner import PhonemeForcedAligner
from animation_anchor.generator import VisemeFrameSeq, VisemeFrameSeqGenerator, Viseme

class TestVisemeFrameSeqGenerator(unittest.TestCase):
    def test_generate(self):
        aligner = PhonemeForcedAligner()
        parser = parser_factory('AnimationParser')()
        generator = VisemeFrameSeqGenerator(frame_rate=25, fixed_landmarks=[[0, 0],[60, 36]], viseme_kind='aide')
        phoneme_durations = aligner.align('春走在路上，看看世界无限宽广，繁花似锦，人来人往， 那无人能解的忧伤', Path(__file__).parent / '11.mp3')
        viseme_durations = parser.phoneme_durations2viseme_durations(phoneme_durations)

        viseme_frame_seq = generator.generate(viseme_durations)
        for viseme_frame in viseme_frame_seq:
            print(viseme_frame[0])
            print(viseme_frame[1])
            break



class TestVisemeFrameSeq(unittest.TestCase):
    def test_allocate_num_frame(self):
        generator = VisemeFrameSeq(frame_rate=25)
        self.assertSequenceEqual(list(generator.allocate_num_frame([1, 2, 3])), [25, 25, 25])
        self.assertEqual(sum(generator.allocate_num_frame([1, 2, 3, 3.1, 3.2, 3.3, 3.4, 3.5])),
                         generator.get_total_num_frames([1, 2, 3, 3.1, 3.2, 3.3, 3.5]))
        # print(generator.allocate_num_frame([1, 2, 3, 3.1, 3.2, 3.3, 3.4, 3.5]))

    def test_sample_frames(self):
        generator = VisemeFrameSeq(frame_rate=25)
        visemes_end = [0.1, 0.2, 0.3, 0.4]
        visemes_num_frames = generator.allocate_num_frame(visemes_end)
        print('viseme num frames', visemes_num_frames)
        frames = generator.sample_frames(visemes_num_frames, [list(range(10)), list(range(10)), list(range(10)), list(range(10))])
        print(frames)

    def test_getitem(self):
        try:
            visemes = [Viseme('aide/C1', begin=0.0, end=1.0),
                       Viseme('aide/C2', begin=1.0, end=2.0),
                       Viseme('aide/C3', begin=2.0, end=3.0),
                       Viseme('aide/C4', begin=3.0, end=4.0),
                       Viseme('aide/C5', begin=4.0, end=5.0)]
            viseme_frame_seq = VisemeFrameSeq(viseme_seq=visemes)
            print('length of viseme frame seq is {}'.format(len(viseme_frame_seq)))
        except:
            import sys
            print('the serialization is still not done.', file=sys.stderr)
            raise

class TestViseme(unittest.TestCase):
    def test_getitem(self):
        viseme = Viseme('aide/C1', begin=0.1, end=3.0)
        self.assertEqual(len(viseme), 8)
        fig = plt.figure()
        plt.imshow(viseme[0][0])
        plt.show()

if __name__ == '__main__':
    unittest.main()

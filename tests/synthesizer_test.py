import unittest
import sys
sys.path.append('../')
import cv2
from pathlib import Path
from matplotlib import pyplot as plt
from animation_anchor.synthesizer import TemplateFrameSeq, template_root
from animation_anchor.generator import Viseme, viseme_root, VisemeFrameSeq
from animation_anchor.utils.log import draw


class TestTemplateFrameSeq(unittest.TestCase):
    def setUp(self):
        print('setting up')
        self.template_frame_seq = TemplateFrameSeq(template_root.joinpath('aide'),
                                                   fixed_landmarks=[[210, 234], [270, 270]])
        viseme1 = Viseme('C1', begin=0.0, end=1.0, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        viseme2 = Viseme('C1', begin=1.0, end=3.0, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        viseme3 = Viseme('C1', begin=3.0, end=4.0, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        viseme4 = Viseme('C1', begin=4.0, end=5.0, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        viseme5 = Viseme('C1', begin=5.0, end=6.0, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        viseme6 = Viseme('C1', begin=6.1, end=7.2, fixed_landmarks=[[0, 0],
                                                                    [60, 36]])
        self.viseme_frame_seq = VisemeFrameSeq([viseme1, viseme2, viseme3, viseme4, viseme5, viseme6])

    def test_getitem(self):
        template_frame_seq = TemplateFrameSeq(template_root.joinpath('aide'),

                                              fixed_landmarks=[[210, 234], [270, 270]])
        template_frame_seq.frames_landmarks = list(range(4))
        ids = [template_frame_seq[i] for i in range(10)]
        self.assertSequenceEqual(ids, [0, 1, 2, 3, 3, 2, 1, 0, 0, 1])

    def test_synthesize(self):
        img = self.template_frame_seq.synthesize(self.viseme_frame_seq[0], self.template_frame_seq[0])

        # fig = plt.figure()
        # plt.imshow(img )
        #
        # plt.show()

    def test_synthesize_seq(self):
        import time
        start = time.time()
        imgs = self.template_frame_seq.synthesize_seq(self.viseme_frame_seq)
        print('{} frames took {} seconds.'.format(len(imgs), time.time() - start))
        fig = plt.figure()
        plt.imshow(imgs[-1] )
        plt.show()



    def test_get_face_mask(self):
        template_frame_seq = TemplateFrameSeq(template_root.joinpath('aide'),
                                              fixed_landmarks=[[210, 234], [270, 270]])
        viseme_frame = self.viseme_frame_seq[0][0]
        img = self.template_frame_seq.get_face_mask(viseme_frame) * 255
        # fig = plt.figure()
        # plt.imshow(img)
        # plt.show()

    def test_draw(self):
        template_frame_seq = TemplateFrameSeq(template_root.joinpath('aide'),
                                              fixed_landmarks=[[210, 234], [270, 270]])
        img = draw(self.template_frame_seq[0][0], self.template_frame_seq[0][1])
        # fig = plt.figure()
        # plt.imshow(img)
        # plt.show()


if __name__ == '__main__':
    unittest.main()

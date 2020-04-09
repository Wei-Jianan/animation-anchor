import os
import numpy as np
import cv2
import bisect

from typing import Sequence, Optional, List

# from collections import Iterable
from pathlib import Path
from ..parser import VisemeDuration
from ..utils import read_frames, read_landmarks


class Viseme:
    viseme_root = Path(__file__).parent.joinpath('../assets/viseme').resolve()

    def __init__(self, viseme_name, begin, end, fixed_landmarks: Optional[list] = None):
        self.begin = begin
        self.end = end
        viseme_dir = self.viseme_root / viseme_name
        if not viseme_dir.exists():
            raise FileNotFoundError("{} the viseme name must have matched viseme assets dictionary.".format(viseme_dir))
        self.frames = read_frames(viseme_dir)
        if fixed_landmarks is None:
            self.landmarks = read_landmarks(viseme_dir)
        else:
            self.landmarks = np.array([fixed_landmarks for i in range(len(self.frames))])
            if self.landmarks.shape != (len(self.frames), 2, 2):
                raise ValueError(
                    'the fixed_landmarks {} is supposed to be transformed to ndarray with shape (length of frames, 2, 2)'.format(
                        fixed_landmarks))
        if type(begin) != float or type(end) != float:
            raise TypeError('duration must be float type.')
        if len(self.frames) != len(self.landmarks):
            raise ValueError(
                'the length of frames which is {} must be equal to the length of landmarks which is {}'.format(
                    len(self.frames),
                    len(self.landmarks)))

    def __getitem__(self, idx):
        return self.frames[idx], self.landmarks[idx]

    def __len__(self):
        return len(self.frames)


class VisemeFrameSeq:
    def __init__(self, viseme_seq: Sequence[Viseme] = [], frame_rate=25):
        self.visemes = viseme_seq
        self.frame_rate = frame_rate
        self.initialize()

    def check_type(self, os, type_):
        if not isinstance(os, Sequence):
            if isinstance(os, type_):
                raise TypeError
        else:
            for o in os:
                if type(o) != type_:
                    raise TypeError

    def initialize(self):
        # initialize here.
        try:
            self.check_type(self.visemes, Viseme)
        except TypeError:
            raise TypeError("the viseme sequence must be type of iterable Viseme.")
        if not self.visemes:
            return
        visemes_end = []
        for viseme in self.visemes[1:]:
            visemes_end.append(viseme.begin)
        visemes_end.append(self.visemes[-1].end)
        visemes_num_frames = self.allocate_num_frame(visemes_end)
        self.frames_landmarks = self.sample_frames(visemes_num_frames, self.visemes)
        assert abs(
            len(self.frames_landmarks) - self.get_total_num_frames(
                visemes_end)) <= 1, 'the len of frames must approximate to total num frames.'

    def get_total_num_frames(self, visemes_end):
        total_duration = visemes_end[-1] if len(visemes_end) > 0 else 0
        total_num_frames = int(total_duration * self.frame_rate)
        return total_num_frames

    def allocate_num_frame(self, visemes_end):
        if not (visemes_end):
            return []
        visemes_end = np.array(visemes_end)
        total_num_frames = self.get_total_num_frames(visemes_end)

        frames_time_stamp = [i * 1 / self.frame_rate for i in range(total_num_frames)]
        visemes_num_frames = [0]
        for viseme_end in visemes_end:
            visemes_num_frames.append(bisect.bisect_left(frames_time_stamp, viseme_end))
        visemes_num_frames = np.diff(np.array(visemes_num_frames))
        return visemes_num_frames

    def sample_frames(self, visemes_num_frames, visemes):
        frames = []
        if len(visemes_num_frames) == 0 and len(visemes) == 0:
            return frames
        assert len(visemes_num_frames) == len(
            visemes), 'num of visemes_num_frames {} is not equal to num of visemes {}'.format(len(visemes_num_frames),
                                                                                              len(visemes))
        for viseme_num_frames, viseme in zip(visemes_num_frames, visemes):
            samples_id = np.linspace(start=0, stop=len(viseme), num=viseme_num_frames, endpoint=False).astype(np.int32)
            # frames.append(viseme[samples_id])
            for id in samples_id:
                frames.append(viseme[id])
        # frames = np.concatenate(frames, axis=0)
        return frames

    def append(self, viseme):
        # initialize when append new viseme
        self.check_type(viseme, Viseme)
        self.visemes.append(viseme)
        self.initialize()

    def __len__(self):
        return len(self.frames_landmarks)

    def __getitem__(self, idx):
        return self.frames_landmarks[idx]

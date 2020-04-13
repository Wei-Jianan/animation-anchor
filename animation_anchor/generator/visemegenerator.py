from typing import Iterable, Optional, List
from ..parser import VisemeDuration
from .viseme import Viseme, VisemeFrameSeq
from . import viseme_root


class VisemeFrameSeqGenerator:
    def __init__(self, frame_rate, viseme_kind: str, fixed_landmarks: Optional[List[List]] = None):
        self.frame_rate = frame_rate
        self.fixed_landmarks = fixed_landmarks
        self.viseme_kind=viseme_kind
        if not viseme_root.joinpath(self.viseme_kind).exists():
            raise FileNotFoundError('this kind of viseme "{}" is not exists, there shoud be a viseme kind directory in path assets/viseme'.format(self.viseme_kind))


    def check_type(self, viseme_durations):
        for viseme_duration in viseme_durations:
            # print(type(viseme_name_duration[0]), isinstance(viseme_name_duration[1], float))
            if not isinstance(viseme_duration, VisemeDuration):
                raise TypeError('invalid input for viseme_name_duration.')

    def generate(self, viseme_durations: Iterable[VisemeDuration]) -> VisemeFrameSeq:
        # self.check_type(viseme_durations)
        visemes = [Viseme(self.viseme_kind + '/' + viseme_name, begin=begin, end=end, fixed_landmarks=self.fixed_landmarks) for
                   (viseme_name, begin, end) in viseme_durations]
        viseme_frame_seq = VisemeFrameSeq(visemes, frame_rate=self.frame_rate)
        return viseme_frame_seq

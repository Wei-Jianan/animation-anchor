# -*- coding: utf-8 -*-
from typing import Optional, List
from .templateseq import TemplateFrameSeq
from ..generator import VisemeFrameSeq

from typing import Iterable
import numpy as np


class VideoSynthesizer:
    def __init__(self, template_name='zqy2.mp4', fixed_landmarks: Optional[List[List]] = None):
        self.template_frame_seq = TemplateFrameSeq(template_name, fixed_landmarks=fixed_landmarks)

    def synthesize(self, viseme_frame_seq: VisemeFrameSeq) -> Iterable[np.ndarray]:
        img_seq = self.template_frame_seq.synthesize_seq(viseme_frame_seq)
        return img_seq
import argparse
import subprocess
from cv2 import cv2
import os, sys
from tempfile import NamedTemporaryFile
from typing import Optional, List
import ffmpeg

from .htkaligner import PhonemeForcedAligner
from .parser import parser_factory
from .generator import VisemeFrameSeqGenerator
from .synthesizer import VideoSynthesizer

tmp_dir = os.path.join(os.path.dirname(__file__), 'tmp/')


class Anchor:
    def __init__(self, frame_rate, viseme_fixed_landmarks: Optional[List[List]] = None,
                 template_fixed_landmarks: Optional[List[List]] = None):
        self.frame_rate = frame_rate
        self.pheneme_forced_aligner = PhonemeForcedAligner()
        self.parser = parser_factory('AnimationParser')()
        self.viseme_frame_generator = VisemeFrameSeqGenerator(frame_rate=self.frame_rate,
                                                              fixed_landmarks=viseme_fixed_landmarks)
        self.template_fixed_landmarks = template_fixed_landmarks
        self.synthesizer_pool = {}

    def _tts(self, text):
        wav_file = NamedTemporaryFile(suffix='.wav')
        subprocess.check_call(['espeak', '-vzh', text, '-w', wav_file.name])
        return wav_file

    def _get_video(self, img_seq, wav_path, frame_rate):
        video_file = NamedTemporaryFile(suffix='.mp4')
        video_with_voice_file = NamedTemporaryFile(suffix='.mp4')
        # skvideo.io.vwrite(video_file.name, list(img_seq))
        subprocess.check_call(
            ['ffmpeg', '-y', '-i', wav_path, '-i', video_file.name, '-c:v', 'copy', '-c:a', 'aac', '-strict',
             'experimental',
             video_with_voice_file.name])
        return video_with_voice_file, video_file


    def write_video(self, img_seq, wav_file, debug=False):
        video_file = NamedTemporaryFile(suffix='.mp4')
        video_with_voice_file = NamedTemporaryFile(suffix='.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        img_iter = iter(img_seq)
        img = next(img_iter)
        out = cv2.VideoWriter(video_file.name, fourcc, self.frame_rate, (img.shape[1], img.shape[0]))
        for img in img_iter:
        # while True:
            # img = next(img_iter)
            out.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        out.release()
        v = ffmpeg.input(video_file.name).video
        a = ffmpeg.input(wav_file.name).audio
        jointed = ffmpeg.concat(v, a, v=1, a=1)
        ffmpeg.output(jointed, video_with_voice_file.name).run(overwrite_output=True, quiet=True)

        return video_with_voice_file

    def _write_txt(self, text, random_name):
        text_path = os.path.join(tmp_dir, random_name + '.txt')
        f = open(text_path, "a+")
        empty_list = []
        for character in text:
            if character >= u'\u4e00' and character <= u'\u9fa5':
                f.writelines(character + "\n")
        f.close()
        return text_path

    def inference(self, text, wav_path=None, template_name='aide'):
        self.synthesizer_pool.setdefault(template_name, VideoSynthesizer(template_name, self.template_fixed_landmarks))
        if wav_path is None:
            wav_file = self._tts(text)
            wav_path = wav_file.name
        phoneme_durations = self.pheneme_forced_aligner.align(text, wav_path)
        viseme_durations = list(self.parser.phoneme_durations2viseme_durations(phoneme_durations))
        viseme_frame_seq = self.viseme_frame_generator.generate(viseme_durations)
        video_synthesizer = self.synthesizer_pool[template_name]
        img_seq = video_synthesizer.synthesize(viseme_frame_seq)
        # video_with_voice_file, video_file = self._get_video(img_seq, wav_path, self.frame_rate)
        video_with_voice_file = self.write_video(img_seq, wav_file)
        return video_with_voice_file

import math
from scipy.io import wavfile
import numpy as np
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

from queue import Queue
from enum import Enum, unique
from collections import namedtuple
from typing import Sequence, Tuple, Iterable, Optional, List
import tempfile
from tempfile import NamedTemporaryFile
import time, cv2, ffmpeg, os
import subprocess
import datetime

from .anchor import Anchor
from .synthesizer import TemplateFrameSeq, VideoSynthesizer
from .utils import LOG

from .htkaligner import PhonemeForcedAligner
from .parser import parser_factory
from .generator import VisemeFrameSeqGenerator
from .synthesizer import VideoSynthesizer
from .utils import LOG


@unique
class AnchorState(Enum):
    ready = 'not running'
    stop = 'stopped'
    listening = 'waiting'
    speaking = 'speaking'


AnchorTask = namedtuple('AnchorTask', ['viseme_frame_seq', 'wav_frame_seq', 'anchor_state', 'text_id', 'template_name'])


class AnchorStateException(Exception):
    pass


class StreamAnchor(Anchor):
    def __init__(self, default_template_name='aide', num_worker=1,
                 waiting_frame_num=30, sampling_rate=16000, async_mode=False, debug=False, **kwargs):
        super(StreamAnchor, self).__init__(**kwargs)
        self.task_queue = Queue()
        self.generating_thread = FrameGenerator(self)
        # self.pool = mp.Pool(num_worker)
        self.pool = ProcessPoolExecutor(num_worker)
        self.waiting_frame_num = waiting_frame_num
        self.sampling_rate = sampling_rate
        self.template_name = default_template_name
        self.task_mutex = threading.RLock()
        self.task_state = AnchorState.ready
        self.state_mutex = threading.RLock()
        self.current_state = AnchorState.ready
        self.stream = Queue()
        self.frame_no = 0
        self.gotten_no = 0
        self.async_mode = async_mode
        self.debug = debug

    def __repr__(self):
        # TODO
        return self.__class__.__name__ + '<' + str(id(self)) + '>'

    def __iter__(self):
        # with self.task_mutex:
        # TODO
        # time.sleep(0.2)
        if not self.stream.qsize() and self.task_state != AnchorState.speaking and self.task_state != AnchorState.listening:
            raise AnchorStateException(' Stream Anchor should be start first before iter')
        return self

    def __next__(self):
        with self.task_mutex:
            if self.task_queue.qsize() == 0 \
                    and self.stream.qsize() < self.waiting_frame_num \
                    and self.task_state != AnchorState.stop:
                self._generate_listening(self.waiting_frame_num)
        frame = self.stream.get()
        if not frame:
            with self.state_mutex:
                self.current_state = AnchorState.stop
            raise StopIteration
        self._pace_control(self.frame_rate)
        video_frame_async, audio_frame, text_id = frame

        if self.async_mode:
            video_frame = video_frame_async.result()
        else:
            video_frame = video_frame_async

        video_frame = video_frame.copy()
        if self.debug:
            font = cv2.FONT_HERSHEY_SIMPLEX
            datestr = str(datetime.datetime.now())
            cv2.putText(video_frame, datestr, (10, 100), font, 0.5, (0, 255, 255), 2, cv2.LINE_AA)
            # video_frame = np.array(video_frame)
        LOG.info(
            'iterate a frame pair: text_id: {}.'.format(text_id))

        return video_frame, audio_frame, text_id

    def start_stream(self):
        LOG.info('{} starting stream.'.format(self))
        self._initialize()

    def stop_stream(self):
        with self.task_mutex:
            self.task_state = AnchorState.stop
        self.task_queue.put(None)
        # self.task_queue.join()
        # self.task_queue

    def put_text_wav(self, text, wav_path, text_id, template_name='aide'):
        LOG.info('{} get wav and text: {}, and start preprocessing'.format(self, text))
        with self.task_mutex:
            if self.task_state == AnchorState.ready:
                raise AnchorStateException(' Stream Anchor should be start first before iter')
        phoneme_durations = self.phoneme_forced_aligner.align(text, wav_path)
        viseme_durations = list(self.parser.phoneme_durations2viseme_durations(phoneme_durations))
        viseme_frame_seq = self.viseme_frame_generator.generate(viseme_durations)
        wav_frame_seq = self._split_wav(wav_path)
        LOG.info('{} text: {} preprocessing done'.format(self, text))
        self._generate_speaking(viseme_frame_seq, wav_frame_seq, text_id=text_id, template_name=template_name)

    def _split_wav(self, wav_path) -> Iterable[np.ndarray]:
        def _generate(wav_data, sample_per_frame):
            for i in range(math.ceil(len(wav_data) / sample_per_frame)):
                if (i + 1) * sample_per_frame > len(wav_data):
                    wave_frame = self._blank_wave_frame(sample_per_frame)
                    wave_frame[: len(wav_data) - i * sample_per_frame] = wav_data[i * sample_per_frame:]
                else:
                    wave_frame = wav_data[i * sample_per_frame: (i + 1) * sample_per_frame]
                yield wave_frame

        resampled_wav_file = tempfile.NamedTemporaryFile(suffix='.wav')
        subprocess.check_call(['sox', wav_path, '-r', str(self.sampling_rate), resampled_wav_file.name])
        sampling_rate, wav_data = wavfile.read(resampled_wav_file.name)
        sample_per_frame = sampling_rate // self.frame_rate
        return _generate(wav_data, sample_per_frame)

    def _combine_wav(self, wave_frames: Iterable[np.ndarray]) -> tempfile.NamedTemporaryFile:
        wave_file = tempfile.NamedTemporaryFile(suffix='.wav')
        LOG.info('{} combine the audio_frames to {}'.format(self, wave_file.name))
        wave_data = np.concatenate(list(wave_frames), axis=0)
        wavfile.write(wave_file.name, rate=self.sampling_rate, data=wave_data)
        return wave_file

    def _blank_wave_frame(self, sample_per_frame):
        wave_frame = np.zeros(shape=(sample_per_frame,), dtype=np.int16)
        return wave_frame

    def _pace_control(self, frame_rate):
        while (time.time() - self.start_time) < self.gotten_no / self.frame_rate:
            time.sleep(max(0, (1 / frame_rate) - 0.015))
        self.gotten_no += 1

    def get_state(self):
        with self.state_mutex:
            return self.current_state

    def _initialize(self):
        self._generate_listening(self.waiting_frame_num)
        with self.state_mutex:
            self.template_frame_seq = self._get_template_frame_seq(self.template_name)
        self.generating_thread.start()
        self.start_time = time.time()

    def _get_template_frame_seq(self, template_name):
        self.synthesizer_pool.setdefault(template_name, VideoSynthesizer(template_name, self.template_fixed_landmarks))
        template_frame_seq = self.synthesizer_pool[template_name].template_frame_seq
        return template_frame_seq

    def _generate_listening(self, waiting_frame_num):
        LOG.info('put listening anchor {} {} frames in task queue'.format(self, waiting_frame_num))
        with self.task_mutex:
            self.task_state = AnchorState.listening
            self.task_queue.put(AnchorTask(viseme_frame_seq=[None for i in range(waiting_frame_num)],
                                           wav_frame_seq=[self._blank_wave_frame(self.sampling_rate // self.frame_rate)
                                                          for i in range(waiting_frame_num)],
                                           anchor_state=AnchorState.listening,
                                           text_id=None,
                                           template_name=self.template_name))

    def _generate_speaking(self, viseme_frame_seq: Sequence[Tuple[np.ndarray, np.ndarray]],
                           wav_frame_seq: Sequence[np.ndarray], template_name, text_id=None):
        with self.task_mutex:
            self.task_state = AnchorState.speaking
            self.task_queue.put(AnchorTask(viseme_frame_seq=viseme_frame_seq,
                                           wav_frame_seq=wav_frame_seq,
                                           anchor_state=AnchorState.speaking, text_id=text_id,
                                           template_name=template_name))
        LOG.info('put speaking anchor {} {} frames in task queue'.format(self, len(viseme_frame_seq)))

    def generate(self):
        '''
        called in another thread.
        :return: None
        '''
        # while True:
        anchor_task = self.task_queue.get()
        if anchor_task is None:
            LOG.info('generating thread stop')
            self.stream.put(None)
            return
            # TODO stop here should be the proper place
            # with self.state_mutex:
            #     self.current_state = AnchorState.stop
            # break

        viseme_frame_seq = anchor_task.viseme_frame_seq
        wav_frame_seq = anchor_task.wav_frame_seq
        anchor_state = anchor_task.anchor_state
        text_id = anchor_task.text_id
        # TODO template_name
        for i, (viseme_frame, wav_frame) in enumerate(zip(viseme_frame_seq, wav_frame_seq)):
            # TODO async muti processing
            if self.async_mode:
                frame_async = self.pool.submit(self.template_frame_seq.synthesize,
                                               viseme_frame,
                                               self.template_frame_seq[self.frame_no + i]
                                               )

                self.stream.put((frame_async, wav_frame, text_id))
            # TODO sync one processing
            else:
                frame = self.template_frame_seq.synthesize(viseme_frame, self.template_frame_seq[self.frame_no + i])
                self.stream.put((frame, wav_frame, text_id))
        self.frame_no += 1
        with self.state_mutex:
            self.current_state = anchor_state

        LOG.info(
            'generating anchor task from stream_anchor text_id: {}, current_state {}'.format(text_id, anchor_state))


class FrameGenerator(threading.Thread):
    def __init__(self, stream_anchor: StreamAnchor):
        super(FrameGenerator, self).__init__()
        self.stream_anchor = stream_anchor

    def run(self):
        while True:
            self.stream_anchor.generate()
            if self.stream_anchor.get_state() == AnchorState.stop:
                break

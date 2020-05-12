import time
import math
import numpy as np
from fractions import Fraction
from threading import Thread, Event
from multiprocessing import Process, Value, Queue, Manager
from ctypes import c_char_p

import av
import av.datasets

from . import StreamAnchor
from .utils import LOG


class AnchorLive:

    def __init__(self, streamId, videoInfo, audioInfo,
                 rtsp_url, rtsp_option,
                 viseme_fixed_landmarks, template_fixed_landmarks,
                 default_template_name='aide', viseme_kind='aide',
                 num_worker=None, waiting_frame_num=15,
                 async_mode=False, debug=False, speack_over_callback=lambda text, textid, frame_no: None):
        """
        :param streamId:
        :videoInfo
        :audioInfo
        :speack_over_callback

        :param kwargs:
         kwargs eg.
            {
                "streamID":"uuid-uuid-uuid-uuid",
                "protocol":"rtsp",
                "speack_over_callback":"http://30.76.137.6:8099/callback",
                "media":{
                    "audio":{
                        “format”:{
                            "codec":"PCMA",
                            "sampleRate":8000,
                            "channelNum":1
                        }
                    },
                    "video":{
                        "format":{
                            "codec":"H264",
                            "profile":"Baseline"
                        },
                        "parameter":{
                            "resolution":{"width":640,"height":480},
                            "framerate":15,
                            "maxBitrate":500,
                            "keyFrameInterval":2
                        }
                    }
                }
            }
        """

        self.streamId = streamId
        self.speack_over_callback = speack_over_callback
        self.videoInfo = videoInfo
        self.audioInfo = audioInfo

        self.resolution = videoInfo.get("resolution", {"with": 640, "height": 480})
        # self.req_args = kwargs

        # init something
        self.init_const()  # 配置常量,streamID rtsp 音视频信息参数等 timebase等
        self.init_var()  # 配置变量,关于推流中 时间累加器
        self.init_process_share()  # 配置课程可共享的变量

        self.init_container(rtsp_url=rtsp_url, rtsp_option=rtsp_option)  # 配置pyav-rtsp容器

        # self.queue = Queue(5)
        # self.avitems = AVItems(self.queue)
        self.avitems = StreamAnchor(frame_rate=self.framerate,
                                    num_worker=num_worker,
                                    sampling_rate=self.sampleRate,
                                    viseme_fixed_landmarks=viseme_fixed_landmarks,
                                    template_fixed_landmarks=template_fixed_landmarks,
                                    default_template_name=default_template_name,
                                    viseme_kind=viseme_kind,
                                    waiting_frame_num=waiting_frame_num,
                                    async_mode=async_mode,
                                    debug=debug,
                                    )

    def init_const(self):
        # media info
        # self.resolution = {"with":640,"height":480} # 视频分辨率
        self.width = self.resolution.get("width")
        self.height = self.resolution.get("height")
        self.framerate = self.videoInfo.get("framerate", 25)
        # audio info
        if self.audioInfo.get("channelNum") != 1:
            LOG.warning('not support audio channel more then 1')
        self.channelNum = 1  # 音频声道数
        self.sampleRate = self.audioInfo.get("sampleRate", 16000)  # 音频采样率
        self.layout_set = {1: "mono", 2: "stereo", }
        self.layout = self.layout_set[self.channelNum]
        # time_base
        self.video_time_base = 1 / self.framerate
        self.audio_time_base = 1 / (self.sampleRate / 1024)

    def init_var(self):
        # ---- init meida options ----
        self.video_fps = 0
        self.audio_fps = 0
        self.audio_time = 0
        self.video_time = 0

    def init_process_share(self):
        # self.status = Value('i', 0)
        self.waiting_value = "waiting"
        self.speaking_value = "speaking"
        self.text_map = {}
        self.event = Event()
        # self.manager = Manager()
        # self.status = self.manager.Value(c_char_p, self.waiting_value)
        # self.seqNo = self.manager.Value(c_char_p, None)
        # self.frame_index = Value('i', 0)

    def init_container(self, rtsp_url, rtsp_option):
        self.rtsp_options = {'rtsp_transport': rtsp_option}
        self.rtsp = '{}/{}'.format(rtsp_url, self.streamId)
        self.rtsp_network = '{}/{}'.format(rtsp_url, self.streamId)
        self.container = av.open(self.rtsp, 'w', format='rtsp', options=self.rtsp_options)
        # self.container init_process_share= av.open("test.mkv","w")

        # print("init_container...")
        self.video_stream = self.container.add_stream('mpeg2video', rate=self.framerate)
        self.video_stream.pix_fmt = 'yuv420p'
        self.video_stream.width = self.width
        self.video_stream.height = self.height
        self.video_stream.codec_context.time_base = Fraction(1, self.framerate)

        self.audio_stream = self.container.add_stream('aac', rate=self.sampleRate, layout=self.layout)  # layout="mono"
        self.audio_stream.codec_context.time_base = Fraction(1, self.sampleRate)
        # print(self.audio_stream)
        # print("init_container...done")

    def get_seqNo(self):
        if self.seqNo.value == None:
            return ""
        return self.seqNo.value

    def encode_video_ndarray(self, vframe_ndarray):
        # self.video_fps += 1
        # self.video_time += self.video_time_base
        vframe = av.VideoFrame.from_ndarray(vframe_ndarray, format='rgb24')
        # LOG.info(f'v {vframe}')
        for packet in self.video_stream.encode(vframe):
            packet.pts = self.video_fps
            self.video_fps += 1
            self.video_time += self.video_time_base
            self.container.mux(packet)

    def encode_audio_ndarray(self, aframe_ndarray):
        aframe_ndarray_reshape = aframe_ndarray.reshape((1, len(aframe_ndarray)))
        aframe = av.AudioFrame.from_ndarray(aframe_ndarray_reshape, format='s16', layout=self.layout)
        aframe.rate = self.sampleRate
        aframe.sample_rate = self.sampleRate
        aframe.time_base = Fraction(1, self.sampleRate)
        aframe.pts = None

        # LOG.info(f'a {aframe}')
        for packet in self.audio_stream.encode(aframe):
            # LOG.info('a {packet}')
            packet.pts = self.audio_fps * 1024
            self.audio_fps += 1
            self.audio_time += self.audio_time_base
            self.container.mux(packet)

    def worker(self):

        # 初始化 嘉楠的 主播类
        # start and get frame
        self.avitems.start_stream()
        self.event.set()

        tmp_seqNo = None

        for vframe_ndarray, aframe_ndarray, seqNo, in self.avitems:
            # time.sleep(0.035)
            if seqNo != tmp_seqNo:
                # # 改变状态
                print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
                if seqNo == None:  # speaking -> waiting
                    print("----> 0")
                    Thread(target=lambda: self.speack_over_callback(self.text_map[tmp_seqNo], str(seqNo),
                                                                    str(self.avitems.frame_no))).start()
                else:  # waiting -> speaking
                    print("----> 1")
                tmp_seqNo = seqNo
            self.encode_audio_ndarray(aframe_ndarray)
            self.encode_video_ndarray(vframe_ndarray)

    def start(self):

        self.p = Thread(target=self.worker)
        self.p.start()
        self.event.wait()
        return True

    def stop(self):
        self.avitems.stop_stream()
        if self.p.is_alive():
            # self.p.terminate()
            self.p.join()

    def put_text(self, text, wav_path, text_id):
        self.avitems.put_text_wav(text, wav_path, text_id)
        self.text_map[text_id] = text
        # self.queue.put(text)
        return True

    def get_status(self):
        print('h')
        return str(self.avitems.get_state().value)



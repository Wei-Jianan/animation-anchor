import sys
from pathlib import Path
import numpy as np
import uuid
from multiprocessing import Process
import subprocess

sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

import shutil
import os, time
import concurrent.futures
from animation_anchor import Anchor, StreamAnchor, AnchorState, AnchorLive
from animation_anchor.utils import LOG

STREAM_MODE = True
LIVE_MODE = True


def stream_generating(stream_anchor):
    LOG.info('starting get frame from stream_anchor')
    video_frames = []
    audio_frames = []
    for i, (video_frame, audio_frame, text_id) in enumerate(stream_anchor):
        LOG.info('got {} st frame from stream_anchor with text_id {}'.format(i, text_id))
        video_frames.append(video_frame)
        audio_frames.append(audio_frame)
    return video_frames, audio_frames


if __name__ == '__main__':

    os.makedirs('aide', exist_ok=True)
    if not STREAM_MODE:
        anchor = Anchor(frame_rate=25, viseme_kind='aide', viseme_fixed_landmarks=[[0, 0], [60, 36]],
                        template_fixed_landmarks=[[210, 234], [270, 270]])
        example_dir = Path(__file__).parent.resolve()
        # video_file = anchor.inference('啦,啦,啦，我是卖报的小行家, 大风大雨都不怕', template_name='aide')
        # with open('example.mp4', 'wb') as f:
        #     shutil.copyfileobj(video_file, f)
        for i in range(1, 6, 1):
            txt_path = '{:0>2d}.txt'.format(i)
            wav_path = '{:0>2d}.wav'.format(i)
            video_path = 'aide/{:0>2d}.mp4'.format(i)
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt = f.read()
            video_file = anchor.inference(text=txt, wav_path=wav_path, template_name='aide')
            with open(video_path, 'wb') as f:
                shutil.copyfileobj(video_file, f)
            video_file.close()
    elif LIVE_MODE and STREAM_MODE:
        init_args = {
            "streamID": "abc",
            "speack_over_callback": "speack_over_callback",
            "videoInfo": {
                "resolution": {"width": 640, "height": 480},
                "framerate": 15,
            },

            "audioInfo": {
                "sampleRate": 16000,
                "channelNum": 1
            },
        }

        anchor_live = AnchorLive(init_args["streamID"], init_args["videoInfo"], init_args["audioInfo"],
                                 # speack_over_callback=init_args["speack_over_callback"],
                                 rtsp_url="rtsp://localhost:8554", rtsp_option='tcp',
                                 viseme_kind='aide',
                                 viseme_fixed_landmarks=[[0, 0], [60, 36]],
                                 template_fixed_landmarks=[[210, 234], [270, 270]],
                                 default_template_name='aide',
                                 waiting_frame_num=10,
                                 speack_over_callback=lambda text, text_id, frame_no: LOG.warning(
                                     '!!!!!!!!' + text + str(text_id) + ' frame_no: ' + str(frame_no))
                                 )
        anchor_live.start()
        # subprocess.Popen(['ffplay', '-i', str(anchor_live.rtsp)])
        print(anchor_live.rtsp)
        for i in range(1, 6, 1):
            txt_path = '{:0>2d}.txt'.format(i)
            wav_path = '{:0>2d}.wav'.format(i)
            print("----------GET_STATE-------------", anchor_live.get_status())
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            anchor_live.put_text(text, wav_path=wav_path, text_id=str(uuid.uuid4()))

            print("----------GET_STATE-------------", anchor_live.get_status())
            listening_time = abs(np.random.normal()) * 15
            # listening_time = 20
            LOG.info('listening customer for {} seconds'.format(listening_time))
            time.sleep(abs(listening_time))
            print("----------GET_STATE-------------", anchor_live.get_status())
        # anchor_live.stop()


    else:
        stream_anchor = StreamAnchor(frame_rate=25,
                                     num_worker=4,
                                     viseme_kind='aide',
                                     viseme_fixed_landmarks=[[0, 0], [60, 36]],
                                     template_fixed_landmarks=[[210, 234], [270, 270]],
                                     default_template_name='aide',
                                     waiting_frame_num=15,
                                     async_mode=False
                                     )

        stream_anchor.start_stream()
        executor = concurrent.futures.ThreadPoolExecutor()

        anchor_frames_async = executor.submit(stream_generating, stream_anchor)
        # time.sleep(3)
        for i in range(1, 6, 1):
            txt_path = '{:0>2d}.txt'.format(i)
            wav_path = '{:0>2d}.wav'.format(i)
            with open(txt_path, 'r', encoding='utf-8') as f:
                txt = f.read()
            stream_anchor.put_text_wav(text=txt, wav_path=wav_path,
                                       text_id=i, template_name='aide')
            time.sleep(abs(np.random.normal()) * 3)
        stream_anchor.stop_stream()
        frames, audio_frames = anchor_frames_async.result()
        # frames, audio_frames = stream_generating(stream_anchor)
        wave_file = stream_anchor._combine_wav(audio_frames)
        video_file = stream_anchor.write_video(frames, wave_file.name)

        executor.shutdown(wait=True)
        with open('aide.mp4', 'wb') as f:
            shutil.copyfileobj(video_file, f)

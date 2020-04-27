import unittest
import sys
from pathlib import Path
import shutil
import concurrent.futures
sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

from animation_anchor import StreamAnchor, AnchorState


def stream_generating(stream_anchor):
    video_frames = []
    audio_frames = []
    for video_frame, audio_frame, _ in stream_anchor:
        video_frames.append(video_frame)
        audio_frames.append(audio_frame)
        if stream_anchor.get_state() == AnchorState.ready:
            break
    return video_frames, audio_frames



class TestStreamAnchor(unittest.TestCase):
    def setUp(self):
        self.stream_anchor = StreamAnchor(frame_rate=25,
                                          viseme_kind='aide',
                                          viseme_fixed_landmarks=[[0, 0], [60, 36]],
                                          template_fixed_landmarks=[[210, 234], [270, 270]],
                                          default_template_name='aide', num_worker=1,
                                          waiting_frame_num=30
                                          )

    def test_split_wav(self):
        wave_data = self.stream_anchor._split_wav('11.mp3')
        wave_file = self.stream_anchor._combine_wav(wave_data)
        with open('temp_11.wav', 'wb') as f:
            shutil.copyfileobj(wave_file, f)


    def test_end2end_inference(self):
        self.stream_anchor.start_stream()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            frame_async = executor.submit(stream_generating, self.stream_anchor)
            self.stream_anchor.put_text_wav()








if __name__ == '__main__':
    unittest.main()

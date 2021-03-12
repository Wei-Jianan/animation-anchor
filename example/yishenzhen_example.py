import sys
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt


sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

import shutil
import os
from animation_anchor import Anchor

if __name__ == '__main__':
    anchor = Anchor(frame_rate=25, viseme_kind='yishenzhen', viseme_fixed_landmarks=[[0, 0], [180, 100]],
                    template_fixed_landmarks=[[610, 510], [790, 610]])
    example_dir = Path(__file__).parent.resolve()

    os.makedirs('yishenzhen', exist_ok=True)

    for i in range(1, 6, 1):
        i = 0
        txt_path = '{:0>2d}.txt'.format(i)
        wav_path = '{:0>2d}.wav'.format(i)
        video_path = './yishenzhen/{:0>2d}.mp4'.format(i)

        with open(txt_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        video_file = anchor.inference(text=txt, wav_path=wav_path, template_name='yishenzhen')
        with open(video_path, 'wb') as f:
            shutil.copyfileobj(video_file, f)
        print('copy to {}'.format(video_path))
        video_file.close()

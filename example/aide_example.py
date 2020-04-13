import sys
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

import shutil
import os
from animation_anchor import Anchor

if __name__ == '__main__':
    anchor = Anchor(frame_rate=25, viseme_kind='aide', viseme_fixed_landmarks=[[0, 0],[60, 36]],
                    template_fixed_landmarks=[[210, 234], [270, 270]])
    example_dir = Path(__file__).parent.resolve()
    # video_file = anchor.inference('啦,啦,啦，我是卖报的小行家, 大风大雨都不怕', template_name='aide')
    # with open('example.mp4', 'wb') as f:
    #     shutil.copyfileobj(video_file, f)
    os.makedirs('aide', exist_ok=True)
    for i in range(1,6,1):
        txt_path = '{:0>2d}.txt'.format(i)
        wav_path = '{:0>2d}.wav'.format(i)
        video_path = 'aide/{:0>2d}.mp4'.format(i)
        with open(txt_path, 'r', encoding='utf-8') as f:
            txt = f.read()
        video_file = anchor.inference(text=txt, wav_path=wav_path, template_name='aide')
        with open(video_path, 'wb') as f:
            shutil.copyfileobj(video_file, f)
        video_file.close()



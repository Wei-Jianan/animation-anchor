import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.joinpath('..').resolve()))

import shutil
from animation_anchor import Anchor

if __name__ == '__main__':
    anchor = Anchor(frame_rate=25, viseme_fixed_landmarks=[[0, 0],[60, 36]],
                    template_fixed_landmarks=[[210, 234], [270, 270]])
    video_file = anchor.inference('啦,啦,啦，我是卖报的小当家, 大风大雨都不怕', template_name='aide')
    with open('example.mp4', 'wb') as f:
        shutil.copyfileobj(video_file, f)
    video_file.close


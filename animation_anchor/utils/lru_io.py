import cv2
import numpy as np
from pathlib import Path
from functools import lru_cache


def alpha_blend(img):
    if len(img.shape) == 1:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    # print('img shape: ', img.dtype)
    if len(img.shape) == 3:
        if img.shape[2] == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if img.shape[2] == 4:
            foreground = img[:, :, 0:3]
            alpha = img[:, :, 3]
            alpha = np.stack((alpha, alpha, alpha), axis=-1)
            alpha = np.floor(alpha.astype(np.float16) / 255)
            # return cv2.cvtColor(foreground, cv2.COLOR_BGR2RGB)
            foreground = cv2.cvtColor(foreground, cv2.COLOR_BGR2RGB).astype(np.float16)
            background = np.zeros_like(foreground).astype(np.float16)
            out_img = alpha * foreground + (1 - alpha) * background
            return out_img.astype(np.uint8)


@lru_cache()
def read_frames(viseme_dir):
    img_types = ('*.jpg', '*.png')
    frames_path = []
    for img_type in img_types:
        frames_path.extend(sorted(Path(viseme_dir).glob(img_type)))
    if len(frames_path) == 0:
        raise FileNotFoundError('there should be one and only be one *.txt in material dir {}'.format(viseme_dir))
    frames = [alpha_blend(cv2.imread(str(frame_path), cv2.IMREAD_UNCHANGED)) for frame_path in frames_path]
    return frames


@lru_cache()
def read_landmarks(viseme_dir):
    landmarks_files = list(Path(viseme_dir).glob('*.txt'))
    if len(landmarks_files) == 0 or len(landmarks_files) > 1:
        raise FileNotFoundError('there should be one and only be one *.txt in material dir {}'.format(str(viseme_dir)))
    landmarks_file = landmarks_files[0]
    landmarks = np.loadtxt(str(landmarks_file))
    if len(landmarks.shape) != 2 or landmarks.shape[1] != 2:
        raise ValueError('the shape of landmarks must be T * 2 instead of {}'.format(landmarks.shape))
    return landmarks

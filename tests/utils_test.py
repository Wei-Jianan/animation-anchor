from matplotlib import pyplot as plt
from animation_anchor.utils import read_frames
if __name__ == '__main__':
    frames = read_frames('/Users/jiananwei/Downloads/平安爱德-虚拟主播动画资源/C2')
    print(frames[0])
    fig = plt.figure()
    for frame in frames:
        plt.imshow(frame)
        plt.show()


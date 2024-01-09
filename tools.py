import random
from moviepy.editor import *

PERCENTS = (0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100)


def invert_green_blue(image):
    """
    Inverts green and blue pixels of a clip (VideoFileClip)
    """
    return image[:, :, [0, 2, 1]]


def get_closest_percent(percent):
    """
    returns lowest passed threshold
    """
    for p in PERCENTS:
        if percent - p < 10:
            return p


def preload(videos_path, resolution):
    """
    preloads all video files once
    """

    videos_list = []
    width, height = int(int(resolution) * (16 / 9)), int(resolution)
    print('Preloading videos from video path "{}"'.format(videos_path))

    for vid in os.listdir(videos_path):
        # seed to randomise individual videos orientation / colour to give illusion of change between videos
        randomizer = random.random()
        if randomizer < 0.3:
            videos_list.append(VideoFileClip(videos_path + vid, target_resolution=(height, width)))
        elif randomizer < 0.6:
            videos_list.append(VideoFileClip(videos_path + vid, target_resolution=(height, width)).fl_image(invert_green_blue))
        elif randomizer < 0.9:
            videos_list.append(VideoFileClip(videos_path + vid, target_resolution=(height, width)).fx(vfx.mirror_x))
        else:
            videos_list.append(VideoFileClip(videos_path + vid, target_resolution=(height, width)).fl_image(invert_green_blue).fx(vfx.mirror_y))

    for vid in videos_list:
        if vid.size[0] > width or vid.size[1] > height:
            print(vid.filename)
            videos_list.remove(vid)

    return videos_list

from GenerateTimeStamps import *
from moviepy.editor import *

import random, math, os, sys

"""
Simple, randomized, tempo synced video generation
"""

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
    print("Preloading videos from video path: " + videos_path)
    print(width + height)

    for vid in os.listdir(videos_path):
        randomizer = random.random()  # seed to randomise individual videos orientation / colour to give illusion of change between videos
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


def make_sub_movie(music_file_path, bpm, videos_list, idx, start, finish, duration, resolution):
    """
    Saves a simple movie synced to the provided audio file

    music_file_path (str): path to song (.wav)
    bpm (int / float): beats per minute tempo of the song
    videos_list (list): videos to use
    idx (int): video index

    start: first downbeat
    finish: last downbeat
    duration: total duration
    resolution: desired output resolution (ex: 1080 or 720)
    """

    filename = music_file_path.split(os.sep)[-1:]
    main_folder = os.path.join(*music_file_path.split(os.sep)[:-1])
    titles_path = os.path.join(str(main_folder), 'titles' + os.sep)
    temp_path = os.path.join(str(main_folder), 'temp' + os.sep)
    length_of_a_beat = 1 / (bpm / 60)  # time between beats
    videos = []

    # black screen on start
    if 0 < start < 4:
        videos.append(VideoFileClip(titles_path + random.choice([x for x in os.listdir(titles_path)])).subclip(0, start).fx(vfx.colorx, 0.0))
    
    # ambient intro on start
    elif start > 0:
        clip = VideoFileClip(titles_path + random.choice([x for x in os.listdir(titles_path)])).subclip(0, start)
        videos.append(clip.fx(vfx.fadein, duration=clip.duration/2))

    new4_bar_block = True  # outlines every 4 bars to switch up speeds
    beats = 0  # current beats rendered
    current_render_percent = 0  # used to print progress to console

    print("Generating video " + str(idx + 1))
    
    while start < finish:

        # switch up video rate every 4 bars
        if beats % 16 == 0:
            new4_bar_block = True

        if new4_bar_block:
            i = random.choice([1, 4, 4, 4, 8, 8, 16, 16, 16])  # random rate of change of the videos
            
        while True:
            try:  # try / catch block to account for videos that are not long enough
                video = random.choice(videos_list)
                video_start = random.randint(0, math.floor(video.duration - length_of_a_beat * i))  # random video portion
                break
            except ValueError:
                continue
        
        videos.append(video.subclip(video_start, video_start + length_of_a_beat * i))
    
        start += (length_of_a_beat * i)
        beats += i

        # print progress to screen
        percent_rendered = get_closest_percent(start / finish * 100)
        if percent_rendered != current_render_percent:
            current_render_percent = percent_rendered
            print(str(current_render_percent) + "%/ rendered")

        new4_bar_block = False
    
    # Ambient outro
    if start < duration:
        clip = VideoFileClip(titles_path + random.choice([x for x in os.listdir(titles_path)])).subclip(0, duration-start)
        videos.append(clip.fx(vfx.fadeout, duration=clip.duration/2))

    final_clip = concatenate_videoclips(videos, method="compose")

    width, height = int(resolution * (16 / 9)), int(resolution)
    if final_clip.size == (width, height):
        # write video
        final_clip.write_videofile(filename=temp_path + str(filename) + str(idx) + "_resized.mp4", preset="ultrafast", threads=6, audio=False)
    else:
        # name output differently to denote not yet 720p
        final_clip.write_videofile(filename=temp_path + str(filename) + str(idx) + ".mp4", preset="ultrafast", threads=6, audio=False)

    # memory save
    for v in videos:
        v.close()
    final_clip.close()


def main(argv):
    music_file_path = argv[0]
    bpm = argv[1]
    complexity = argv[2]
    resolution = argv[3]

    print("Analysing waveform")
    start, finish = guess_first_and_last_down_beat(music_file_path)
    duration = get_duration(music_file_path)

    main_folder = os.path.join(*music_file_path.split(os.sep)[:-2])
    videos_path = os.path.join(str(main_folder), 'videos' + os.sep)
    videos_list = preload(videos_path, resolution)
    for idx in range(int(complexity)):
        make_sub_movie(music_file_path, int(bpm), videos_list, idx, start, finish, duration, resolution)


if __name__ == "__main__":
    main(sys.argv[1:])

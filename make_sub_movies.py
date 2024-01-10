import math
import random
import logging as log
from os.path import join, split, splitext

from moviepy.editor import *
# from multiprocessing import Pool
from mutiprocessing_log import LoggingPool

from generate_timestamps import *
from tools import preload, get_closest_percent

'''
If simple_vid: Simple, randomized, tempo synced video generation
If smart_vid: Dynamic video generation - Intense sections of music will have faster visuals
'''

HIGH_INTENSITY = [1, 1, 1, 4, 4, 4]
MEDIUM_INTENSITY = [4, 4, 4, 4, 8, 8, 8, 16]
LOW_INTENSITY = [8, 8, 8, 16, 16, 16, 16]


def make_sub_movie(music_file_path: str, bpm: float, videos_list: list, idx: int,
                   start: float, finish: float, duration: float, intensities: dict, resolution: str, dynamic: str):
    """
    Saves a simple or smart movie synced to the provided audio file

    music_file_path (str): path to song (.wav)
    bpm (int / float): beats per minute tempo of the song
    videos_list (list): videos to use
    idx (int): video index

    start: first downbeat
    finish: last downbeat
    duration: total duration
    resolution (str): desired output resolution (ex: 1080 or 720)
    """

    song_name, _ = splitext(split(music_file_path)[1])
    project_folder = f"{join(*music_file_path.split(os.sep)[:-2])}"
    titles_path = str(join(project_folder, 'titles' + os.sep))
    titles_list = os.listdir(titles_path)
    temp_path = str(join(project_folder, 'temp' + os.sep))
    length_of_a_beat = 60 / bpm   # time between beats
    videos = []

    # black screen on start
    if 0 < start < 4:
        videos.append(VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, start).fx(vfx.colorx, 0.0))

    # ambient intro on start
    elif start > 0:
        clip = VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, start)
        videos.append(clip.fx(vfx.fadein, duration=clip.duration/2))

    new4_bar_block = True  # outlines every 4 bars to switch up speeds
    current4_bar_block = 0  # current 4 bar block to pull intensities from
    fade_out = False  # used to fade out before a drop
    beats = 0  # current beats rendered

    current_render_percent = 0  # used to print progress to console

    print(f"Generating video {song_name}_subVid{idx}.mp4")

    while start < finish if dynamic == 'simple_vid' else beats < (len(intensities) * 16):

        # switch up video rate every 4 bars
        if beats % 16 == 0:
            new4_bar_block = True

        if new4_bar_block:

            # simple video case (static video selection) #
            if dynamic == 'simple_vid':
                i = random.choice([1, 4, 4, 4, 8, 8, 16, 16, 16])  # random rate of change of the videos

            # smart video case (dynamic video selection) #
            elif dynamic == 'smart_vid':
                if intensities[current4_bar_block] == "High":
                    # If the previous section was low and this one is high, make it speedy by default
                    if current4_bar_block > 0 and intensities[current4_bar_block - 1] == "Low":
                        i = 1
                    else:
                        i = random.choice(HIGH_INTENSITY)
                elif intensities[current4_bar_block] == "Medium":
                    i = random.choice(MEDIUM_INTENSITY)
                else:
                    try:
                        # Check next section is a "drop"
                        if intensities[current4_bar_block + 1] == "High":
                            i = 16
                            fade_out = True
                        else:
                            i = random.choice(LOW_INTENSITY)
                    except KeyError:
                        i = random.choice(LOW_INTENSITY)
                current4_bar_block += 1

        while True:
            try:  # try / catch block to account for videos that are not long enough
                video = random.choice(videos_list)
                video_start = random.randint(0, math.floor(video.duration - length_of_a_beat * i))  # random video part
                break
            except ValueError:
                continue

        if not fade_out:
            videos.append(video.subclip(video_start, video_start + length_of_a_beat * i))
        else:  # fadeout before a drop
            video_fade_out = video.subclip(video_start, video_start + length_of_a_beat * i)
            videos.append(video_fade_out.fx(vfx.fadeout, duration=video_fade_out.duration / 4))
            fade_out = False

        start += (length_of_a_beat * i)
        beats += i

        # print progress to screen
        percent = start / finish * 100 if dynamic == 'simple_vid' else beats / (len(intensities) * 16) * 100
        percent_rendered = get_closest_percent(percent)
        if percent_rendered != current_render_percent:
            current_render_percent = percent_rendered
            print(f"{current_render_percent} %/ rendered")

        new4_bar_block = False

    # Ambient outro
    if start < duration:
        clip = VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, duration-start)
        videos.append(clip.fx(vfx.fadeout, duration=clip.duration/2))

    # Makes all videos at the same resolution
    print(f"Making sub videos {resolution}p")
    width, height = str(int(int(resolution) * (16 / 9))), resolution
    for vid in videos:
        if vid.h != int(height):
            print(f"resizing video {vid.filename}")
            output_path = splitext(vid.filename)[0] + "_resized" + splitext(vid.filename)[1]
            os.system("ffmpeg -hwaccel cuda -i " + vid.filename + " -c:v h264_nvenc -vf scale=" + width + ":" + height +
                      " -crf 18 -preset slow -qp 20 -y " + output_path + " -hide_banner -loglevel warning")  # -qp 20 -c:v h264_cuvid
            vid.size = (int(width), int(height))
            vid.filename = output_path

    final_clip = concatenate_videoclips(videos, method="compose")

    # write video
    os.makedirs(temp_path, exist_ok=True)
    final_clip.write_videofile(filename=temp_path + song_name + "_subVid" + str(idx) + ".mp4", bitrate='8000000',
                               threads=16, verbose=False, preset="slow", audio=False, codec="h264_nvenc")

    # memory save
    for v in videos:
        v.close()
    final_clip.close()


def main(argv):
    music_file_path = argv[0]
    bpm = argv[1]
    complexity = argv[2]
    resolution = argv[3]
    parallel_proc = argv[4]
    dynamic = argv[5]

    print(f"Analysing waveform of {split(music_file_path)[1]}")
    start, finish = guess_first_and_last_down_beat(music_file_path)
    duration = get_duration(music_file_path)
    intensities = get_intensities(music_file_path, bpm)

    main_folder = split(split(music_file_path)[0])[0]
    videos_path = join(main_folder, 'videos' + os.sep)
    videos_list = preload(videos_path, resolution)
    if parallel_proc:
        # p = Pool(processes=int(complexity)*2)
        with LoggingPool('%(asctime)-15s (PID %(process)-5d) [%(levelname)-8s]: %(message)s', level=log.INFO,
                         filename='import.log') as _:
            with LoggingPool().make_pool(6) as pool:
                for idx in range(int(complexity)):
                    # args = music_file_path, bpm, videos_list, idx, start, finish, duration, intensities, resolution, dynamic
                    pool.apply_async(make_sub_movie, (music_file_path, bpm, videos_list, idx, start, finish, duration, intensities, resolution, dynamic,))
                pool.close()
                pool.join()
    else:
        for idx in range(int(complexity)):
            args = music_file_path, bpm, videos_list, idx, start, finish, duration, intensities, resolution, dynamic
            make_sub_movie(*args)


if __name__ == "__main__":
    main(sys.argv[1:])

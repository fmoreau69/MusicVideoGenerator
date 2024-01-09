import math
import random

from moviepy.editor import *
from multiprocessing import Pool

from generate_timestamps import *
from tools import preload, get_closest_percent

"""
Simple, randomized, tempo synced video generation
"""


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

    filename = str(music_file_path.split(os.sep)[-1:][0])
    project_folder = str(os.path.join(*music_file_path.split(os.sep)[:-2]))
    titles_path = str(os.path.join(project_folder, 'titles' + os.sep))
    titles_list = os.listdir(titles_path)
    temp_path = str(os.path.join(project_folder, 'temp' + os.sep))
    length_of_a_beat = 1 / (bpm / 60)  # time between beats
    videos = []

    # black screen on start
    if 0 < start < 4:
        videos.append(VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, start).fx(vfx.colorx, 0.0))
    
    # ambient intro on start
    elif start > 0:
        clip = (VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, start))
        videos.append(clip.fx(vfx.fadein, duration=clip.duration/2))

    new4_bar_block = True  # outlines every 4 bars to switch up speeds
    beats = 0  # current beats rendered
    current_render_percent = 0  # used to print progress to console

    print("Generating video " + filename + "_subVid" + str(idx) + ".mp4")
    
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
        clip = VideoFileClip(titles_path + random.choice([x for x in titles_list])).subclip(0, duration-start)
        videos.append(clip.fx(vfx.fadeout, duration=clip.duration/2))

    # Makes all videos at the same resolution
    for vid in videos:
        width, height = str(int(int(resolution) * (16/9))), resolution
        if vid.h != int(height):
            print("resizing video " + vid.filename)
            output_path = os.path.splitext(vid.filename)[0] + "_resized" + os.path.splitext(vid.filename)[1]
            os.system("ffmpeg -hwaccel cuda -i " + vid.filename + "-c:v h264_nvenc -vf scale=" + width + ":" + height +
                      " -crf 18 -preset medium -y " + output_path + " -hide_banner -loglevel warning")  # -qp 20
            vid.size = (int(width), int(height))
            vid.filename = output_path  # .replace('_resized', '')
        else:
            print("Video" + vid.filename + " is already " + height + "p")

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
    parallel_proc = argv[4]

    print('Analysing waveform of "{}"'.format(str(music_file_path.split(os.sep)[-1])))
    start, finish = guess_first_and_last_down_beat(music_file_path)
    duration = get_duration(music_file_path)

    main_folder = os.path.join(*music_file_path.split(os.sep)[:-2])
    videos_path = os.path.join(str(main_folder), 'videos' + os.sep)
    videos_list = preload(videos_path, resolution)
    if parallel_proc:
        p = Pool(processes=int(complexity))
        for idx in range(int(complexity)):
            args = music_file_path, float(bpm), videos_list, idx, start, finish, duration, resolution
            p.apply_async(make_sub_movie, args=args)
        p.close()
        p.join()
    else:
        for idx in range(int(complexity)):
            args = music_file_path, float(bpm), videos_list, idx, start, finish, duration, resolution
            make_sub_movie(*args)


if __name__ == "__main__":
    main(sys.argv[1:])

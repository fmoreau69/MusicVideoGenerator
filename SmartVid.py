from GenerateTimeStamps import *
from moviepy.editor import *
from SimpleVid import preload, get_closest_percent
import random, math, os, sys

'''
Dynamic video generation - Intense sections of music will have faster visuals
'''

HIGH_INTENSITY = [1, 1, 1, 4, 4, 4]
MEDIUM_INTENSITY = [4, 4, 4, 4, 8, 8, 8, 16]
LOW_INTENSITY = [8, 8, 8, 16, 16, 16, 16]


def make_sub_movie(music_file_path, bpm, videos_list, idx, start, finish, duration, intensities, resolution):
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

    filename = str(music_file_path.split(os.sep)[-1:])
    main_folder = os.path.join(*music_file_path.split(os.sep)[:-2])
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
    current4_bar_block = 0  # current 4 bar block to pull intensities from
    fade_out = False  # used to fade out before a drop
    beats = 0  # current beats rendered

    current_render_percent = 0  # used to print progress to console
    
    print("Generating video " + str(idx + 1))

    while beats < (len(intensities) * 16):

        # switch up video rate every 4 bars
        if beats % 16 == 0:
            new4_bar_block = True

        if new4_bar_block:
            # DYNAMIC video selection
            if intensities[current4_bar_block] == "High":
                if current4_bar_block > 0 and intensities[current4_bar_block - 1] == "Low":  # If the previous section was low and this one is high, make it speedy by defualt
                    i = 1
                else:
                    i = random.choice(HIGH_INTENSITY) 

            elif intensities[current4_bar_block] == "Medium":
                i = random.choice(MEDIUM_INTENSITY)
            else: 
                try:
                    if intensities[current4_bar_block + 1] == "High":  # check next section is a "drop"
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
                video_start = random.randint(0, math.floor(video.duration - length_of_a_beat * i))  # random video portion
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
        percent_rendered = get_closest_percent((beats / (len(intensities) * 16) * 100))
        if percent_rendered != current_render_percent:
            current_render_percent = percent_rendered
            print(str(current_render_percent) + "%/ rendered")
       
        new4_bar_block = False
    
    # Ambient outro
    if start < duration:
        clip = VideoFileClip(titles_path + random.choice([x for x in os.listdir(titles_path)])).subclip(0, duration-start)
        videos.append(clip.fx(vfx.fadeout, duration=clip.duration/2))

    final_clip = concatenate_videoclips(videos, method="compose")
    
    width, height = int(int(resolution) * (16 / 9)), int(resolution)
    if final_clip.size == (width, height):
        # write video
        final_clip.write_videofile(filename=temp_path + filename + str(idx) + "_resized.mp4", preset="ultrafast", threads=6, audio=False)
    else:
        # name output differently to denote not yet 720p
        final_clip.write_videofile(filename=temp_path + filename + str(idx) + ".mp4", preset="ultrafast", threads=6, audio=False)

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
    intensities = get_intensities(music_file_path, bpm)

    main_folder = os.path.join(*music_file_path.split(os.sep)[:-2])
    videos_path = os.path.join(str(main_folder), 'videos' + os.sep)
    videos_list = preload(videos_path, resolution)
    for idx in range(int(complexity)):
        make_sub_movie(music_file_path, round(float(bpm)), videos_list, idx, start, finish, duration, intensities, resolution)


if __name__ == "__main__":
    main(sys.argv[1:])

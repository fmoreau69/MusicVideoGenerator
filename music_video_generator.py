import os
import time
import tqdm
import argparse
import pixabay.core
from pexelsapi.pexels import Pexels
from os.path import exists, join, splitext
from video_downloader import video_downloader
import generate_timestamps
from make_sub_movies import main as make_sub_movies

# TODO:
# Add global progress-bar => In progress
# Add multithread capabilities => In progress
# Integrate AI video generation
# different time signature support

clean_up = False
download = False
CLI_mode = False  # if False => adjust parameters below

# parameters
complexity = '3'
dynamic = True
GPU_accel = True
output_res = '1080'
parallel_proc = False

ffmpeg_cmd_in, ffmpeg_cmd_codec = ["ffpb -hwaccel cuda -i ", " -c:v h264_nvenc"] if GPU_accel else ["ffpb -i ", ""]
ffmpeg_cmd_opt = " -hide_banner -loglevel warning -stats"

project_folder = 'E:\\FAB_COMPOS\\Video_songs\\Brest2008\\Clip2'

titles_queries = ['ocean']
videos_queries = ['boat', 'mariners', 'old ship', 'sailors', 'sea']
download_args = {
    'global': {'size': 'large', 'ratio': 16 / 9, 'minWidth': 1920, 'minHeight': 1080,
               'per_page': 100, 'video_nb': 10, 'ratio_strict': 1, 'keep_all': 0, 'sub_folders': False},
    'pixabay': {'use_api': 1, 'px': pixabay.core('41014354-df28462b05ba0f555a30ac65a'),
                'lang': 'en', 'orientation': 'horizontal', 'colors': 'all'},
    'pexels': {'use_api': 1, 'px': Pexels('f7H8h2PvP6H2CZgByxRqbGCsY8kTMsdr8mPlBzwTqcNOX5mSiWngfGkz'),
               'lang': 'en-US', 'orientation': 'landscape', 'colors': ''}
}


def music_video_generator(args):
    """
    Generates a Music Video based on a specific song by calling a few python files and movie editing command line tools

    Arguments:
    1. Project folder (required), path to the project folder
    2. Song name (optional: should be located in project_folder/music/)
    3. Song BPM (optional: automatically detected if not filled in)
    4. Complexity (optional: 2 or 3 | default: 3), 2 for quicker and 3 for more intense visuals
    5. dynamic (optional: True or False | default: True), True for dynamic visuals based on song intensity, False for random visuals
    6. Output (optional), Output file prefix e.g. MyVideo
    7. Output video resolution (optional: e.g. 1080 or 720 | default: 1080)

    """

    start = time.time()

    if download:
        video_downloader(titles_queries, join(project_folder, 'titles'), download_args)
        video_downloader(videos_queries, join(project_folder, 'videos'), download_args)

    # Generates n(complexity) number of randomized videos
    last_sub_input_name = (splitext(args.music_file_path.split(os.sep)[-1:][0])[0] +
                           '_subVid' + str(int(args.complexity) - 1) + '.mp4')
    if not exists(join(args.temp_path, last_sub_input_name)):
        sub_vid_args = args.music_file_path, float(args.bpm), args.complexity, args.output_res, args.parallel_proc
        if args.dynamic:
            os.system("python make_sub_movies.py {0} {1} {2} {3} {4} smart_vid".format(*sub_vid_args)) if CLI_mode \
                else make_sub_movies([*sub_vid_args, 'smart_vid'])
        else:
            os.system("python make_sub_movies.py {0} {1} {2} {3} {4} simple_vid".format(*sub_vid_args)) if CLI_mode \
                else make_sub_movies([*sub_vid_args, 'simple_vid'])

    # Blends all videos
    song_name, _ = splitext(args.music_file_path.split(os.sep)[-1:][0])
    sub_vid_paths = [join(args.temp_path, path) for path in reversed(os.listdir(args.temp_path)) if 'subVid' in path]
    blend_vid_paths = [''] * (len(sub_vid_paths)-1)
    mashed_vid_paths = [''] * (len(sub_vid_paths)-2)
    generated_output_path = join(args.temp_path, song_name + "_generated.mp4")
    count = 0
    for i in reversed(range(len(sub_vid_paths)-1)):
        count += 1
        blend_vid_paths[i] = sub_vid_paths[i+1].replace("subVid", 'blended')
        if not exists(blend_vid_paths[i]):
            print("Blending sub videos together " + str(count))
            os.system(ffmpeg_cmd_in + sub_vid_paths[i+1] + " -i " + sub_vid_paths[i] + ffmpeg_cmd_codec +
                      " -filter_complex blend='difference' -y " + blend_vid_paths[i] + ffmpeg_cmd_opt)
            if i == 0 and len(blend_vid_paths) == 1:
                os.rename(blend_vid_paths[0], generated_output_path)
        if i < len(sub_vid_paths)-2 and not exists(mashed_vid_paths[i]):
            print("Blending those blended videos together " + str(count-1))
            mashed_vid_paths[i] = blend_vid_paths[i+1].replace("blended", 'mashed')
            os.system(ffmpeg_cmd_in + blend_vid_paths[i+1] + " -i " + blend_vid_paths[i] + ffmpeg_cmd_codec +
                      " -filter_complex blend='difference' -y " + mashed_vid_paths[i] + ffmpeg_cmd_opt)
            if i == 0 and len(mashed_vid_paths) == 1:
                os.rename(mashed_vid_paths[0], generated_output_path)
        if i < len(sub_vid_paths)-3 and not exists(generated_output_path):
            print("Mashing those blended videos together")
            os.system(ffmpeg_cmd_in + mashed_vid_paths[i+1] + " -i " + mashed_vid_paths[i] + ffmpeg_cmd_codec +
                      " -filter_complex blend='difference' -y " + generated_output_path + ffmpeg_cmd_opt)

    # chromashift to add pizazz\
    temp_input_file = join(args.temp_path, song_name + "_generated.mp4")
    temp_output_file = join(args.temp_path, song_name + "_generated_final.mp4")
    if not exists(temp_output_file):
        print("Glitching final result")
        os.system(ffmpeg_cmd_in + temp_input_file + ffmpeg_cmd_codec +
                  " -vf chromashift=crv=-200:cbv=100:crh=100 -qp 20 " + temp_output_file + ffmpeg_cmd_opt)

    # make temporary .aac file and add it to the mp4 video (.wav not supported directly)
    output_path_final = temp_output_file.replace("temp", 'out')
    temp_audio_file = join(args.temp_path, song_name + "_temp.aac")
    if not (exists(output_path_final) or exists(temp_audio_file)):
        print("Copying Audio and adding it to video clip")
        os.system(ffmpeg_cmd_in + args.music_file_path + " -ab 256k " + temp_audio_file + ffmpeg_cmd_opt)
        os.makedirs(args.temp_path.replace("temp", 'out'), exist_ok=True)
        os.system(ffmpeg_cmd_in + temp_output_file + " -i " + temp_audio_file +
                  " -c copy -map 0:v:0 -map 1:a:0 " + output_path_final + ffmpeg_cmd_opt)

    # file clean up
    if clean_up:
        print("deleting temporary files")
        for vid in os.listdir(args.temp_path):
            os.remove(join(args.temp_path, vid))

    end = time.time()
    print("Total program runtime, in seconds - " + str(end - start))


def parse_args():
    if CLI_mode:
        parser = argparse.ArgumentParser(description='Generate a music video - talent free!')
        parser.add_argument("--project_folder", help="Path to project folder with all directories it contains")
        parser.add_argument("--song_name", help="Song name (should be located in project_folder/music/)")
        parser.add_argument("--bpm", help="Song BPM (automatically detected if not filled in)")
        parser.add_argument("--complexity", default="3",
                            help="Complexity (2 OR 3), 2 for quicker and 3 for more intense visuals (3 by default)")
        parser.add_argument("--dynamic", default=True,
                            help="True for dynamic visuals based on song intensity, False for random visuals")
        parser.add_argument("--output", help="Output file prefix eg MyVideo")
        parser.add_argument("--output_res", default="1080", help="Output video resolution, 1080 or 720")
        parser.add_argument("--parallel_proc", default=True, help="Use multiprocessing to improve performances")
        args = parser.parse_args()
    else:
        args = argparse.Namespace(project_folder=project_folder,
                                  song_name='',
                                  bpm='',
                                  complexity=complexity,
                                  dynamic=dynamic,
                                  output='',
                                  output_res=output_res,
                                  parallel_proc=parallel_proc)

    # Defining additional necessary arguments
    args.project_folder = args.project_folder if args.project_folder else os.getcwd()
    args.song_name = args.song_name if args.song_name else str(os.listdir(join(args.project_folder, "music"))[0])
    args.music_file_path = str(join(args.project_folder, "music", args.song_name))
    args.titles_path = str(join(args.project_folder, "titles" + os.sep))
    args.videos_path = str(join(args.project_folder, "videos" + os.sep))
    args.temp_path = str(join(args.project_folder, "temp" + os.sep))
    args.bpm = str(generate_timestamps.guess_bpm(args.music_file_path)) if not args.bpm else args.bpm

    return args


if __name__ == "__main__":
    music_video_generator(parse_args())

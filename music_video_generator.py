import os
import time
import argparse

from numba import jit, cuda
import generate_timestamps

# TODO:
# Add multithread capabilities
# different time signature support
# Integrate video_downloader to automatically download videos based on tags


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
    
    # Generates n(complexity) number of randomized videos
    if args.dynamic:
        os.system("python smart_vid.py " + args.music_file_path + " " + args.bpm + " " + args.complexity + " " + args.output_res)
    else:
        os.system("python simple_vid.py " + args.music_file_path + " " + args.bpm + " " + args.complexity + " " + args.output_res)
    
    # Makes all videos at the same resolution
    print("making sub videos " + args.output_res + "p")
    for i in range(int(args.complexity)):
        temp_input_file = os.path.join(args.temp_path, args.song_name + str(i) + ".mp4")
        temp_output_file = os.path.join(args.temp_path, args.song_name + str(i) + "_resized.mp4")
        if not os.path.exists(temp_output_file):
            print("resizing video" + str(i))
            width, height = str(int(args.output_res) * (16/9)), args.output_res
            os.system("ffmpeg -i " + temp_input_file + " -vf scale=" + width + ":" + height +
                      " -crf 18 -preset medium -tune film " + temp_output_file + " -hide_banner -loglevel warning")
        else:
            print("Video" + str(i) + " is already " + args.output_res + "p")

    # Blends all videos
    if int(args.complexity) == 3:
        for i in range(int(args.complexity) - 1):
            print("Blending videos together " + str(i + 1))
            temp_input_file_1 = os.path.join(args.temp_path, args.song_name + str(i) + "_resized.mp4")
            temp_input_file_2 = os.path.join(args.temp_path, args.song_name + str(i + 1) + "_resized.mp4")
            temp_output_file = os.path.join(args.temp_path, args.song_name + str(i) + "_output.mp4")
            os.system("ffmpeg -i " + temp_input_file_1 + " -i " + temp_input_file_2 +
                      " -filter_complex blend='difference' " + temp_output_file + " -hide_banner -loglevel warning")
        
        print("Mashing those blended videos together")
        temp_input_file_1 = os.path.join(args.temp_path, args.song_name + "0_output.mp4")
        temp_input_file_2 = os.path.join(args.temp_path, args.song_name + "1_output.mp4")
        temp_output_file = os.path.join(args.temp_path, args.song_name + "_generated.mp4")
        os.system("ffmpeg -i " + temp_input_file_1 + " -i " + temp_input_file_2 +
                  " -filter_complex blend='difference' " + temp_output_file + " -hide_banner -loglevel warning")

    elif int(args.complexity) == 2:
        print("Blending")
        for i in range(int(args.complexity)-1):
            temp_input_file_1 = os.path.join(args.temp_path, args.song_name + str(i) + "_resized.mp4")
            temp_input_file_2 = os.path.join(args.temp_path, args.song_name + str(i + 1) + "_resized.mp4")
            temp_output_file = os.path.join(args.temp_path, args.song_name + "_generated.mp4")
            os.system("ffmpeg -i " + temp_input_file_1 + " -i " + temp_input_file_2 +
                      " -filter_complex blend='difference' " + temp_output_file + " -hide_banner -loglevel warning")

    else:
        print("Invalid complexity: please choose 2 (fast) or 3 (slow, more complicated output)")
    
    # make temporary .aac file to add to the mp4 video (.wav not supported directly)
    temp_audio_file = os.path.join(args.temp_path, args.song_name + "_temp.aac")
    os.system("ffmpeg -i " + args.music_file_path + " -ab 256k -hide_banner -loglevel warning " + temp_audio_file)

    # chromashift to add pizazz\
    temp_input_file = os.path.join(args.temp_path, args.song_name + "_generated.mp4")
    temp_output_file = os.path.join(args.temp_path, args.song_name + "_generated_final.mp4")
    print("Glitching final result")
    os.system("ffmpeg -i " + temp_input_file + " -vf chromashift=crv=-200:cbv=100:crh=100 " + temp_output_file +
              " -hide_banner -loglevel warning")

    # add audio
    print("Adding Audio")
    os.system("ffmpeg -i " + temp_output_file + " -i " + temp_audio_file + " -c copy -map 0:v:0 -map 1:a:0 " +
              args.out_path + " -hide_banner -loglevel warning")

    # file clean up
    print("deleting temporary files")
    for vid in os.listdir(args.temp_path):
        os.remove(os.path.join(args.temp_path, vid))
    
    end = time.time()
    print("Total program runtime, in seconds - " + str(end - start))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a music video - talent free!')
    parser.add_argument("-project_folder", help="Path to project folder with all directories it contains")
    parser.add_argument("--song_name", help="Song name (should be located in project_folder/music/)")
    parser.add_argument("--bpm", help="Song BPM (automatically detected if not filled in)")
    parser.add_argument("--complexity", default="3",
                        help="Complexity (2 OR 3), 2 for quicker and 3 for more intense visuals (3 by default)")
    parser.add_argument("--dynamic", default=True,
                        help="True for dynamic visuals based on song intensity, False for random visuals")
    parser.add_argument("--output", help="Output file prefix eg MyVideo")
    parser.add_argument("--output_res", default="1080", help="Output video resolution, 1080 or 720")
    args = parser.parse_args()

    # Defining additional necessary arguments
    args.project_folder = args.project_folder if args.project_folder else os.getcwd()
    args.song_name = args.song_name if args.song_name else os.listdir(os.path.join(args.project_folder, "music"))[0]
    args.music_file_path = str(os.path.join(args.project_folder, "music", args.song_name))
    args.out_path = str(os.path.join(args.project_folder, "out", args.output if args.output else args.song_name))
    args.temp_path = os.path.join(args.project_folder, "temp" + os.sep)
    args.titles_path = os.path.join(args.project_folder, "titles" + os.sep)
    args.videos_path = os.path.join(args.project_folder, "videos" + os.sep)
    args.bpm = str(generate_timestamps.guess_bpm(args.music_file_path)) if not args.bpm else args.bpm

    music_video_generator(args)

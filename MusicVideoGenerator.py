import os
import time
import argparse
import librosa

from numba import jit, cuda

# TODO:
# 1080p vs 720p option
# Choose videos to use based on tags
# different time signature support


@jit(target_backend='cuda')
def main(args):
    """
    Generates a Music Video based on a specific song by calling a few python files and movie editing command line tools

    Arguments:
    1. Song name (should be located in music/)
    2. Song BPM (optional)
    3. Complexity (2 OR 3), 2 for quicker and 3 for more intense visuals (3 by default)
    4. Output video resolution (1080p OR 720p, 1080p by default)

    """
    
    start = time.time()
    
    # Generates n(complexity) number of randomized videos
    if args.dynamic:
        os.system("python SmartVid.py " + args.song_name + " " + args.bpm + " " + args.complexity)
    else:
        os.system("python SimpleVid.py " + args.song_name + " " + args.bpm + " " + args.complexity)
    
    # makes all videos at the same resolution
    # makes all videos 720p
    print("making Subvideos " + args.output_res)
    for i in range(int(args.complexity)):
        if not os.path.exists("temp/small" + args.song_name + str(i)+".mp4"):
            print("resizing video" + str(i))
            width = args.output_res[:-1] * (16/9)
            height = args.output_res[:-1]
            os.system("ffmpeg -i temp/" + args.song_name + str(i) + 
                      ".mp4 -vf scale=" + width + ":" + height + "-crf 18 -preset medium temp/small" + args.song_name +
                      str(i) + ".mp4 -hide_banner -loglevel warning")
        else:
            print("Video" + str(i) + " is already 720p")

    # get output name
    if args.output:
        output_name = args.output
    else:
        output_name = args.song_name  # song name by default

    # Blends all videos
    if int(args.complexity) == 3:
        for i in range(int(args.complexity)-1):
            print("Blending videos together "+str(i+1))

            os.system("ffmpeg -i temp/small" + args.song_name + str(i)+".mp4 -i temp/small" + args.song_name + str(i+1)
                      + ".mp4 -filter_complex blend='difference' temp/output" + args.song_name+str(i) +
                      ".mp4 -hide_banner -loglevel warning")
        
        print("Mashing those blended videos together")
        os.system("ffmpeg -i temp/output" + args.song_name + "0.mp4 -i temp/output" + args.song_name + 
                  "1.mp4 -filter_complex blend='difference' temp/" + args.song_name + 
                  "GeneratedMusicVideo.mp4 -hide_banner -loglevel warning")

    elif int(args.complexity) == 2:
        print("Blending")
        for i in range(int(args.complexity)-1):
            os.system("ffmpeg -i temp/small" + args.song_name + str(i) + ".mp4 -i temp/small" + args.song_name + 
                      str(i + 1) + ".mp4 -filter_complex blend='difference' temp/" + args.song_name + 
                      "GeneratedMusicVideo.mp4 -hide_banner -loglevel warning")

    else:
        print("Invalid complexity: please choose 2 (fast) or 3 (slow, more complicated output)")
    
    # make temporary .aac file to add to the mp4 video (.wav not supported directly)
    os.system("ffmpeg -i music/" + args.song_name + " -ab 256k -hide_banner -loglevel warning temp/tempAudio.aac")

    # chromashift to add pizazz\
    print("Glitching final result")
    os.system("ffmpeg -i temp/" + args.song_name + 
              "GeneratedMusicVideo.mp4 -vf chromashift=crv=-200:cbv=100:crh=100 temp/" + args.song_name + 
              "GeneratedMusicVideoFinal.mp4 -hide_banner -loglevel warning")

    # add audio
    print("Adding Audio")
    os.system("ffmpeg -i temp/" + args.song_name + 
              "GeneratedMusicVideoFinal.mp4 -i temp/tempAudio.aac -c copy -map 0:v:0 -map 1:a:0 out/" + output_name + 
              ".mp4 -hide_banner -loglevel warning")

    # file clean up
    print("deleting temporary files")
    for vid in os.listdir("temp/"):
        os.remove("temp/" + vid)
    
    end = time.time()
    print("total program runtime, in seconds - " + str(end - start))


# Estimate BPM
def estimate_tempo(audio_path):
    print('Estimating tempo of {}'.format(audio_path))
    y, sr = librosa.load(audio_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
    print('Estimated tempo of {}'.format(audio_path) + ' = ' + str(tempo[0]))
    return tempo[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate a music video - talent free!')
    parser.add_argument("-song_name", help="Song name (should be located in music/) i.e Music1.wav")
    parser.add_argument("--bpm", help="Song BPM")
    parser.add_argument("--complexity", help="Complexity (2 OR 3), 2 for quicker and 3 for more intense visuals (3 by default)", default="3")
    parser.add_argument("--dynamic", help="True for dynamic visals which respond to song intensity, False for random visuals", default=True)
    parser.add_argument("--output", help="Output file prefix eg MyVideo")
    parser.add_argument("--output_res", help="Output video resolution, 1080p or 720p", default="1080p")
    args = parser.parse_args()

    if not args.bpm:
        args.bpm = str(estimate_tempo(os.path.join("music/" + args.song_name)))

    main(args)

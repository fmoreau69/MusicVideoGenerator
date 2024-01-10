import os
import math
import requests
import logging as log
from tqdm import tqdm

import pixabay.core
from pexelsapi.pexels import Pexels

# TODO:
# Import api_keys from text file => Done
# Add coverr.co: https://api.coverr.co/docs/
# free video footage, SplitShire Videos, Clipstill, Videezy, lifeofvids

# Get API_KEYS
f = open("api_keys.txt", "r")
pixabay_api_key = f.readline().replace('\n', '')
pexels_api_key = f.readline().replace('\n', '')

# Init parameters
queries = ['ocean', 'boat', 'mariners', 'old ship', 'sailors', 'sea']
output_dir = 'G:\\BANQUES_VIDEOS'
args = {
    'global': {'size': 'large', 'ratio': 16 / 9, 'minWidth': 1920, 'minHeight': 1080,
               'per_page': 100, 'video_nb': 20, 'ratio_strict': 1, 'keep_all': 0, 'sub_folders': True},
    'pixabay': {'use_api': 1, 'px': pixabay.core(pixabay_api_key),
                'lang': 'en', 'orientation': 'horizontal', 'colors': 'all'},
    'pexels': {'use_api': 1, 'px': Pexels(pexels_api_key),
               'lang': 'en-US', 'orientation': 'landscape', 'colors': ''}
}


def video_downloader(queries: list, output_dir: str, args: dict):
    global_args = args['global']
    # Loop on queries
    for query in queries:
        file_destination = os.path.join(output_dir, "".join(ch for ch in query if ch.isalnum())) \
            if global_args['sub_folders'] else output_dir
        os.makedirs(file_destination, exist_ok=True)
        # Loop on sources
        for key in args:
            if key != 'global' and args[key]['use_api']:
                videos = get_video_list(query, key, args[key], global_args)
                video_counter = min(math.ceil(global_args['video_nb']/(len(args)-1)), len(videos))
                progress_bar = tqdm(total=video_counter, position=0, leave=True,
                                    desc=f"{key} video download progress for query '{query}'")
                # Loop on videos
                for vid in videos:
                    progress_bar.update(1)
                    filename = f"{vid['id']}.mp4" if isinstance(vid, dict) else f"{vid.getId()}.mp4"
                    file_path = os.path.join(file_destination, filename)
                    if video_counter == 0:
                        log.info(f"All requested {key} video downloaded!")
                        break
                    elif os.path.exists(file_path):
                        log.info(f"Video file '{filename }' has already been downloaded")
                        video_counter -= 1
                        continue
                    else:
                        w = vid['width'] if key != 'pixabay' else next(iter(vid._raw_data['videos'].values()))['width']
                        h = vid['height'] if key != 'pixabay' else next(iter(vid._raw_data['videos'].values()))['height']
                        if global_args['ratio_strict'] and w/h == global_args['ratio'] or global_args['keep_all']:
                            log.info(f"Downloading video file: {filename}")
                            download_video(vid, key, file_path, global_args)
                            video_counter -= 1


def get_video_list(query, key, args, global_args):
    videos = []
    if key == 'pixabay':
        videos = args['px'].queryVideo(query=query, lang=args['lang'], orientation=args['orientation'],
                                       minWidth=global_args['minWidth'], minHeight=global_args['minHeight'],
                                       colors=args['colors'], perPage=global_args['per_page'])
    elif key == 'pexels':
        videos = args['px'].search_videos(query=query, locale=args['lang'], orientation=args['orientation'],
                                          size=global_args['size'],
                                          color=args['colors'], page=1, per_page=global_args['per_page'])['videos']
    return videos


def download_video(vid, key, file_path, global_args):
    if key == 'pixabay' and vid.getVideoLarge():
        vid.download(file_path, global_args['size'])
    elif key == 'pixabay' and vid.getVideoMedium():
        vid.download(file_path, 'medium')
    elif key == 'pexels':
        for elem in vid['video_files']:
            if elem['height'] == vid['height']:
                download_from_url(elem['link'], file_path)
                break


def download_from_url(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)


if __name__ == "__main__":
    video_downloader(queries, output_dir, args)

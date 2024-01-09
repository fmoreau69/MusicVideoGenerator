import os
import requests
from tqdm import tqdm

import pixabay.core
from pexelsapi.pexels import Pexels

# TODO:
# Add coverr.co: https://api.coverr.co/docs/
# free video footage, SplitShire Videos, Clipstill, Videezy, lifeofvids


# Init parameters
queries = ['ocean', 'boat', 'mariners', 'old ship', 'sailors', 'sea']
output_dir = 'G:\BANQUES_VIDEOS'
args = {
    'global': {'size': 'large', 'ratio': 16 / 9, 'minWidth': 1920, 'minHeight': 1080,
               'per_page': 100, 'video_nb': 20, 'ratio_strict': 1, 'keep_all': 0},
    'pixabay': {'use_api': 1, 'px': pixabay.core('41014354-df28462b05ba0f555a30ac65a'),
                'lang': 'en', 'orientation': 'horizontal', 'colors': 'all'},
    'pexels': {'use_api': 1, 'px': Pexels('f7H8h2PvP6H2CZgByxRqbGCsY8kTMsdr8mPlBzwTqcNOX5mSiWngfGkz'),
               'lang': 'en-US', 'orientation': 'landscape', 'colors': ''}
}


def video_downloader(queries: list, output_dir: str, args: dict):
    global_args = args['global']
    # Loop on queries
    for query in queries:
        file_destination = os.path.join(output_dir, "".join(ch for ch in query if ch.isalnum()))
        os.makedirs(file_destination, exist_ok=True)
        # Loop on sources
        for key in args:
            if key != 'global' and args[key]['use_api']:
                videos = get_video_list(query, key, args[key], global_args)
                video_counter = min(global_args['video_nb'], len(videos))
                progress_bar = tqdm(total=video_counter, position=0, leave=True,
                                    desc=key + ' video download progress for query "' + query + '"')
                # Loop on videos
                for vid in videos:
                    video_counter -= 1
                    progress_bar.update(1)
                    filename = str(vid['id']) + '.mp4' if isinstance(vid, dict) else str(vid.getId()) + '.mp4'
                    file_path = os.path.join(file_destination, filename)
                    if video_counter == 0:
                        print('All requested ' + key + ' video downloaded!')
                        break
                    elif os.path.exists(file_path):
                        print('Video file "' + filename + '" has already been downloaded')
                        continue
                    else:
                        w = vid['width'] if key != 'pixabay' else next(iter(vid._raw_data['videos'].values()))['width']
                        h = vid['height'] if key != 'pixabay' else next(iter(vid._raw_data['videos'].values()))['height']
                        if global_args['ratio_strict'] and w/h == global_args['ratio'] or global_args['keep_all']:
                            # print('Downloading video file: ' + filename)
                            download_video(vid, key, file_path, global_args)
                        else:
                            video_counter += 1


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

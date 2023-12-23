import os
import requests
from tqdm import tqdm

import pixabay.core
from pexelsapi.pexels import Pexels


def download_from_url(url, filename):
    response = requests.get(url)
    with open(filename, "wb") as f:
        f.write(response.content)


# init variables
source = ['pixabay', 'pexels']  #, 'pexels'
query = 'rain'
video_nb = 100
video_size = 'large'
output_dir = 'G:\BANQUES_VIDEOS'

# pixabay video downloader
if 'pixabay' in source:
    file_destination = os.path.join(output_dir, 'pixabay', "".join(ch for ch in query if ch.isalnum()))
    os.makedirs(file_destination, exist_ok=True)
    px = pixabay.core("41014354-df28462b05ba0f555a30ac65a")
    videos = px.queryVideo(query)
    video_counter = min(video_nb, len(videos))
    progress_bar_pixabay = tqdm(total=video_counter, desc='Video download progress')
    for vid in videos:
        if video_counter == 0:
            print('All requested pixabay video downloaded!')
            break
        else:
            video_counter -= 1
            filename = str(vid.getId()) + '.mp4'
            progress_bar_pixabay.update(1)
            if os.path.exists(os.path.join(file_destination, filename)):
                print('Video file "' + filename + '" has already been downloaded')
                continue
            else:
                print('downloading video file: ' + filename)
                if vid.getVideoLarge():
                    vid.download(os.path.join(file_destination, filename), video_size)
                elif vid.getVideoMedium():
                    vid.download(os.path.join(file_destination, filename), 'medium')


# pexels video downloader
if 'pexels' in source:
    file_destination = os.path.join(output_dir, 'pexels', query)
    os.makedirs(file_destination, exist_ok=True)
    pexels = Pexels('f7H8h2PvP6H2CZgByxRqbGCsY8kTMsdr8mPlBzwTqcNOX5mSiWngfGkz')
    videos = pexels.search_videos(query=query, orientation='', size='', color='', locale='', page=1, per_page=1000)
    video_counter = min(video_nb, len(videos['videos']))
    progress_bar_pexels = tqdm(total=video_counter, desc='Video download progress')
    for vid in videos['videos']:
        if video_counter == 0:
            print('All requested pixabay video downloaded!')
            break
        else:
            video_counter -= 1
            filename = str(vid['id']) + '.mp4'
            progress_bar_pexels.update(1)
            if os.path.exists(os.path.join(file_destination, filename)):
                print('Video file "' + filename + '" has already been downloaded')
                continue
            else:
                print('downloading video file: ' + filename)
                height = vid['height']
                video_files = vid['video_files']
                url = None
                for elem in video_files:
                    if elem['height'] == height:
                        url = elem['link']
                        download_from_url(url, os.path.join(file_destination, filename))
                        break

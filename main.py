import argparse
import yt_dlp
import os
from mutagen.easyid3 import EasyID3

from helper import rmDirRec

URLS_JSON = []
with open('urls.json', 'r') as f:
    import json
    data = json.load(f)
    for item in data:
        URLS_JSON.append({
            'name': item['name'],
            'url': item['url'],
            'ignore': item.get('ignore', False),
            'overwriteTitle': item.get('overwriteTitle', False),
        })


class TrackNumberPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        trackNumber = info['n_entries'] - info['playlist_index'] + 1

        metatag = EasyID3(info['filepath'])
        metatag['tracknumber'] = str(trackNumber)
        metatag.save()
        return [], info


# read in data_path from passed arguments
parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str)
parser.add_argument('--internal_path', type=str, default='.internal')
parser.add_argument('--temp_path', type=str, default='temp')
args = parser.parse_args()

if not args.path:
    print('No path passed! Pass a path with --path')
    exit()

config = {
    'internal_path': args.internal_path,
    'data_path': args.path,
    'temp_path': args.temp_path,
}

isExist = os.path.exists(config['internal_path'])
if not isExist:
    os.makedirs(config['internal_path'])

isExist = os.path.exists(config['data_path'])
if not isExist:
    os.makedirs(config['data_path'])

ydl_opts_default = {
    # If you want to keep the video file, set this to True
    'keepvideo': False,

    'format': 'bestaudio/best',
    'ignoreerrors': True,
    'postprocessors': [
        {  # Extract audio using ffmpeg
            'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3',
        }, {  # Embed metadata in audio using ffmpeg
            'key': 'FFmpegMetadata', 'add_metadata': True,
        }
    ],
    'paths': {
        'temp': config['temp_path'],
        'home': config['data_path'],
    },
}

with yt_dlp.YoutubeDL(ydl_opts_default) as ydl_playlist:

    for URL in URLS_JSON:
        if URL['ignore']:
            continue

        playlistInfo = ydl_playlist.extract_info(
            URL['url'], download=False, process=False)

        title = URL['name'] if URL['overwriteTitle'] else playlistInfo['title'].lower()

        ydl_opts = ydl_opts_default.copy()
        ydl_opts['outtmpl'] = title + \
            '/%(n_entries-playlist_index+1)04d %(title)s [%(id)s].%(ext)s'
        ydl_opts['download_archive'] = config['internal_path'] + \
            '/ARCHIVE_' + title.upper() + '.txt'
        ydl_opts['postprocessor_args'] = {
            'metadata': ['-metadata', 'album=' + title],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(TrackNumberPP(), when='post_process')
            ydl.download(URL['url'])

# Clean up temp folder
rmDirRec(config['data_path'] + '/' + config['temp_path'])

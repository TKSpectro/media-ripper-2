import yt_dlp
import os
from mutagen.easyid3 import EasyID3

from helper import rmDirRec

# parse urls from urls.txt (one url per line)
# if the url starts with #, it will be ignored
# urls can have comment appended with ## remove that
URLS = []
with open('urls.txt', 'r') as f:
    for line in f:
        if line.startswith('#'):
            continue
        if '##' in line:
            line = line[:line.index('##')]
        URLS.append(line.strip())


class TrackNumberPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        trackNumber = info['playlist_count'] - info['playlist_index'] + 1

        metatag = EasyID3(info['filepath'])
        metatag['tracknumber'] = str(trackNumber)
        metatag.save()
        return [], info


config = {
    'internal_path': 'internal',
    'data_path': 'data',
    'temp_path': 'temp',
}

isExist = os.path.exists(config['internal_path'])
if not isExist:
    os.makedirs(config['internal_path'])

isExist = os.path.exists(config['data_path'])
if not isExist:
    os.makedirs(config['data_path'])

ydl_opts_default = {
    'format': 'bestaudio/best',
    'keepvideo': False,
    'playlistend': 2,
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
    # 'verbose': True,
}

with yt_dlp.YoutubeDL(ydl_opts_default) as ydl_playlist:

    for URL in URLS:
        playlistInfo = ydl_playlist.extract_info(
            URL, download=False, process=False)

        title = playlistInfo['title'].upper()

        ydl_opts = ydl_opts_default.copy()
        ydl_opts['outtmpl'] = title + \
            '/%(playlist_count-playlist_index+1)04d %(title)s [%(id)s].%(ext)s'
        ydl_opts['download_archive'] = 'internal/ARCHIVE_' + title + '.txt'
        ydl_opts['postprocessor_args'] = {
            'metadata': ['-metadata', 'album=' + title],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(TrackNumberPP(), when='post_process')
            ydl.download(URL)

# Clean up temp folder
rmDirRec(config['data_path'] + '/' + config['temp_path'])

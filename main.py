import argparse
import yt_dlp
import os
from mutagen.easyid3 import EasyID3

URLS_JSON = []
with open(os.path.join(os.getcwd(), "urls.json"), "r") as f:
    import json

    data = json.load(f)
    for item in data:
        URLS_JSON.append(
            {
                "name": item["name"],
                "url": item["url"],
                "ignore": item.get("ignore", False),
                "overwriteTitle": item.get("overwriteTitle", False),
            }
        )


class TrackNumberPP(yt_dlp.postprocessor.PostProcessor):
    def run(self, info):
        trackNumber = info["n_entries"] - info["playlist_index"] + 1

        metatag = EasyID3(info["filepath"])
        metatag["tracknumber"] = str(trackNumber)
        metatag.save()
        return [], info


# read in data_path from passed arguments
parser = argparse.ArgumentParser()
parser.add_argument("--path", type=str)
parser.add_argument("--internal_path", type=str, default=".internal")
parser.add_argument("--temp_path", type=str, default=os.path.join(os.getcwd(), ".temp"))
parser.add_argument("--quiet", type=bool, default=False)
args = parser.parse_args()

if not args.path:
    print("No path passed! Pass a path with --path")
    exit()

config = {
    "internal_path": args.internal_path,
    "data_path": args.path,
    "temp_path": args.temp_path,
}

if not os.path.exists(config["internal_path"]):
    os.makedirs(config["internal_path"])
if not os.path.exists(config["data_path"]):
    os.makedirs(config["data_path"])
if not os.path.exists(config["temp_path"]):
    os.makedirs(config["temp_path"])

ydl_opts_default = {
    # If you want to keep the video file, set this to True
    "keepvideo": False,
    # Only print warnings and errors
    "quiet": args.quiet,
    # Download the best quality audio https://github.com/yt-dlp/yt-dlp#format-selection-examples
    "format": "bestaudio/best",
    # Don't stop on error (happens when video is private/deleted)
    "ignoreerrors": True,
    "postprocessors": [
        {  # Extract audio using ffmpeg
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
        },
        {  # Embed metadata in audio using ffmpeg
            "key": "FFmpegMetadata",
            "add_metadata": True,
        },
    ],
    "paths": {
        "temp": config["temp_path"],
        "home": config["data_path"],
    },
}

with yt_dlp.YoutubeDL(ydl_opts_default) as ydl_playlist:
    for URL in URLS_JSON:
        if URL["ignore"]:
            continue

        playlistInfo = ydl_playlist.extract_info(URL["url"], download=False, process=False)

        playlistName = URL["name"] if URL["overwriteTitle"] else playlistInfo["title"].lower()

        ydl_opts = ydl_opts_default.copy()
        ydl_opts["outtmpl"] = playlistName + "/%(n_entries-playlist_index+1)04d %(title)s [%(id)s].%(ext)s"
        ydl_opts["download_archive"] = config["internal_path"] + "/ARCHIVE_" + playlistName.upper() + ".txt"
        ydl_opts["postprocessor_args"] = {
            "metadata": ["-metadata", "album=" + playlistName],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.add_post_processor(TrackNumberPP(), when="post_process")
            ydl.download(URL["url"])

exit()

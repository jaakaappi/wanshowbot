import json
import sys

import yt_dlp
from yt_dlp import YoutubeDL
from yt_dlp.utils import write_json_file


def get_shows():
    ydl_opts = {
        'quiet': True,  # Suppress output to console
        'skip_download': True,  # Do not download the video
        'extract_flat': True,  # Extract metadata only
        "playlistend": 5
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info("https://www.youtube.com/playlist?list=PL8mG-RkN2uTw7PhlnAr4pZZz2QubIbujH",
                                     download=False)
        return info_dict


def get_episode(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': './output/%(id)s.%(ext)s'
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        get_episode(sys.argv[1])
    else:
        info_dict = get_shows()
        with open("output.json", "w+") as output:
            output.write(json.dumps(info_dict, indent=4))

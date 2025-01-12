import sys
from pathlib import Path

from pydub import AudioSegment


def match_target_amplitude(file: str):
    print(f"Opening file {file}")
    track = AudioSegment.from_file(Path("./output") / Path(file))
    change_in_dBFS = -20.0 - track.dBFS
    print(f"Normalizing track")
    normalized_sound = track.apply_gain(change_in_dBFS)
    print(f"Exporting track")
    normalized_sound.export(f"./output/{file.split('.')[0]}.mp3", format="mp3")


if "__main__" == __name__:
    if len(sys.argv) > 1:
        match_target_amplitude(sys.argv[1])
    else:
        print("Usage: audio.py <file>")

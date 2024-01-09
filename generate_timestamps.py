import os
import sys
import csv
import librosa

from tinytag import TinyTag
from scipy.io.wavfile import read


def get_duration(music_file_path: str):
    """
    reads song metadata ard returns duration
    """

    return TinyTag.get(music_file_path).duration


def guess_first_and_last_down_beat(music_file_path: str):
    """
    Reads a .wav audio file (str) and guesses the timestamp of first and last downbeats (float,float) in seconds
    """

    fs, data = read(music_file_path)
    data = data[:, 0]  # one stereo channel for ease
    highest_db = max(data)
    count, count2 = 0, 0

    # find first downbeat
    for count, point in enumerate(data):
        if point >= (highest_db / 1.5):  # > 0 to avoid noise / ambience
            break

    # find last downbeat
    for count2, point in enumerate(data[::-1]):
        if point >= (highest_db / 1.5):  # > 0 to avoid noise / ambience
            break

    duration = get_duration(music_file_path)

    return (count / len(data)) * duration, ((len(data) - count2) / len(data)) * duration


def get_timestamps(music_file_path: str, bpm: float):
    """
    Returns a list [float, float, ...] of the timestamps of all the 4 bar regions in the song

    Parameters:
    - bpm (the tempo (beats per minute) of the song)
    """

    # estimated guess of first and last beat in song
    start, finish = guess_first_and_last_down_beat(music_file_path)
    length_of_a_beat = 1 / (bpm / 60)
    timestamps = [start]

    while start < finish:
        timestamps.append(start + length_of_a_beat * 16)
        start += length_of_a_beat * 16

    return timestamps


def get_counts_in_4_bars(music_file_path: str, bpm: float):
    """
    returns the number of data points in 4 bars of a file for downstream works
    """

    fs, data = read(music_file_path)
    data = data[:, 0]  # one stereo channel for ease

    length = len(data)
    duration = get_duration(music_file_path)

    length_of_a_beat = 1 / (bpm / 60)
    length_of_16_beats = length_of_a_beat * 16  # 4 bars

    # find how many counts in 16 beats
    for count, point in enumerate(data):
        if count / length >= length_of_16_beats / duration:
            return count


def get_intensities(music_file_path: str, bpm: float):
    """
    Returns {4barCount(int):intensity(str)} for each 4 bar segment in the given .wav file

    Intensities = "Low","Medium","High
    """

    duration = get_duration(music_file_path)
    start, finish = guess_first_and_last_down_beat(music_file_path)
    counts_in_4_bars = get_counts_in_4_bars(music_file_path, bpm)

    intensities = {}

    # analyse waveform
    fs, data = read(music_file_path)

    # one stereo channel for ease
    data = data[:, 0]

    length = len(data)

    count_ = 0
    sum_ = float(0)
    bar_block = 0  # current index of 4 bar block

    for count, point in enumerate(data):
        if start / duration <= count / length <= finish / duration:  # only calculate between first and last downbeat

            count_ += 1
            sum_ += float(abs(point))  # absolute value because deviation from 0 (no volume) is what is important

            if sum_ < 0:
                sys.exit()

            # calculate and save average every 4 bars
            if count_ >= counts_in_4_bars:
                intensities[bar_block] = sum_ / count_

                count_ = 0
                sum_ = float(0)
                bar_block += 1

    max_average_value = max(intensities.values())

    # all intensities are relative to one another
    for key in intensities.keys():
        if intensities[key] > 0.96 * max_average_value:
            intensities[key] = "High"
        elif intensities[key] > 0.65 * max_average_value:
            intensities[key] = "Medium"
        else:
            intensities[key] = "Low"

    return intensities


def save_intensities(music_file_path: str, intensities: dict):
    """
    Saves intensities from get_intensities(filename, bpm) as .csv
    """

    ordered = []
    for key in intensities.keys():
        ordered.append((key, intensities[key]))

    ordered = sorted(ordered)

    with open("analysis/" + str(music_file_path) + ".csv", "w", newline='') as file:
        fieldnames = ["Section", "Intensity"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()

        for t in ordered:
            writer.writerow({'Section': t[0], 'Intensity': t[1]})

        file.close()


def guess_bpm(music_file_path: str):
    """
    Reads a .wav file and returns an estimate of the bpm, If bpm is known it should be entered manually for best results
    """

    y, sr = librosa.load(music_file_path)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    tempo = round(librosa.feature.tempo(onset_envelope=onset_env, sr=sr)[0], 1)
    print('Estimated tempo of "{}"'.format(str(music_file_path.split(os.sep)[-1])) + ' = ' + str(tempo))
    return tempo


def main(argv):
    """
    stores intensities to file
    """

    music_file_path = argv[0]
    bpm = argv[1]
    save_intensities(music_file_path, get_intensities(music_file_path, bpm))


if __name__ == "__main__":
    main(sys.argv[1:])

from pathlib import Path
import sys
import os
import numpy as np
import soundfile as sf
import math
import wave

DIRECTORY_PATH = os.getcwd()

# for our data
EXPECTED_SAMPLE_RATE = 384000 
FOLDER = "our_audio"

# for paper data
# EXPECTED_SAMPLE_RATE = 500000 
# FOLDER = "paper_audio"
# ---------------------------------------------

def get_peak_information_of(sample_rate, data):
    if sample_rate != EXPECTED_SAMPLE_RATE:
        print(f"Warning: Expected sample rate {EXPECTED_SAMPLE_RATE} Hz, yet file sample rate is {sample_rate} Hz.")
        return

    # If the audio is stereo, convert to mono by using only the first channel.
    if data.ndim > 1:
        data = data[:, 0]

    # Convert data to float (for safety) and compute the absolute amplitude.
    data = data.astype(np.float64)
    abs_data = np.abs(data)

    # Find the index of the maximum amplitude (the intensity peak).
    peak_index = np.argmax(abs_data)
    peak_amplitude = abs_data[peak_index]  # this is the intensity value

    # calculate the timestamp of the peak
    peak_time_sec = peak_index / sample_rate
    peak_time_ms = peak_time_sec * 1000

    # extract peak from data with some radius
    window_radius_in_samples = 50
    start_index = max(0, peak_index - window_radius_in_samples)
    end_index = min(len(data), peak_index + window_radius_in_samples)
    segment = data[start_index:end_index]

    # Apply a Hanning window to the segment to reduce spectral leakage.
    window = np.hanning(len(segment))
    segment_windowed = segment * window

    # apply fft
    fft_result = np.fft.rfft(segment_windowed)
    magnitude = np.abs(fft_result)
    
    # (Note: frequency resolution = sample_rate / N)
    freq_axis = np.fft.rfftfreq(len(segment), d=1.0/sample_rate)

    dominant_freq_bin_index = np.argmax(magnitude)
    dominant_freq_bin = freq_axis[dominant_freq_bin_index]

    # Output the results.
    print("Intensity Peak Information:")
    print(f"  Timestamp of peak       : {peak_time_ms:.3f} ms")
    print(f"  Peak Intensity          : {peak_amplitude}")
    print(f"  Dominant Frequency Bin  : {dominant_freq_bin:.2f} Hz")


# how to compute audio file length - V1
# Quelle: https://www.geeksforgeeks.org/python/how-to-get-the-duration-of-audio-in-python/
def output_duration(data, sample_rate):
    length = int(len(data) / sample_rate)
    hours = length // 3600  # calculate in hours
    length %= 3600
    mins = length // 60  # calculate in minutes
    length %= 60
    seconds = length  # calculate in seconds

    return hours, mins, seconds


# how to compute audio file length - V2
# Quelle: https://www.tutorialspoint.com/how-to-get-the-duration-of-audio-in-python
def get_duration_wave(file_path):
   with wave.open(str(file_path), 'r') as audio_file:
      frame_rate = audio_file.getframerate()
      n_frames = audio_file.getnframes()
      duration = n_frames / float(frame_rate)
      return duration


def cut_to_5_minute_segments(filename):
    print('-----------NEW SEGMENT----------------')
    base_dir = Path(__file__).resolve().parent
    file_path = base_dir / FOLDER / filename
    info = sf.info(file_path)

    total_frames = info.frames
    sample_rate = info.samplerate
    
    # .. duration (in seconds and minutes) calculated with information of WAV header
    duration_sec = total_frames / sample_rate
    wav_header_duration = duration_sec / 60
    round_wav_header_duration = float("{:.2f}".format(wav_header_duration))
    print(f"Calculated audio duration: {round_wav_header_duration} minutes")
    
    # only to compute length of wav-file
    
    # Quelle: https://www.omnicalculator.com/other/audio-file-size#audio-file-size-calculation-formula-and-how-to-calculate-audio-file-sizes
    # based on formula: audio file size = bit depth * sample rate * duration of audio * number of channels
    file_size = os.path.getsize(file_path)
    bytes_per_sample = 4 # because subtype 32-PCM > bit_depth: 32 > convert to bytes > 4
    actual_audio_duration = file_size / (info.channels * bytes_per_sample * info.samplerate) / 60
    round_actual_audio_duration = float("{:.2f}".format(actual_audio_duration))
    print(f"Actual audio duration: {round_actual_audio_duration} minutes")
    
    if round_actual_audio_duration != round_wav_header_duration:
        print(f"Warning about broken WAV header: Expected minutes {round_actual_audio_duration} minutes, yet file duration has {round_wav_header_duration} minutes.")
        return
    
    block_size = 5 * 60 * sample_rate  # 5 minutes in samples
    output_dir = Path(__file__).parent / "segmente" / f"segments_${filename}"
    output_dir.mkdir(exist_ok=True)
    
    data, _ = sf.read(file_path, dtype='float32', always_2d=False)
    num_segments = math.ceil(len(data) / block_size)
    for i in range(num_segments):
        start = i * block_size
        end = min((i + 1) * block_size, len(data))
        segment_data = data[start:end]
        segment_path = output_dir / f"segment_{i+1:03d}.wav"
        sf.write(segment_path, segment_data, sample_rate)
        print(f"Saved: {segment_path}")

    for segment_file in sorted(output_dir.glob("*.wav")):
        segment_data, sr = sf.read(segment_file, dtype='float32', always_2d=False)
        duration_min = len(segment_data) / sr / 60
        print(f"---- Lese Segment: {segment_file.name}, Dauer: {duration_min:.2f} Minuten ---")
        get_peak_information_of(sr, segment_data)


if __name__ == '__main__':  
    try:    
        for filename in os.listdir(FOLDER):
            if not filename.endswith(".wav"):
                continue
            cut_to_5_minute_segments(filename)
    except Exception as e:
        print("Error reading WAV file:", e)
        sys.exit(1)

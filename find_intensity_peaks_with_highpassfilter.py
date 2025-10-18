import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, filtfilt, find_peaks
import sys
import matplotlib.pyplot as plt

# paper data
specific_audio_file = "paper_audio/id_10_sound_1.wav"
expected_sample_rate = 500000 # for paper data

# our data
# expected_sample_rate = 384000 # for our data
# specific_audio_file = "our_audio/10-cm-status-ok-384khz.wav"

# High-pass filter parameters:
hp_cutoff_frequency = 20000          # High-pass cutoff frequency = 20 kHz
hp_filter_order = 5        # Order of the Butterworth filter

# Threshold percentage (original paper said: "We filtered the recordings using 20 kHz high-pass filter. A recording was saved only if triggered with a sound which exceeded 2% of the maximum dynamic range of the microphone.")
threshold_percent = 0.02


# ---------------------------------------------


def apply_highpass_filter_on(audiosamples, cutoff_frequency, sampling_frequency, filter_order=5):
    nyquist = sampling_frequency / 2.0
    normalized_cutoff = cutoff_frequency / nyquist
    b, a = butter(filter_order, normalized_cutoff, btype='high', analog=False)
    filtered_data = filtfilt(b, a, audiosamples)
    return filtered_data


def main():
    try:
        sample_rate, data = wavfile.read(specific_audio_file)
            
        # Alert if the file's sample rate does not match the expected one.
        if sample_rate != expected_sample_rate:
            print(f"Warning: Expected sample rate {expected_sample_rate} Hz but file sample rate is {sample_rate} Hz.")

        # Convert to mono  (if it isn't already)
        if data.ndim > 1:
            data = data[:, 0]

        # Convert the audio data to float (if it isn't already)
        data = data.astype(np.float64)

        filtered_data = apply_highpass_filter_on(data, hp_cutoff_frequency, sample_rate, filter_order=hp_filter_order)

        # Compute the absolute amplitude of the filtered signal.
        abs_filtered = np.abs(filtered_data)

        threshold_value = threshold_percent * np.max(abs_filtered)
        print(f"High-pass Filtered Signal Threshold = {threshold_value:.3f} (2% of maximum)")

        peaks, _properties = find_peaks(abs_filtered, height=threshold_value)

        if peaks.size == 0:
            print("No intensity peaks found above the threshold.")
            sys.exit(0)

        print("\nDetected Intensity Peaks:")
        for idx, p in enumerate(peaks, start=1):
            peak_time_sec = p / sample_rate
            peak_time_ms = peak_time_sec * 1000
            intensity = abs_filtered[p]
            print(f"Peak {idx}: Timestamp = {peak_time_ms:.3f} ms, Intensity = {intensity:.3f}")

        time_axis = np.arange(len(data)) / sample_rate  # seconds

        plt.figure(figsize=(12, 6))
        plt.plot(time_axis, abs_filtered, label="Filtered Absolute Amplitude")
        plt.plot(time_axis[peaks], abs_filtered[peaks], "rx", markersize=8, label="Detected Peaks")
        plt.axhline(y=threshold_value, color='gray', linestyle='--', label="Threshold")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.title("Intensity Peak Detection after 20 kHz High-Pass Filter")
        plt.legend()
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print("Error reading WAV file:", e)
        sys.exit(1)


if __name__ == '__main__':
    main()

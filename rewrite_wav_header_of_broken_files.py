import os
import struct
import shutil
from pathlib import Path

FOLDER = "our_audio"
OUTPUT_DIRECTORY = "our_audio/fixed_header/"

def fix_wav_header(filepath: Path, output_folder: Path):
    # Make sure output folder exists
    output_folder.mkdir(parents=True, exist_ok=True)

    # Copy original file to output folder
    fixed_path = output_folder / filepath.name
    shutil.copy2(filepath, fixed_path)

    filesize = os.path.getsize(fixed_path)
    chunk_size = filesize - 8
    subchunk2_size = filesize - 44

    with open(fixed_path, "r+b") as f:
        # Fix ChunkSize (offset 4)
        f.seek(4)
        f.write(struct.pack("<I", chunk_size))

        # Fix Subchunk2Size (offset 40)
        f.seek(40)
        f.write(struct.pack("<I", subchunk2_size))

    print(f"[OK] Fixed {filepath.name} -> {fixed_path} | ChunkSize={chunk_size}, Subchunk2Size={subchunk2_size}")


def batch_fix_wav_headers(folder: str):
    folder_path = Path(folder)
    if not folder_path.exists():
        print(f"Folder {folder} not found.")
        return

    wav_files = list(folder_path.glob("*.wav"))
    if not wav_files:
        print(f"No WAV files found in {folder}.")
        return

    print(f"Found {len(wav_files)} WAV file(s). Saving fixed copies to: {OUTPUT_DIRECTORY}\n")

    for wav_file in wav_files:
        try:
            fix_wav_header(wav_file, Path(OUTPUT_DIRECTORY))
        except KeyboardInterrupt:
            exit
        except Exception as e:
            print(f"[ERR] Could not fix {wav_file.name}: {e}")
            file_path = Path(OUTPUT_DIRECTORY) / wav_file.name
            print(f"{file_path}")
            if file_path.exists():
                file_path.unlink()



if __name__ == "__main__":
    batch_fix_wav_headers(FOLDER)


# RESULT: WAV-FILES bigger than 4GB, which standard wav headers cannot represent
# BECAUSE OF THAT: wav-files header truncated
# For files larger than 4 GB, you need RF64 (RIFF64) or WAVE64 format
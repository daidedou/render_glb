import os
import re
import subprocess
from PIL import Image
from rembg import remove, new_session


def remove_background(folder, out_folder=None, model="isnet-general-use"):
    """
    Remove background from PNG images.

    Parameters
    ----------
    folder : str
        Input folder containing PNG images
    out_folder : str | None
        If None → overwrite images in place
        If provided → save processed images into this folder
    model : str
        rembg model (default: best 'isnet-general-use')
    """

    if out_folder is not None:
        os.makedirs(out_folder, exist_ok=True)

    session = new_session(model)

    for file in sorted(os.listdir(folder)):
        if not file.lower().endswith(".png"):
            continue

        in_path = os.path.join(folder, file)
        out_path = in_path if out_folder is None else os.path.join(out_folder, file)

        try:
            img = Image.open(in_path).convert("RGBA")
            result = remove(img, session=session)
            result.save(out_path)

            print(f"Processed {file}")

        except Exception as e:
            print(f"Failed {file}: {e}")


def compile_video_from_folder(folder, output="output.mp4", fps=24):
    """
    Detect PNG sequence pattern automatically and compile a video with ffmpeg.
    """

    files = sorted(f for f in os.listdir(folder) if f.lower().endswith(".png"))
    if not files:
        raise ValueError("No PNG files found in folder")

    first_file = files[0]
    first_path = os.path.join(folder, first_file)

    # Extract numeric sequence
    match = re.search(r"(.*?)(\d+)\.png$", first_file)
    if not match:
        raise ValueError("Could not detect numbered pattern in filename")

    prefix, number = match.groups()
    padding = len(number)
    start_number = int(number)

    pattern = f"{prefix}%0{padding}d.png"

    # Get resolution
    with Image.open(first_path) as img:
        width, height = img.size

    print(f"Detected pattern: {pattern}")
    print(f"Start number: {start_number}")
    print(f"Resolution: {width}x{height}")

    filter_complex = (
        f"color=white:size={width}x{height} [bg]; "
        f"[bg][0:v] overlay=shortest=1"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", str(fps),
        "-start_number", str(start_number),
        "-i", os.path.join(folder, pattern),
        "-filter_complex", filter_complex,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "18",
        output
    ]

    subprocess.run(cmd, check=True)
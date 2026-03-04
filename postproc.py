import argparse
import os
import utils

# assuming the helper functions are imported or in the same file
# from helpers import remove_background, compile_video_from_folder


def main(folder, fps, eevee):
    folder = os.path.abspath(folder)

    if not os.path.isdir(folder):
        raise ValueError(f"Folder does not exist: {folder}")

    working_folder = folder

    if not eevee:
        print("Removing background from frames...")
        bg_removed = os.path.join(folder, "bg_removed")

        utils.remove_background(folder, out_folder=bg_removed)

        working_folder = bg_removed

    print("Compiling video...")
    output_path = os.path.join(folder, "output.mp4")

    utils.compile_video_from_folder(
        working_folder,
        output=output_path,
        fps=fps
    )

    print(f"Video saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compile PNG frames into video")
    parser.add_argument("--folder", help="Folder containing PNG frames")
    parser.add_argument("--fps", type=int, default=24, help="Frames per second")
    parser.add_argument(
        "--eevee",
        action="store_true",
        help="If set, skip background removal"
    )

    args = parser.parse_args()

    main(args.folder, args.fps, args.eevee)
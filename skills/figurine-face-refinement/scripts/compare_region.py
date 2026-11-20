"""Build a matched local clay comparison using an external Python with Pillow."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

RENDERER = Path(__file__).with_name("clay_views.py")
# Coordinates are relative to the standard face framing used by clay_views.
PRESETS = {
    "eye": ([0, -35, 35], (.14, .17, .86, .64)),
    "nose": ([0, 35, 70], (.18, .25, .82, .82)),
    "lash": ([0, -35, 35], (.10, .12, .90, .59)),
}


def digest(path):
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def view(folder, angle):
    return folder / f"view_{angle:+03d}.png"


def fingerprints(folder, angles):
    return [digest(view(folder, a)) for a in angles]


def cache_valid(folder, angles):
    try:
        return fingerprints(folder, angles) == json.loads((folder / "hashes.json").read_text())
    except (OSError, ValueError):
        return False


def render(blender, model, frame, folder):
    subprocess.run([blender, "-b", str(model), "--python-exit-code", "1", "-P",
                    str(RENDERER), "--", "--frame", str(frame), "--output", str(folder)], check=True)


def board(before, after, angles, crop, dest):
    columns = []
    sizes = set()
    for angle in angles:
        pair = []
        for folder in (before, after):
            with Image.open(view(folder, angle)) as image:
                sizes.add(image.size)
                w, h = image.size
                box = tuple(round(v * s) for v, s in zip(crop, (w, h, w, h)))
                if box[2] <= box[0] or box[3] <= box[1]:
                    raise ValueError("Crop is smaller than one pixel")
                pair.append(image.crop(box).convert("RGB"))
        columns.append(pair)
    if len(sizes) != 1:
        raise ValueError("Input render sizes do not match")
    w, h = columns[0][0].size
    result = Image.new("RGB", (len(angles) * (w + 6) - 6, 2 * (h + 31)), "#20252a")
    draw = ImageDraw.Draw(result)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 19)
    except OSError:
        font = ImageFont.load_default()
    for col, (angle, pair) in enumerate(zip(angles, columns)):
        for row, image in enumerate(pair):
            x, y = col * (w + 6), row * (h + 31)
            label = ("Baseline", "Current")[row]
            draw.text((x + 6, y + 5), f"{label}   {angle:+d} deg", font=font, fill="white")
            result.paste(image, (x, y + 31))
    result.save(dest, format="PNG")


def compare(args):
    if args.output.suffix.lower() != ".png":
        raise ValueError("Output must be a PNG")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    angles, default_crop = PRESETS[args.region]
    crop = args.crop or default_crop
    if not (all(math.isfinite(v) and 0 <= v <= 1 for v in crop)
            and crop[0] < crop[2] and crop[1] < crop[3]):
        raise ValueError("Crop must be x0 y0 x1 y1 normalized to 0..1")
    config = json.loads(args.frame.read_text(encoding="utf-8-sig"))
    config["angles"] = angles
    settings = json.dumps(config, sort_keys=True)
    with tempfile.TemporaryDirectory(dir=args.output.parent) as tmp:
        tmp = Path(tmp)
        frame = tmp / "frame.json"
        frame.write_text(settings, encoding="utf-8")
        before, after = tmp / "baseline", tmp / "current"
        if not args.no_cache:
            version = subprocess.check_output([args.blender, "--version"]).decode(errors="replace")
            key_fields = [str(args.baseline.resolve()), digest(args.baseline), settings,
                          version, digest(RENDERER)]
            key = hashlib.sha256(json.dumps(key_fields).encode()).hexdigest()
            cache = (args.cache or args.output.parent / ".clay-cache") / key
        if args.no_cache or not cache_valid(cache, angles):
            render(args.blender, args.baseline, frame, before)
            if not args.no_cache:
                cache.mkdir(parents=True, exist_ok=True)
                # Publish the manifest last. Partial results never qualify as hits.
                hashes = fingerprints(before, angles)
                with tempfile.TemporaryDirectory(dir=cache) as subdir:
                    staging = Path(subdir)
                    for angle in angles:
                        staged = view(staging, angle)
                        shutil.copyfile(view(before, angle), staged)
                        os.replace(staged, view(cache, angle))
                    manifest = staging / "hashes.json"
                    manifest.write_text(json.dumps(hashes))
                    os.replace(manifest, cache / manifest.name)
        else:
            before = cache
        render(args.blender, args.current, frame, after)
        output = tmp / "board.png"
        board(before, after, angles, crop, output)
        os.replace(output, args.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", default="blender")
    for name in ("baseline", "current", "frame", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--region", choices=PRESETS, required=True)
    parser.add_argument("--crop", type=float, nargs=4)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--no-cache", action="store_true")
    compare(parser.parse_args())

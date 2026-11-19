"""Render comparable clay views in a disposable Blender background process."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def landmark(settings, name):
    values = settings[name]
    if len(values) != 3 or not all(math.isfinite(v) for v in values):
        raise ValueError(f"{name} must contain three finite world coordinates")
    return Vector(values)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    settings = json.loads(args.frame.read_text(encoding="utf-8-sig"))
    left = landmark(settings, "screen_left_eye")
    right = landmark(settings, "screen_right_eye")
    chin = landmark(settings, "chin")
    span = (right - left).length
    if span == 0:
        raise ValueError("The two eye points coincide")
    side = (right - left).normalized()
    mid = (left + right) * 0.5
    up = mid - chin
    up -= side * up.dot(side)
    if up.length < span * 0.01:
        raise ValueError("The chin needs to be below the eye line")
    up.normalize()
    front = side.cross(up).normalized()
    width = float(settings.get("width_in_eye_spans", 3.15)) * span
    angles = settings.get("angles", [0, -35, 35, -70, 70])
    if not math.isfinite(width) or width <= 0 or not angles:
        raise ValueError("Provide a positive frame width and at least one angle")
    if not all(type(a) is int and -90 <= a <= 90 for a in angles) or len(set(angles)) != len(angles):
        raise ValueError("Angles must be unique integer degrees in [-90, 90]")
    target = mid.lerp(chin, 0.24)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    shade = scene.display.shading
    shade.light = "STUDIO"
    shade.studio_light = "paint.sl"
    shade.color_type = "SINGLE"
    shade.single_color = (0.62, 0.62, 0.62)
    shade.show_shadows = False
    shade.show_cavity = False
    shade.show_specular_highlight = True
    shade.background_type = "VIEWPORT"
    shade.background_color = (0.06, 0.06, 0.06)
    scene.render.film_transparent = False
    scene.render.use_border = False
    scene.render.use_sequencer = False
    scene.render.use_compositing = False
    scene.render.use_multiview = False
    scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
    scene.render.resolution_x = 920
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "BW"
    camera_data = bpy.data.cameras.new("Review camera")
    camera = bpy.data.objects.new("Review camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = width
    camera_data.clip_start = width / 1000
    camera_data.clip_end = width * 20
    args.output.mkdir(parents=True, exist_ok=True)
    for angle in angles:
        radians = math.radians(angle)
        axis = side * math.cos(radians) - front * math.sin(radians)
        view = side * math.sin(radians) + front * math.cos(radians)
        camera.location = target + view * width * 4
        camera.rotation_euler = Matrix((axis, up, view)).transposed().to_euler()
        scene.render.filepath = str((args.output / f"view_{angle:+03d}.png").resolve())
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
